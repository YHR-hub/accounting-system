from __future__ import annotations
"""财务报表标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
import io, sys
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class ReportsTabMixin:
    def _build_reports_tab(self):
        f = self.tabs['reports']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=8)
        for text, cmd in [('资产负债表', self._show_balance_sheet),
                          ('利润表', self._show_income),
                          ('现金流量表', self._show_cashflow)]:
            tk.Button(top, text=text, font=FONT_TEXT, command=cmd,
                      bg=self._c('primary'), fg='white', width=14).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📤 导出Excel', font=FONT_TEXT, command=self._export_excel_gui,
                  bg='#FFD54F', width=14).pack(side=tk.LEFT, padx=5)

        self.r_text = tk.Text(f, font=('Consolas', 11), bg='white', relief=tk.SUNKEN,
                              wrap=tk.NONE, state=tk.DISABLED)
        self.r_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        hsb = ttk.Scrollbar(f, orient=tk.HORIZONTAL, command=self.r_text.xview)
        self.r_text.configure(xscrollcommand=hsb.set)
        hsb.pack(fill=tk.X, padx=10)
        vsb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.r_text.yview)
        self.r_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _show_balance_sheet(self):
        self.r_text.config(state=tk.NORMAL)
        self.r_text.delete('1.0', tk.END)
        old = sys.stdout
        sys.stdout = buf = io.StringIO()
        acc.balance_sheet()
        sys.stdout = old
        self.r_text.insert(tk.END, buf.getvalue())
        self.r_text.config(state=tk.DISABLED)

    def _show_income(self):
        self.r_text.config(state=tk.NORMAL)
        self.r_text.delete('1.0', tk.END)
        old = sys.stdout
        sys.stdout = buf = io.StringIO()
        acc.income_statement()
        sys.stdout = old
        self.r_text.insert(tk.END, buf.getvalue())
        self.r_text.config(state=tk.DISABLED)

    def _show_cashflow(self):
        self.r_text.config(state=tk.NORMAL)
        self.r_text.delete('1.0', tk.END)
        old = sys.stdout
        sys.stdout = buf = io.StringIO()
        acc.cash_flow_statement()
        sys.stdout = old
        self.r_text.insert(tk.END, buf.getvalue())
        self.r_text.config(state=tk.DISABLED)

    def _export_excel_gui(self):
        try:
            acc.export_excel()
            messagebox.showinfo('成功', f'报表已导出到:\n{acc.get_excel_path()}')
        except Exception as e:
            messagebox.showerror('错误', f'导出失败: {e}')
