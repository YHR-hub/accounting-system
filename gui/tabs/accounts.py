from __future__ import annotations
"""科目余额标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
from decimal import Decimal
from gui.constants import FONT_TEXT
import accsys as acc

class AccountsTabMixin:
    def _build_accounts_tab(self):
        f = self.tabs['accounts']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=8)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT,
                  command=self._refresh_balances, bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='新增科目', font=FONT_TEXT, command=self._add_account_gui,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='设置期初余额', font=FONT_TEXT, command=self._set_opening_gui,
                  bg='#FFD54F').pack(side=tk.LEFT, padx=5)

        cols = ('code', 'name', 'category', 'balance', 'nature')
        self.a_tree = ttk.Treeview(f, columns=cols, show='headings', height=20)
        self.a_tree.heading('code', text='科目编码')
        self.a_tree.heading('name', text='科目名称')
        self.a_tree.heading('category', text='类别')
        self.a_tree.heading('balance', text='余额')
        self.a_tree.heading('nature', text='方向')
        self.a_tree.column('code', width=100)
        self.a_tree.column('name', width=180)
        self.a_tree.column('category', width=80)
        self.a_tree.column('balance', width=120)
        self.a_tree.column('nature', width=60)

        vsb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.a_tree.yview)
        self.a_tree.configure(yscrollcommand=vsb.set)
        self.a_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_balances()

    def _refresh_balances(self):
        for item in self.a_tree.get_children():
            self.a_tree.delete(item)
        accounts = acc.load_accounts_from_db()
        try:
            balances = acc.calc_balances(accounts)
        except Exception:
            balances = {}

        total_d = Decimal('0')
        total_c = Decimal('0')
        cat_labels = {'asset': '资产', 'liability': '负债', 'equity': '权益', 'income': '收入', 'expense': '费用'}
        for a in accounts:
            code = a['code']
            bal = balances.get(code, Decimal('0'))
            bal_f = float(bal)
            if bal_f > 0 and a['nature'] == 'debit':
                total_d += bal
                nature = '借'
            elif bal_f > 0 and a['nature'] == 'credit':
                total_c += bal
                nature = '贷'
            elif bal_f < 0 and a['nature'] == 'debit':
                total_c += -bal
                nature = '贷'
            elif bal_f < 0 and a['nature'] == 'credit':
                total_d += -bal
                nature = '借'
            else:
                nature = '-'

            self.a_tree.insert('', tk.END, values=(
                code, a['name'], cat_labels.get(a['category'], a['category']),
                f'{abs(bal_f):.2f}', nature,
            ))

        self.a_tree.insert('', tk.END, values=('', '──── 合计 ────', '',
                                                f'借: {float(total_d):.2f}  贷: {float(total_c):.2f}', ''))

    def _add_account_gui(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('新增科目')
        dialog.geometry('400x280+500+300')
        dialog.resizable(False, False)

        tk.Label(dialog, text='科目编码:', font=FONT_TEXT).pack(pady=(15, 2))
        code_e = tk.Entry(dialog, font=FONT_TEXT, width=20)
        code_e.pack()

        tk.Label(dialog, text='科目名称:', font=FONT_TEXT).pack(pady=(10, 2))
        name_e = tk.Entry(dialog, font=FONT_TEXT, width=30)
        name_e.pack()

        tk.Label(dialog, text='类别:', font=FONT_TEXT).pack(pady=(10, 2))
        cat_var = tk.StringVar(value='asset')
        cf = tk.Frame(dialog)
        cf.pack()
        for k, v in [('asset', '资产'), ('liability', '负债'), ('equity', '权益'), ('income', '收入'), ('expense', '费用')]:
            tk.Radiobutton(cf, text=v, variable=cat_var, value=k, font=FONT_TEXT).pack(side=tk.LEFT, padx=5)

        def submit():
            code = code_e.get().strip()
            name = name_e.get().strip()
            cat = cat_var.get()
            if not code or not name:
                messagebox.showwarning('提示', '请填写完整')
                return
            conn = acc.get_conn()
            try:
                nature = 'debit' if cat in ('asset', 'expense') else 'credit'
                conn.execute('INSERT INTO accounts (code,name,category,nature) VALUES (?,?,?,?)',
                             (code, name, cat, nature))
                conn.commit()
                messagebox.showinfo('成功', f'科目 {code}-{name} 已添加')
                dialog.destroy()
                self._refresh_balances()
                acc._sync_accounts_to_json()
            except sqlite3.IntegrityError:
                messagebox.showerror('错误', '科目编码已存在')
            conn.close()

        tk.Button(dialog, text='确认添加', font=FONT_TEXT, command=submit,
                  bg=self._c('primary'), fg='white').pack(pady=15)

    def _set_opening_gui(self):
        code = simpledialog.askstring('设置期初余额', '输入科目编码:')
        if not code:
            return
        accounts = acc.load_accounts_from_db()
        if not any(a['code'] == code for a in accounts):
            messagebox.showerror('错误', '科目不存在')
            return
        amt = simpledialog.askfloat('设置期初余额', '金额 (借方为正, 贷方为负):')
        if amt is None:
            return
        conn = acc.get_conn()
        year = datetime.now().year
        conn.execute(
            'INSERT OR REPLACE INTO opening_balances (account_code, amount, fiscal_year) VALUES (?,?,?)',
            (code, amt, year))
        conn.commit()
        conn.close()
        messagebox.showinfo('成功', f'科目 {code} 期初余额已设置')
        self._refresh_balances()
