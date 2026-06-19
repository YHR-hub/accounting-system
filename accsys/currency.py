"""多币种汇率模块"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from datetime import date
from typing import Dict
from .database import get_conn


def fetch_exchange_rates(base: str = "CNY") -> Dict[str, float]:
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        rates = data.get("rates", {})
        return {k: v for k, v in rates.items() if k in ("USD", "EUR", "GBP", "JPY", "HKD", "KRW", "CNY")}
    except Exception:
        return {}


def show_exchange_rates():
    print("\n── 汇率查询 ──")
    print("正在获取最新汇率...")
    rates = fetch_exchange_rates()
    if rates:
        base_currency = "CNY"
        print(f"\n基币: {base_currency}  (1 {base_currency} = ?)")
        print(f"{'币种':<8} {'汇率':>12}")
        print("-" * 22)
        for currency in ("USD", "EUR", "GBP", "JPY", "HKD", "KRW"):
            if currency in rates:
                print(f"{currency:<8} {rates[currency]:>12.6f}")
        print("\n提示: 汇率会自动缓存到数据库")
        today = date.today().isoformat()
        conn = get_conn()
        for cur, rate in rates.items():
            conn.execute("INSERT OR REPLACE INTO exchange_rates (currency, date, rate) VALUES (?, ?, ?)",
                         (cur, today, rate))
        conn.commit()
        conn.close()
    else:
        print("无法获取在线汇率，请手动输入")
        manual_exchange_rate()


def manual_exchange_rate():
    cur = input("币种代码 (如 USD): ").upper().strip()
    if not cur:
        return
    rate_str = input(f"1 CNY = ? {cur}: ").strip()
    try:
        rate = float(rate_str)
        if rate <= 0:
            print("汇率必须大于0")
            return
    except ValueError:
        print("无效数字")
        return
    today = date.today().isoformat()
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO exchange_rates (currency, date, rate) VALUES (?, ?, ?)",
                 (cur, today, rate))
    conn.commit()
    conn.close()
    print(f"[OK] 汇率已保存: 1 CNY = {rate:.4f} {cur}")
