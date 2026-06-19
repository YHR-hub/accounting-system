from __future__ import annotations
"""现金流量表(直接法)标签页。"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class CashflowTabMixin:
    def _build_cashflow_tab(self):
        f = self.tabs['cashflow']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='💵 现金流量表 (直接法)', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='年份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15,2))
        self.cf_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2024, to=2035, textvariable=self.cf_year,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT)
        tk.Label(top, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(5,2))
        self.cf_month = tk.StringVar(value='12')
        tk.Spinbox(top, from_=1, to=12, textvariable=self.cf_month,
                   font=FONT_TEXT, width=5).pack(side=tk.LEFT)
        tk.Label(top, text='(0=全年)', font=FONT_SMALL, bg=self._c('bg'), fg='gray').pack(side=tk.LEFT)
        tk.Button(top, text='🔄 计算', font=FONT_TEXT, command=self._refresh_cashflow,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        self.cf_text = tk.Text(f, font=('Consolas', 12), relief=tk.SUNKEN,
                                bg=self._c('bg'), state=tk.DISABLED)
        self.cf_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_cashflow()

    def _refresh_cashflow(self):
        try:
            year = int(self.cf_year.get())
            month = int(self.cf_month.get())
        except ValueError:
            return
        data = acc.cash_flow_statement_direct(year, month)
        self.cf_text.config(state=tk.NORMAL)
        self.cf_text.delete('1.0', tk.END)
        self.cf_text.insert(tk.END, f'💵 现金流量表 (直接法)\n')
        self.cf_text.insert(tk.END, f'  期间: {year}年{data["month"]}月\n')
        self.cf_text.insert(tk.END, f'{"─"*45}\n\n')
        lines = [
            ('一、经营活动产生的现金流量', True),
            ('  销售商品、提供劳务收到的现金', data['cash_from_customers']),
            ('  购买商品、接受劳务支付的现金', data['cash_to_suppliers']),
            ('  支付给职工以及为职工支付的现金', data['cash_for_salaries']),
            ('  支付的各项税费', data['cash_for_taxes']),
            ('', None),
            ('  经营活动现金净额', data['net_cash_operating']),
            ('', None),
            ('二、投资活动产生的现金流量', True),
            ('  (数据来自间接法)', None),
            ('', None),
            ('三、筹资活动产生的现金流量', True),
            ('  (数据来自间接法)', None),
        ]
        for label, val in lines:
            if val is True:
                self.cf_text.insert(tk.END, f'{label}\n', 'bold')
            elif val is None:
                self.cf_text.insert(tk.END, f'{label}\n')
            else:
                sign = '' if val < 0 else ' '
                self.cf_text.insert(tk.END, f'{label:<35s} {sign}{val:>12,.2f}\n')
        self.cf_text.tag_configure('bold', font=('Consolas', 12, 'bold'))
        self.cf_text.insert(tk.END, f'\n{"─"*45}\n')
        self.cf_text.insert(tk.END, f'{"经营活动现金净额":<35s} {data["net_cash_operating"]:>12,.2f}\n')
        self.cf_text.config(state=tk.DISABLED)
