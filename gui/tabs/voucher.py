from __future__ import annotations
"""凭证录入标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class VoucherTabMixin:
    def _build_voucher_tab(self):
        f = self.tabs['voucher']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=10)

        tk.Label(top, text='日期:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=5)
        self.v_date = tk.Entry(top, font=FONT_TEXT, width=14)
        self.v_date.pack(side=tk.LEFT, padx=2)
        self.v_date.insert(0, date.today().isoformat())

        tk.Label(top, text='摘要:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15, 2))
        self.v_summary = tk.Entry(top, font=FONT_TEXT, width=40)
        self.v_summary.pack(side=tk.LEFT, padx=2)

        tk.Button(top, text='+ 清零', font=FONT_TEXT,
                  command=self._clear_voucher, bg='#E8D5F5').pack(side=tk.RIGHT, padx=5)

        grid = ttk.Frame(f)
        grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ('code', 'name', 'amount', 'direction')
        self.v_tree = ttk.Treeview(grid, columns=cols, show='headings', height=6)
        self.v_tree.heading('code', text='科目编码')
        self.v_tree.heading('name', text='科目名称')
        self.v_tree.heading('amount', text='金额')
        self.v_tree.heading('direction', text='方向')
        self.v_tree.column('code', width=100)
        self.v_tree.column('name', width=160)
        self.v_tree.column('amount', width=120)
        self.v_tree.column('direction', width=60)
        self.v_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(grid, orient=tk.VERTICAL, command=self.v_tree.yview)
        self.v_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        inp = tk.Frame(f, bg=self._c('bg'))
        inp.pack(fill=tk.X, pady=5)

        accounts = acc.load_accounts_from_db()
        self.acc_names = {a['code']: a['name'] for a in accounts}
        self.acc_codes = sorted(self.acc_names.keys())
        self.v_code_var = tk.StringVar()
        self.v_code_combo = ttk.Combobox(inp, textvariable=self.v_code_var,
                                         values=self.acc_codes, width=12, font=FONT_TEXT)
        self.v_code_combo.pack(side=tk.LEFT, padx=2)
        self.v_code_combo.bind('<<ComboboxSelected>>', self._on_code_change)
        self.v_code_combo.bind('<KeyRelease>', self._on_code_change)

        self.v_name_label = tk.Label(inp, text='', font=FONT_TEXT, bg='white', width=18, anchor='w', relief=tk.SUNKEN)
        self.v_name_label.pack(side=tk.LEFT, padx=2)

        self.v_amount = tk.Entry(inp, font=FONT_TEXT, width=14)
        self.v_amount.pack(side=tk.LEFT, padx=2)
        self.v_amount.insert(0, '0.00')

        self.v_dir = tk.StringVar(value='d')
        tk.Radiobutton(inp, text='借', variable=self.v_dir, value='d',
                       font=FONT_TEXT, bg=self._c('bg'), fg='#FF4757').pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(inp, text='贷', variable=self.v_dir, value='c',
                       font=FONT_TEXT, bg=self._c('bg'), fg='#7C3AED').pack(side=tk.LEFT, padx=2)

        tk.Button(inp, text='添加分录', font=FONT_TEXT,
                  command=self._add_entry, bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)
        tk.Button(inp, text='删除选中', font=FONT_TEXT,
                  command=self._remove_entry, bg='#FF6B6B', fg='white').pack(side=tk.LEFT, padx=2)

        bal = tk.Frame(f, bg=self._c('bg'))
        bal.pack(fill=tk.X, pady=2)
        self.lb_debit = tk.Label(bal, text='借方: 0.00', font=FONT_TEXT,
                                 bg=self._c('alt'), fg='#FF4757', width=16, relief=tk.RIDGE)
        self.lb_debit.pack(side=tk.LEFT, padx=5)
        self.lb_credit = tk.Label(bal, text='贷方: 0.00', font=FONT_TEXT,
                                  bg=self._c('alt'), fg='#7C3AED', width=16, relief=tk.RIDGE)
        self.lb_credit.pack(side=tk.LEFT, padx=5)
        self.lb_diff = tk.Label(bal, text='差额: 0.00', font=FONT_TEXT,
                                bg=self._c('alt'), width=20, relief=tk.RIDGE)
        self.lb_diff.pack(side=tk.LEFT, padx=5)
        self.lb_status = tk.Label(bal, text='', font=FONT_TEXT, bg=self._c('bg'))
        self.lb_status.pack(side=tk.LEFT, padx=10)

        tk.Button(bal, text='💾  保存凭证', font=('微软雅黑', 12, 'bold'),
                  command=self._save_voucher, bg=self._c('primary'), fg='white',
                  padx=20).pack(side=tk.RIGHT, padx=10)

        tk.Label(f, text='已生成的凭证:', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w', padx=10, pady=(10, 0))
        self.v_output = tk.Text(f, font=('Consolas', 10), height=8, relief=tk.SUNKEN,
                                bg='#FFF0F5', state=tk.DISABLED)
        self.v_output.pack(fill=tk.BOTH, padx=10, pady=5)

        tpl_frame = tk.Frame(f, bg=self._c('bg'))
        tpl_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(tpl_frame, text='📋 凭证模板:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.tpl_var = tk.StringVar()
        template_names = acc.get_template_names()
        self.tpl_combo = ttk.Combobox(tpl_frame, textvariable=self.tpl_var,
                                       values=template_names, width=18, font=FONT_TEXT, state='readonly')
        self.tpl_combo.pack(side=tk.LEFT, padx=2)
        if template_names:
            self.tpl_var.set(template_names[0])
        tk.Label(tpl_frame, text='金额:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.tpl_amount = tk.Entry(tpl_frame, font=FONT_TEXT, width=12)
        self.tpl_amount.pack(side=tk.LEFT, padx=2)
        self.tpl_amount.insert(0, '1000.00')
        tk.Button(tpl_frame, text='一键生成', font=FONT_TEXT,
                  command=self._apply_template, bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)
        self.tpl_desc = tk.Label(tpl_frame, text='', font=FONT_SMALL, bg=self._c('bg'), fg='gray')
        self.tpl_desc.pack(side=tk.LEFT, padx=5)
        self.tpl_combo.bind('<<ComboboxSelected>>', self._on_template_select)
        if template_names:
            self._on_template_select()

    def _on_template_select(self, event=None):
        name = self.tpl_var.get()
        if name and name in acc.VOUCHER_TEMPLATES:
            self.tpl_desc.config(text=acc.VOUCHER_TEMPLATES[name].get("desc", ""))

    def _apply_template(self):
        name = self.tpl_var.get()
        if not name:
            messagebox.showwarning('提示', '请选择模板')
            return
        try:
            amt = float(self.tpl_amount.get().strip())
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('提示', '金额必须为正数')
            return
        date_str = self.v_date.get().strip()
        v_no = acc.apply_voucher_template(name, amt, date_str)
        if v_no:
            messagebox.showinfo('成功', f'凭证已生成: {v_no}')
            self._refresh_voucher_list()
        else:
            messagebox.showerror('错误', '模板生成失败')

    def _on_code_change(self, event=None):
        code = self.v_code_var.get()
        if code in self.acc_names:
            self.v_name_label.config(text=self.acc_names[code])
        else:
            self.v_name_label.config(text='')

    def _add_entry(self):
        code = self.v_code_var.get().strip()
        if code not in self.acc_names:
            messagebox.showwarning('提示', '请选择有效科目')
            return
        try:
            amt = float(self.v_amount.get().strip())
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('提示', '金额必须为正数')
            return
        direction = '借' if self.v_dir.get() == 'd' else '贷'
        self.v_tree.insert('', tk.END, values=(code, self.acc_names[code], f'{amt:.2f}', direction))
        self._update_balance()

    def _remove_entry(self):
        selected = self.v_tree.selection()
        if selected:
            for item in selected:
                self.v_tree.delete(item)
            self._update_balance()

    def _update_balance(self):
        total_d = 0.0
        total_c = 0.0
        for item in self.v_tree.get_children():
            vals = self.v_tree.item(item, 'values')
            amt = float(vals[2])
            if vals[3] == '借':
                total_d += amt
            else:
                total_c += amt
        self.lb_debit.config(text=f'借方: {total_d:.2f}')
        self.lb_credit.config(text=f'贷方: {total_c:.2f}')
        diff = total_d - total_c
        self.lb_diff.config(text=f'差额: {diff:.2f}')
        if abs(diff) < 0.01:
            self.lb_status.config(text='✓ 借贷平衡', fg='green')
        else:
            self.lb_status.config(text='✗ 借贷不平', fg='red')

    def _clear_voucher(self):
        for item in self.v_tree.get_children():
            self.v_tree.delete(item)
        self.v_summary.delete(0, tk.END)
        self.v_output.config(state=tk.NORMAL)
        self.v_output.delete('1.0', tk.END)
        self.v_output.config(state=tk.DISABLED)
        self._update_balance()
        self.lb_status.config(text='')

    def _save_voucher(self):
        entries = []
        total_d = 0.0
        total_c = 0.0
        for item in self.v_tree.get_children():
            vals = self.v_tree.item(item, 'values')
            amt = float(vals[2])
            if vals[3] == '借':
                total_d += amt
                entries.append({'code': vals[0], 'debit': amt, 'credit': 0})
            else:
                total_c += amt
                entries.append({'code': vals[0], 'debit': 0, 'credit': amt})

        if abs(total_d - total_c) > 0.01:
            messagebox.showerror('错误', f'借贷不平！借方={total_d:.2f} 贷方={total_c:.2f}')
            return
        if total_d == 0:
            messagebox.showwarning('提示', '请至少添加一条分录')
            return
        summary = self.v_summary.get().strip()
        if not summary:
            messagebox.showwarning('提示', '请输入摘要')
            return
        date_str = self.v_date.get().strip()
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror('错误', '日期格式错误 (YYYY-MM-DD)')
            return

        year, month = dt.year, dt.month
        conn = acc.get_conn()
        try:
            v_no = acc.next_voucher_no(year, month)
            cur = conn.execute(
                'INSERT INTO vouchers (voucher_no, date, summary, fiscal_year, fiscal_month) VALUES (?,?,?,?,?)',
                (v_no, date_str, summary, year, month))
            vid = cur.lastrowid
            for e in entries:
                conn.execute(
                    'INSERT INTO journal_entries (voucher_id, account_code, debit, credit) VALUES (?,?,?,?)',
                    (vid, e['code'], e['debit'], e['credit']))
            conn.commit()

            self.v_output.config(state=tk.NORMAL)
            self.v_output.delete('1.0', tk.END)
            acc.show_voucher(vid, conn)
            conn.close()

            out = self.v_output.get('1.0', tk.END)
            self.v_output.delete('1.0', tk.END)
            self.v_output.insert(tk.END, out)
            self.v_output.config(state=tk.DISABLED)

            messagebox.showinfo('成功', f'凭证已保存: {v_no}')
            self._clear_voucher()
            self._refresh_balances()
            self._refresh_voucher_list()
        except Exception as e:
            conn.rollback()
            conn.close()
            messagebox.showerror('错误', f'保存失败: {e}')
