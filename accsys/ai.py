from __future__ import annotations

"""云端AI助手模块。"""

import json
import os
from datetime import date
from typing import Optional

import requests

from .database import get_conn
from .constants import AI_CONFIG_FILE, DEFAULT_AI_CONFIG, RAG_SYSTEM_PROMPT


def load_ai_config() -> dict:
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_AI_CONFIG, **json.load(f)}
        except Exception:
            pass
    return dict(DEFAULT_AI_CONFIG)


def save_ai_config(cfg: dict) -> bool:
    try:
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERR] save_ai_config: {e}")
        return False


def _build_financial_context() -> str:
    conn = get_conn()
    try:
        v_count = conn.execute("SELECT COUNT(*) FROM vouchers").fetchone()[0]
        je_count = conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
        acct_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        last_v = conn.execute(
            "SELECT fiscal_year, fiscal_month FROM vouchers ORDER BY id DESC LIMIT 1").fetchone()
        period = f"{last_v['fiscal_year']}年{last_v['fiscal_month']:02d}月" if last_v else "无"
        year = date.today().year
        rev = conn.execute(
            "SELECT COALESCE(SUM(je.credit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND a.category='income'", (year,)).fetchone()[0] or 0
        exp = conn.execute(
            "SELECT COALESCE(SUM(je.debit),0) FROM vouchers v "
            "JOIN journal_entries je ON v.id=je.voucher_id "
            "JOIN accounts a ON je.account_code=a.code "
            "WHERE v.fiscal_year=? AND a.category='expense'", (year,)).fetchone()[0] or 0
        asset = conn.execute(
            "SELECT COALESCE(SUM(balance),0) FROM accounts "
            "WHERE category='asset'").fetchone()[0] or 0
        liability = conn.execute(
            "SELECT COALESCE(SUM(balance),0) FROM accounts "
            "WHERE category='liability'").fetchone()[0] or 0
        conn.close()
        lines = [
            f"当前会计系统状态 ({date.today().isoformat()}):",
            f"- 凭证总数: {v_count} 张, 分录总数: {je_count} 条, 科目数: {acct_count} 个",
            f"- 最新凭证期间: {period}",
            f"- {year}年收入: {float(rev):,.2f}, 支出: {float(exp):,.2f}",
            f"- 资产总额: {float(asset):,.2f}, 负债总额: {float(liability):,.2f}",
            "- 功能: 凭证管理/报表/固定资产/税务/多币种/期末处理/可视化/区块链/ESG",
            "- 你是一个财务AI助手，用中文回答用户关于财务数据的问题",
            "- 根据以上数据上下文，给出专业、简洁的回答",
        ]
        return "\n".join(lines)
    except Exception:
        conn.close()
        return "会计系统助手，用中文回答财务相关问题。"


def call_ai(messages: list, stream: bool = False) -> str:
    cfg = load_ai_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return "请先在 设置-AI配置 中启用并填写API密钥"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    has_system = any(m.get("role") == "system" for m in messages)
    if not has_system:
        system_msg = {"role": "system", "content": _build_financial_context()}
        messages = [system_msg] + messages
    payload = {
        "model": cfg.get("model", "gpt-3.5-turbo"),
        "messages": messages,
        "max_tokens": cfg.get("max_tokens", 2048),
        "temperature": cfg.get("temperature", 0.7),
        "stream": stream,
    }
    try:
        resp = requests.post(cfg['endpoint'], headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"API调用失败: {e}"


def ask_ai(question: str, context: Optional[str] = None) -> str:
    user_msg = question
    if context:
        user_msg = f"【上下文】{context}\n\n【问题】{question}"
    messages = [
        {"role": "user", "content": user_msg},
    ]
    return call_ai(messages)


def ai_query_database(question: str) -> str:
    cfg = load_ai_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return "请先配置AI"
    has_system = False
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": question})
    payload = {
        "model": cfg.get("model", "gpt-3.5-turbo"),
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.1,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {cfg['api_key']}"}
    try:
        resp = requests.post(cfg['endpoint'], headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        sql = resp.json()["choices"][0]["message"]["content"].strip()
        if "--NEED_CLARIFY--" in sql:
            return "问题不够明确，请补充更多细节"
        sql = sql.replace("```sql", "").replace("```", "").strip()
        conn = get_conn()
        try:
            rows = conn.execute(sql).fetchall()
            if not rows:
                return "查询完成，没有找到相关数据"
            cols = [d[0] for d in conn.execute(sql).description]
            lines = [" | ".join(cols), "-" * (len(cols) * 20)]
            for r in rows[:20]:
                lines.append(" | ".join(str(v) if v is not None else "" for v in r))
            if len(rows) > 20:
                lines.append(f"... 共 {len(rows)} 条，仅显示前20条")
            conn.close()
            return "\n".join(lines)
        except Exception as sqlerr:
            conn.close()
            return f"SQL执行错误: {sqlerr}\n生成的SQL: {sql}"
    except Exception as e:
        return f"AI调用失败: {e}"
