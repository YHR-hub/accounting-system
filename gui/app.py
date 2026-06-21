from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date
from typing import Optional

import accsys as acc

from gui.constants import (
    FONT_TITLE, FONT_SUB, FONT_TEXT, FONT_SMALL, FONT_CUTE,
    COLOR_BG, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARN,
    COLOR_ALT, COLOR_ACCENT, COLOR_VIOLET, COLOR_PURPLE,
    MOOD_COLORS, SHOW_EXPERIMENTAL, EXPERIMENTAL_TABS,
)

from gui.tabs.voucher import VoucherTabMixin
from gui.tabs.query import QueryTabMixin
from gui.tabs.accounts import AccountsTabMixin
from gui.tabs.reports import ReportsTabMixin
from gui.tabs.assets import AssetsTabMixin
from gui.tabs.tax import TaxTabMixin
from gui.tabs.currency import CurrencyTabMixin
from gui.tabs.period import PeriodTabMixin
from gui.tabs.viz import VizTabMixin
from gui.tabs.intel import IntelTabMixin
from gui.tabs.blockchain import BlockchainTabMixin
from gui.tabs.esg import ESGTabMixin
from gui.tabs.startup import StartupTabMixin
from gui.tabs.ai import AITabMixin
from gui.tabs.aging import AgingTabMixin
from gui.tabs.budget import BudgetTabMixin
from gui.tabs.inventory import InventoryTabMixin
from gui.tabs.audit import AuditTabMixin
from gui.tabs.alerts import AlertsTabMixin
from gui.tabs.recon import ReconTabMixin
from gui.tabs.payroll import PayrollTabMixin
from gui.tabs.projects import ProjectsTabMixin
from gui.tabs.cashflow import CashflowTabMixin
from gui.tabs.attachments import AttachmentsTabMixin
from gui.tabs.overview import OverviewTabMixin


