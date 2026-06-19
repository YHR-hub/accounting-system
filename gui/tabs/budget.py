from __future__ import annotations
"""预算管理标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class BudgetTabMixin:
    def _build_budget_tab(self):
        f = self.tabs['budget']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📊 预算管理', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Label(top, text='年份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10,2))
        self.bg_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2024, to=2035, textvariable=self.bg_year,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10,2))
        self.bg_month = tk.StringVar(value='0')
        tk.Spinbox(top, from_=0, to=12, textvariable=self.bg_month,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text='(0=全年)', font=FONT_SMALL, bg=self._c('bg'), fg='gray').pack(side=tk.LEFT)

        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_budget,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='✏️ 设置预算', font=FONT_TEXT, command=self._set_budget_dialog,
                  bg=self._c('accent'), fg='white').pack(side=tk.LEFT, padx=5)

        cols = ('code', 'name', 'category', 'budget', 'actual', 'variance', 'pct')
        self.bg_tree = ttk.Treeview(f, columns=cols, show='headings', height=18)
        self.bg_tree.heading('code', text='科目编码')
        self.bg_tree.heading('name', text='科目名称')
        self.bg_tree.heading('category', text='类别')
        self.bg_tree.heading('budget', text='预算金额')
        self.bg_tree.heading('actual', text='实际金额')
        self.bg_tree.heading('variance', text='差异')
        self.bg_tree.heading('pct', text='执行率%')
        self.bg_tree.column('code', width=90)
        self.bg_tree.column('name', width=140)
        self.bg_tree.column('category', width=60, anchor='center')
        self.bg_tree.column('budget', width=120, anchor='e')
        self.bg_tree.column('actual', width=120, anchor='e')
        self.bg_tree.column('variance', width=120, anchor='e')
        self.bg_tree.column('pct', width=80, anchor='center')
        self.bg_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.bg_tree.tag_configure('over', foreground='#FF4757')
        self.bg_tree.tag_configure('under', foreground='#7BC67E')
        self._refresh_budget()

    def _refresh_budget(self):
        for item in self.bg_tree.get_children():
            self.bg_tree.delete(item)
        try:
            year = int(self.bg_year.get())
            month = int(self.bg_month.get())
        except ValueError:
            return
        items = acc.get_budget_status(year, month)
        for it in items:
            tag = ''
            if it['pct'] > 100:
                tag = 'over'
            elif it['pct'] < 50 and it['budget'] > 0:
                tag = 'under'
            self.bg_tree.insert('', tk.END, values=(
                it['account_code'], it['account_name'],
                {'asset':'资产','liability':'负债','equity':'权益','income':'收入','expense':'费用'}.get(it['category'], it['category']),
                f"{it['budget']:,.2f}", f"{it['actual']:,.2f}",
                f"{it['variance']:,.2f}", f"{it['pct']:.1f}%",
            ), tags=(tag,) if tag else ())

    def _set_budget_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('设置预算')
        win.geometry('550x480')
        win.resizable(False, False)

        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='✏️ 设置预算金额', font=FONT_SUB, bg=self._c('bg')).pack(pady=(0, 10))

        tk.Label(frame, text='科目:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        accts = acc.get_all_accounts()
        acct_choices = [f"{a['code']} {a['name']}" for a in accts]
        self.bg_acct_var = tk.StringVar()
        bg_acct_cb = ttk.Combobox(frame, textvariable=self.bg_acct_var, values=acct_choices,
                                  font=FONT_TEXT, width=50)
        bg_acct_cb.pack(fill=tk.X, pady=(0, 10))

        row = tk.Frame(frame, bg=self._c('bg'))
        row.pack(fill=tk.X)
        tk.Label(row, text='年份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT)
        bg_set_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(row, from_=2024, to=2035, textvariable=bg_set_year, font=FONT_TEXT, width=8).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15,2))
        bg_set_month = tk.StringVar(value='1')
        tk.Spinbox(row, from_=1, to=12, textvariable=bg_set_month, font=FONT_TEXT, width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(frame, text='预算金额:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10, 2))
        bg_set_amount = tk.StringVar(value='0')
        tk.Entry(frame, textvariable=bg_set_amount, font=('Consolas', 11)).pack(fill=tk.X)

        tk.Label(frame, text='备注:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10, 2))
        bg_set_note = tk.Text(frame, font=('Consolas', 10), height=3)
        bg_set_note.pack(fill=tk.X)

        def do_set_budget():
            acct = self.bg_acct_var.get().strip()
            if not acct:
                messagebox.showwarning('提示', '请选择科目')
                return
            code = acct.split()[0]
            try:
                year = int(bg_set_year.get())
                month = int(bg_set_month.get())
                amount = float(bg_set_amount.get())
            except ValueError:
                messagebox.showerror('错误', '请填写有效数字')
                return
            acc.set_budget(code, year, month, amount, bg_set_note.get('1.0', tk.END).strip())
            messagebox.showinfo('成功', '预算已保存')
            win.destroy()
            self._refresh_budget()

        tk.Button(frame, text='💾 保存预算', font=FONT_TEXT, command=do_set_budget,
                  bg=self._c('primary'), fg='white', width=20, pady=4).pack(pady=15)
