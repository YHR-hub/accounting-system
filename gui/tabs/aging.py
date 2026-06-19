from __future__ import annotations
"""应收应付账龄分析标签页。"""
import tkinter as tk
from tkinter import ttk
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class AgingTabMixin:
    def _build_aging_tab(self):
        f = self.tabs['aging']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📋 应收应付账龄分析', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        self.aging_type = tk.StringVar(value='ar')
        tk.Radiobutton(top, text='应收账款', variable=self.aging_type, value='ar',
                       font=FONT_TEXT, bg=self._c('bg'), command=self._refresh_aging).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(top, text='应付账款', variable=self.aging_type, value='ap',
                       font=FONT_TEXT, bg=self._c('bg'), command=self._refresh_aging).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_aging,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        self.aging_summary = tk.Label(f, text='', font=FONT_TEXT, bg=self._c('bg'), fg=self._c('accent'))
        self.aging_summary.pack(anchor='w', padx=15, pady=2)

        cols = ('account', 'balance', 'last_date', 'days', 'bucket', 'rate', 'provision')
        self.aging_tree = ttk.Treeview(f, columns=cols, show='headings', height=16)
        self.aging_tree.heading('account', text='科目')
        self.aging_tree.heading('balance', text='余额')
        self.aging_tree.heading('last_date', text='最后交易')
        self.aging_tree.heading('days', text='天数')
        self.aging_tree.heading('bucket', text='账龄区间')
        self.aging_tree.heading('rate', text='计提比例')
        self.aging_tree.heading('provision', text='坏账准备')
        self.aging_tree.column('account', width=140)
        self.aging_tree.column('balance', width=120, anchor='e')
        self.aging_tree.column('last_date', width=100, anchor='center')
        self.aging_tree.column('days', width=60, anchor='center')
        self.aging_tree.column('bucket', width=100, anchor='center')
        self.aging_tree.column('rate', width=80, anchor='center')
        self.aging_tree.column('provision', width=120, anchor='e')
        self.aging_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_aging()

    def _refresh_aging(self):
        for item in self.aging_tree.get_children():
            self.aging_tree.delete(item)
        at = self.aging_type.get()
        items = acc.aging_analysis(at)
        total_balance = 0
        total_provision = 0
        for it in items:
            self.aging_tree.insert('', tk.END, values=(
                f"{it['account_code']} {it['account_name']}",
                f"{it['balance']:,.2f}", it['last_date'], it['days'],
                it['bucket'], f"{it['provision_rate']*100:.1f}%",
                f"{it['bad_debt_provision']:,.2f}",
            ))
            total_balance += it['balance']
            total_provision += it['bad_debt_provision']
        label = '应收' if at == 'ar' else '应付'
        self.aging_summary.config(
            text=f"📊 {label}余额合计: {total_balance:,.2f}  |  坏账准备: {total_provision:,.2f}  |  账户数: {len(items)}")