class AccountingApp(
    OverviewTabMixin,
    VoucherTabMixin,
    QueryTabMixin,
    AccountsTabMixin,
    ReportsTabMixin,
    AssetsTabMixin,
    TaxTabMixin,
    CurrencyTabMixin,
    PeriodTabMixin,
    VizTabMixin,
    IntelTabMixin,
    BlockchainTabMixin,
    ESGTabMixin,
    StartupTabMixin,
    AITabMixin,
    AgingTabMixin,
    BudgetTabMixin,
    InventoryTabMixin,
    AuditTabMixin,
    AlertsTabMixin,
    ReconTabMixin,
    PayrollTabMixin,
    ProjectsTabMixin,
    CashflowTabMixin,
    AttachmentsTabMixin,
):
    def __init__(self, root: tk.Tk):
        self.root = root
        root.withdraw()
        acc.init_db()
        acc.ensure_accounts()
        acc.init_users()
        acc.load_theme()
        self._apply_theme()
        self._apply_widget_defaults()

        if not self._show_login():
            root.destroy()
            return

        root.deiconify()
        self.root.title('✨ 会计系统专业版 ✨')
        self._center(self.root, 1160, 800)
        self.root.minsize(960, 600)
        self.root.configure(bg=self._c('bg'))

        self._build_ui()
        self._bind_events()

    def _c(self, key: str) -> str:
        """Get current theme color."""
        return acc.get_theme().get(key, '#F4F5F7')

    def _apply_theme(self):
        """Apply theme colors to module-level constants."""
        t = acc.get_theme()
        global COLOR_BG, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARN, COLOR_ALT, COLOR_ACCENT, COLOR_VIOLET, COLOR_PURPLE
        COLOR_BG = t['bg']
        COLOR_PRIMARY = t['primary']
        COLOR_SUCCESS = t['success']
        COLOR_WARN = t['warn']
        COLOR_ALT = t['alt']
        COLOR_ACCENT = t['accent']
        COLOR_VIOLET = t['violet']
        COLOR_PURPLE = t['purple']

    def _apply_widget_defaults(self):
        """通过 Tk 选项数据库统一所有按钮的默认风格（扁平/无边框/手型/内边距）。

        仅设置默认值，各按钮已显式指定的颜色不受影响。
        """
        o = self.root.option_add
        o('*Button.relief', 'flat')
        o('*Button.borderWidth', 0)
        o('*Button.highlightThickness', 0)
        o('*Button.cursor', 'hand2')
        o('*Button.padX', 12)
        o('*Button.padY', 5)

    def _center(self, win, w: int, h: int):
        """把窗口按屏幕大小收缩并居中（适配小屏笔记本，避免超出被切掉）。"""
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        w = min(w, sw - 80)
        h = min(h, sh - 100)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 20)
        win.geometry(f'{w}x{h}+{x}+{y}')
        return w, h

    def _show_login(self) -> bool:
        acc.CURRENT_USER = {}
        bg = '#F4F5F7'
        win = tk.Toplevel(self.root)
        win.title('登录 - 会计系统专业版')
        self._center(win, 440, 470)
        win.resizable(False, False)
        win.configure(bg=bg)

        def on_close():
            acc.CURRENT_USER = {}
            win.destroy()

        win.protocol('WM_DELETE_WINDOW', on_close)

        card = tk.Frame(win, bg='white', padx=34, pady=26,
                        highlightbackground='#E3E5F0', highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor='center', width=372, height=410)

        tk.Label(card, text='💠', font=('微软雅黑', 28), bg='white', fg='#6C5CE7').pack(pady=(2, 0))
        tk.Label(card, text='会计系统专业版', font=('微软雅黑', 17, 'bold'),
                 bg='white', fg='#2D3436').pack(pady=(2, 1))
        tk.Label(card, text='Professional Accounting System', font=('微软雅黑', 9),
                 bg='white', fg='#A6A8B8').pack(pady=(0, 18))

        tk.Label(card, text='用户名', font=('微软雅黑', 10), bg='white', fg='#636E72').pack(anchor='w')
        user_var = tk.StringVar(value='admin')
        e1 = tk.Entry(card, textvariable=user_var, font=('Consolas', 12),
                      relief='flat', bg='#F1F2F6')
        e1.pack(fill=tk.X, ipady=6, pady=(3, 12))

        tk.Label(card, text='密码', font=('微软雅黑', 10), bg='white', fg='#636E72').pack(anchor='w')
        pass_var = tk.StringVar(value='admin123')
        e2 = tk.Entry(card, textvariable=pass_var, font=('Consolas', 12), show='●',
                      relief='flat', bg='#F1F2F6')
        e2.pack(fill=tk.X, ipady=6, pady=(3, 4))

        result_var = tk.StringVar()
        tk.Label(card, textvariable=result_var, font=('微软雅黑', 9), bg='white',
                 fg='#E74C3C').pack(pady=(2, 4))

        def do_login():
            r = acc.login(user_var.get(), pass_var.get())
            if r['success']:
                win.destroy()
            else:
                result_var.set('用户名或密码错误')

        btn = tk.Button(card, text='登 录', font=('微软雅黑', 13, 'bold'),
                        command=do_login, bg='#6C5CE7', fg='white', bd=0, cursor='hand2',
                        activebackground='#5A4BD1', activeforeground='white')
        btn.pack(fill=tk.X, ipady=8, pady=(6, 12))

        tk.Label(card, text='演示账号  admin / admin123', font=('微软雅黑', 9),
                 bg='white', fg='#B4B6C2').pack()

        win.bind('<Return>', lambda e: do_login())
        e1.focus_set()
        win.grab_set()
        self.root.wait_window(win)
        return acc.CURRENT_USER.get('username') != ''

    def _build_ui(self):
        top = tk.Frame(self.root, bg=self._c('primary'), height=56)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        tk.Label(top, text='💠 会计系统专业版 v2.0', font=FONT_TITLE,
                 bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=20, pady=8)

        user = acc.CURRENT_USER
        role_label = {'admin': '管理员', 'accountant': '会计员', 'viewer': '查询员'}
        tk.Label(top, text=f'👤 {user.get("display_name","")} ({role_label.get(user.get("role",""),"")})',
                 font=FONT_TEXT, bg=self._c('primary'), fg='#E8E6FF').pack(side=tk.RIGHT, padx=5)
        tk.Button(top, text='🌙 深色', font=FONT_TEXT, command=self._toggle_theme,
                  bg=self._c('accent'), fg='white', bd=0, padx=10, cursor='hand2',
                  activebackground=self._c('violet'), activeforeground='white').pack(side=tk.RIGHT, padx=2)
        tk.Button(top, text='⚙ 设置', font=FONT_TEXT, command=self._show_settings,
                  bg=self._c('accent'), fg='white', bd=0, padx=15, cursor='hand2',
                  activebackground=self._c('violet'), activeforeground='white').pack(side=tk.RIGHT, padx=10)

        tk.Frame(self.root, bg=self._c('tab_act'), height=2).pack(fill=tk.X)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self._c('bg'), borderwidth=0)
        style.configure('TNotebook.Tab', font=FONT_TEXT, padding=[16, 8],
                        background=self._c('tab_bg'), foreground=self._c('tab_fg'), borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', self._c('tab_sel')), ('active', self._c('tab_act'))],
                  foreground=[('selected', self._c('tab_sel_fg')), ('active', self._c('tab_fg'))])

        # 全局表格(Treeview)现代化：白底、行更高、表头加粗扁平、选中靛紫高亮
        style.configure('Treeview', background=self._c('text_bg'), fieldbackground=self._c('text_bg'),
                        foreground=self._c('fg'), rowheight=28, font=FONT_SMALL, borderwidth=0)
        style.configure('Treeview.Heading', font=FONT_CUTE, background=self._c('tab_bg'),
                        foreground=self._c('fg'), relief='flat', padding=6)
        style.map('Treeview', background=[('selected', self._c('primary'))],
                  foreground=[('selected', 'white')])
        style.map('Treeview.Heading', background=[('active', self._c('tab_act'))])
        # 滚动条 / 输入框 / 下拉框 配合主题
        style.configure('Vertical.TScrollbar', background=self._c('tab_bg'), borderwidth=0, troughcolor=self._c('bg'))
        style.configure('Horizontal.TScrollbar', background=self._c('tab_bg'), borderwidth=0, troughcolor=self._c('bg'))
        style.configure('TCombobox', fieldbackground=self._c('text_bg'), background=self._c('tab_bg'))

        # 底部状态栏
        status = tk.Frame(self.root, bg=self._c('tab_bg'), height=26)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        su = acc.CURRENT_USER
        tk.Label(status, text=f'👤 {su.get("display_name","")}（{role_label.get(su.get("role",""),"")}）',
                 bg=self._c('tab_bg'), fg=self._c('tab_fg'), font=FONT_SMALL).pack(side=tk.LEFT, padx=12)
        tk.Label(status, text=f'📅 {date.today().isoformat()}',
                 bg=self._c('tab_bg'), fg=self._c('tab_fg'), font=FONT_SMALL).pack(side=tk.LEFT, padx=4)
        tk.Label(status, text='● 就绪', bg=self._c('tab_bg'), fg=self._c('success'),
                 font=FONT_SMALL).pack(side=tk.RIGHT, padx=12)

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tabs = {}
        tab_names = [
            ('overview', '  🏠 概览  '),
            ('voucher', '  ✏️ 凭证录入  '),
            ('query', '  🔍 凭证查询  '),
            ('accounts', '  💰 科目余额  '),
            ('reports', '  📊 财务报表  '),
            ('period', '  📅 期末处理  '),
            ('assets', '  🏠 固定资产  '),
            ('aging', '  📋 应收应付  '),
            ('budget', '  📊 预算管理  '),
            ('inventory', '  📦 库存管理  '),
            ('viz', '  📈 可视化  '),
            ('intel', '  🧠 智能分析  '),
            ('blockchain', '  ⛓️ 区块链  '),
            ('esg', '  🌿 ESG  '),
            ('startup', '  🚀 创业工具  '),
            ('ai', '  🤖 AI助手  '),
            ('tax', '  🧾 税务  '),
            ('currency', '  💱 多币种  '),
            ('audit', '  📋 审计日志  '),
            ('alerts', '  🔔 财务预警  '),
            ('recon', '  🏦 银企对账  '),
            ('payroll', '  💰 薪资管理  '),
            ('projects', '  🏗️ 项目会计  '),
            ('cashflow', '  💵 现金流量  '),
            ('attachments', '  📎 附件管理  '),
        ]
        if not SHOW_EXPERIMENTAL:
            tab_names = [t for t in tab_names if t[0] not in EXPERIMENTAL_TABS]
        for key, label in tab_names:
            frame = tk.Frame(nb, bg=COLOR_BG)
            nb.add(frame, text=label)
            self.tabs[key] = frame

        self.notebook = nb
        self._build_overview_tab()
        self._build_voucher_tab()
        self._build_query_tab()
        self._build_accounts_tab()
        self._build_reports_tab()
        self._build_period_tab()
        self._build_assets_tab()
        self._build_viz_tab()
        self._build_intel_tab()
        if 'blockchain' in self.tabs:
            self._build_blockchain_tab()
        if 'esg' in self.tabs:
            self._build_esg_tab()
        self._build_startup_tab()
        self._build_aging_tab()
        self._build_budget_tab()
        self._build_inventory_tab()
        if 'ai' in self.tabs:
            self._build_ai_tab()
        self._build_tax_tab()
        self._build_currency_tab()
        self._build_audit_tab()
        self._build_alerts_tab()
        self._build_recon_tab()
        self._build_payroll_tab()
        self._build_projects_tab()
        self._build_cashflow_tab()
        self._build_attachments_tab()

    def _bind_events(self):
        self.root.bind('<Control-s>', lambda e: self._save_voucher())

    def _toggle_theme(self):
        mode = 'dark' if acc.get_theme_mode() == 'light' else 'light'
        acc.set_theme_mode(mode)
        self._apply_theme()
        self.root.configure(bg=self._c('bg'))
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._bind_events()

    def _show_settings(self):
        win = tk.Toplevel(self.root)
        win.title('系统设置')
        win.geometry('450x380')
        win.resizable(False, False)
        win.configure(bg=COLOR_BG)

        frame = tk.Frame(win, bg=COLOR_BG, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='⚙ 系统设置', font=FONT_SUB, bg=COLOR_BG).pack(pady=(0, 15))

        theme_frame = tk.Frame(frame, bg=COLOR_BG)
        theme_frame.pack(fill=tk.X, pady=5)
        mode = acc.get_theme_mode()
        tk.Label(theme_frame, text=f'当前主题: {"🌙 深色" if mode=="dark" else "🌸 浅色"}',
                 font=FONT_TEXT, bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        tk.Button(theme_frame, text='切换主题', font=FONT_TEXT,
                  command=lambda: [win.destroy(), self._toggle_theme()],
                  bg=COLOR_ACCENT, fg='white').pack(side=tk.LEFT, padx=10)

        user = acc.CURRENT_USER
        role_label = {'admin': '管理员', 'accountant': '会计员', 'viewer': '查询员'}
        tk.Label(frame, text=f'当前用户: {user.get("display_name","")} ({role_label.get(user.get("role",""),"")})',
                 font=FONT_TEXT, bg=COLOR_BG, fg=COLOR_VIOLET).pack(anchor='w', pady=5)

        btn_data = [
            ('🤖 AI 模型配置', self._show_ai_config, '#C084FC'),
            ('📊 数据库维护', self._db_maintenance, '#FFB347'),
            ('👤 用户管理', self._show_user_mgmt, '#7BC67E'),
            ('📋 关于系统', self._show_about, '#9C27B0'),
        ]
        for txt, cmd, bgc in btn_data:
            tk.Button(frame, text=txt, font=FONT_TEXT, command=lambda c=cmd: [win.destroy(), c()],
                      bg=bgc, fg='white', width=30, pady=5).pack(pady=5)

    def _db_maintenance(self):
        """Database maintenance dialog."""
        if messagebox.askyesno('确认', '执行数据库VACUUM优化？\n(可能耗时较久)'):
            conn = acc.get_conn()
            conn.execute('VACUUM')
            conn.close()
            messagebox.showinfo('完成', '数据库优化完成')

    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title('关于')
        win.geometry('440x380')
        win.resizable(False, False)
        win.configure(bg=COLOR_BG)

        card = tk.Frame(win, bg='white', padx=28, pady=22,
                        highlightbackground='#E3E5F0', highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(card, text='💠', font=('微软雅黑', 30), bg='white', fg=self._c('primary')).pack()
        tk.Label(card, text='会计系统专业版 v2.0', font=('微软雅黑', 16, 'bold'),
                 bg='white', fg='#2D3436').pack(pady=(2, 1))
        tk.Label(card, text='Professional Accounting System', font=('微软雅黑', 9),
                 bg='white', fg='#A6A8B8').pack(pady=(0, 14))

        info = ('凭证管理 · 财务报表 · 固定资产 · 税务 · 多币种\n'
                '期末处理 · 数据可视化 · 智能分析 · 区块链账本\n'
                'ESG 报告 · 库存 / 薪资 / 项目 · AI 智能助手')
        tk.Label(card, text=info, font=('微软雅黑', 10), bg='white', fg='#636E72',
                 justify='center').pack(pady=(0, 12))
        tk.Label(card, text='Python · Tkinter · SQLite · FastAPI · React',
                 font=('微软雅黑', 9), bg='white', fg='#9AA0B5').pack()

        tk.Button(card, text='关 闭', font=('微软雅黑', 11, 'bold'), command=win.destroy,
                  bg=self._c('primary'), fg='white').pack(pady=(18, 0), ipadx=24, ipady=4)
        win.grab_set()

    def _show_user_mgmt(self):
        win = tk.Toplevel(self.root)
        win.title('用户管理')
        win.geometry('500x400')
        win.resizable(False, False)
        win.configure(bg=COLOR_BG)

        frame = tk.Frame(win, bg=COLOR_BG, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='👤 用户管理', font=FONT_SUB, bg=COLOR_BG).pack(pady=(0, 10))

        cols = ('username', 'display', 'role', 'active')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=8)
        tree.heading('username', text='用户名')
        tree.heading('display', text='显示名')
        tree.heading('role', text='角色')
        tree.heading('active', text='状态')
        tree.column('username', width=100)
        tree.column('display', width=100)
        tree.column('role', width=80, anchor='center')
        tree.column('active', width=60, anchor='center')
        tree.pack(fill=tk.BOTH, expand=True)

        conn = acc.get_conn()
        rows = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
        role_map = {'admin': '管理员', 'accountant': '会计员', 'viewer': '查询员'}
        for r in rows:
            tree.insert('', tk.END, values=(r['username'], r['display_name'],
                                            role_map.get(r['role'], r['role']),
                                            '✅ 启用' if r['is_active'] else '❌ 停用'))

        tk.Label(frame, text='默认账号: admin/admin123, accountant/acc123, viewer/view123',
                 font=FONT_SMALL, bg=COLOR_BG, fg='gray').pack(pady=5)
        tk.Button(frame, text='关闭', font=FONT_TEXT, command=win.destroy,
                  bg=COLOR_BG).pack()


def main():
    import os
    import sys
    root = tk.Tk()
    root.title('会计系统专业版')
    try:
        base = getattr(sys, '_MEIPASS', None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico = os.path.join(base, 'accounting_icon.ico')
        if os.path.exists(ico):
            root.iconbitmap(ico)
    except Exception:
        pass
    app = AccountingApp(root)
    root.mainloop()
