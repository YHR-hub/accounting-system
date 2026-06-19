from __future__ import annotations
"""薪资管理标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class PayrollTabMixin:
    def _build_payroll_tab(self):
        f = self.tabs['payroll']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='💰 薪资管理', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Button(top, text='➕ 添加员工', font=FONT_TEXT, command=self._add_employee_dialog,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Label(top, text='年份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15,2))
        self.pr_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2024, to=2035, textvariable=self.pr_year,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT)
        tk.Label(top, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(5,2))
        self.pr_month = tk.StringVar(value=str(date.today().month))
        tk.Spinbox(top, from_=1, to=12, textvariable=self.pr_month,
                   font=FONT_TEXT, width=5).pack(side=tk.LEFT)
        tk.Button(top, text='🧮 计算工资', font=FONT_TEXT, command=self._calc_payroll,
                  bg=self._c('accent'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='✅ 确认发放', font=FONT_TEXT, command=self._confirm_payroll,
                  bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📄 生成凭证', font=FONT_TEXT, command=self._gen_payroll_voucher,
                  bg=self._c('warn'), fg='white').pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.VERTICAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        etop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(etop, height=160)
        tk.Label(etop, text='👥 员工列表 (双击编辑)', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        ecols = ('id', 'code', 'name', 'dept', 'pos', 'salary', 'insurance', 'fund')
        self.emp_tree = ttk.Treeview(etop, columns=ecols, show='headings', height=5)
        self.emp_tree.heading('id', text='ID')
        self.emp_tree.heading('code', text='工号')
        self.emp_tree.heading('name', text='姓名')
        self.emp_tree.heading('dept', text='部门')
        self.emp_tree.heading('pos', text='职位')
        self.emp_tree.heading('salary', text='基本工资')
        self.emp_tree.heading('insurance', text='社保')
        self.emp_tree.heading('fund', text='公积金')
        for c in ecols:
            w = 40 if c=='id' else 60 if c in ('code','insurance','fund') else 80 if c in ('dept','pos') else 100 if c in ('salary',) else 120 if c=='name' else 60
            self.emp_tree.column(c, width=w, anchor='e' if c in ('salary','insurance','fund') else 'w')
            self.emp_tree.column('id', width=40, anchor='center')
            self.emp_tree.column('code', width=60, anchor='center')
        self.emp_tree.pack(fill=tk.BOTH, expand=True)
        self.emp_tree.bind('<Double-1>', self._edit_employee_dialog)

        ptop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(ptop)
        tk.Label(ptop, text='📋 工资记录', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        pcols = ('id', 'emp', 'name', 'dept', 'gross', 'ins', 'fund', 'taxable', 'tax', 'net', 'status')
        self.pr_tree = ttk.Treeview(ptop, columns=pcols, show='headings', height=8)
        self.pr_tree.heading('id', text='ID')
        self.pr_tree.heading('emp', text='工号')
        self.pr_tree.heading('name', text='姓名')
        self.pr_tree.heading('dept', text='部门')
        self.pr_tree.heading('gross', text='应发')
        self.pr_tree.heading('ins', text='社保')
        self.pr_tree.heading('fund', text='公积金')
        self.pr_tree.heading('taxable', text='应税')
        self.pr_tree.heading('tax', text='个税')
        self.pr_tree.heading('net', text='实发')
        self.pr_tree.heading('status', text='状态')
        for c in pcols:
            w = 40 if c=='id' else 55 if c in ('emp','tax','status') else 70 if c in ('ins','fund','taxable') else 80 if c in ('gross','net') else 60 if c=='dept' else 100 if c=='name' else 60
            self.pr_tree.column(c, width=w, anchor='e' if c in ('gross','ins','fund','taxable','tax','net') else 'w')
            self.pr_tree.column('id', width=40, anchor='center')
            self.pr_tree.column('emp', width=55, anchor='center')
            self.pr_tree.column('status', width=55, anchor='center')
        self.pr_tree.pack(fill=tk.BOTH, expand=True)
        self._refresh_payroll()

    def _refresh_payroll(self):
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        emps = acc.get_all_employees()
        for e in emps:
            self.emp_tree.insert('', tk.END, values=(
                e['id'], e['code'], e['name'], e['department'], e['position'],
                f"{e['base_salary']:,.2f}", f"{e['insurance']:,.2f}", f"{e['housing_fund']:,.2f}",
            ))
        self._refresh_payroll_records()

    def _refresh_payroll_records(self):
        for item in self.pr_tree.get_children():
            self.pr_tree.delete(item)
        try:
            year = int(self.pr_year.get())
            month = int(self.pr_month.get())
        except ValueError:
            return
        rows = acc.get_payroll_records(year=year, month=month)
        for r in rows:
            status_cn = {'draft':'📝草稿','confirmed':'✅已确认','paid':'💰已付'}.get(r['status'], r['status'])
            self.pr_tree.insert('', tk.END, values=(
                r['id'], r['emp_code'], r['emp_name'], r['department'],
                f"{r['gross_pay']:,.2f}", f"{r['insurance']:,.2f}", f"{r['housing_fund']:,.2f}",
                f"{r['taxable_income']:,.2f}", f"{r['income_tax']:,.2f}",
                f"{r['net_pay']:,.2f}", status_cn,
            ))

    def _add_employee_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('添加员工')
        win.geometry('400x380')
        win.resizable(False, False)
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text='➕ 添加员工', font=FONT_SUB, bg=self._c('bg')).pack(pady=(0,10))
        labels = [('工号:', 'code'), ('姓名:', 'name'), ('部门:', 'dept'), ('职位:', 'pos'),
                  ('基本工资:', 'salary'), ('社保:', 'ins'), ('公积金:', 'fund')]
        vars_ = {}
        for lbl, key in labels:
            tk.Label(frame, text=lbl, font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
            v = tk.StringVar(value='0' if key in ('salary','ins','fund') else '')
            vars_[key] = v
            tk.Entry(frame, textvariable=v, font=FONT_TEXT).pack(fill=tk.X, pady=(0,3))
        def do_add():
            try:
                r = acc.add_employee(vars_['code'].get(), vars_['name'].get(), vars_['dept'].get(),
                                     vars_['pos'].get(), float(vars_['salary'].get() or 0),
                                     float(vars_['ins'].get() or 0), float(vars_['fund'].get() or 0))
            except ValueError:
                messagebox.showerror('错误', '金额必须是数字')
                return
            if r.get('success'):
                messagebox.showinfo('成功', '员工已添加')
                win.destroy()
                self._refresh_payroll()
            else:
                messagebox.showerror('错误', r.get('error',''))
        tk.Button(frame, text='💾 保存', font=FONT_TEXT, command=do_add,
                  bg=self._c('primary'), fg='white', width=15, pady=3).pack(pady=10)

    def _edit_employee_dialog(self, event=None):
        sel = self.emp_tree.selection()
        if not sel:
            return
        vals = self.emp_tree.item(sel[0], 'values')
        eid = int(vals[0])
        win = tk.Toplevel(self.root)
        win.title('编辑员工')
        win.geometry('400x380')
        win.resizable(False, False)
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text='✏️ 编辑员工', font=FONT_SUB, bg=self._c('bg')).pack(pady=(0,10))
        labels = [('姓名:', 'name'), ('部门:', 'dept'), ('职位:', 'pos'),
                  ('基本工资:', 'salary'), ('社保:', 'ins'), ('公积金:', 'fund')]
        vars_ = {}
        defaults = {'name': vals[2], 'dept': vals[3], 'pos': vals[4],
                    'salary': vals[5], 'ins': vals[6], 'fund': vals[7]}
        for lbl, key in labels:
            tk.Label(frame, text=lbl, font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
            v = tk.StringVar(value=defaults[key])
            vars_[key] = v
            tk.Entry(frame, textvariable=v, font=FONT_TEXT).pack(fill=tk.X, pady=(0,3))
        def do_update():
            try:
                acc.update_employee(eid, name=vars_['name'].get(), department=vars_['dept'].get(),
                                    position=vars_['pos'].get(), base_salary=float(vars_['salary'].get() or 0),
                                    insurance=float(vars_['ins'].get() or 0), housing_fund=float(vars_['fund'].get() or 0))
            except ValueError:
                messagebox.showerror('错误', '金额必须是数字')
                return
            messagebox.showinfo('成功', '员工信息已更新')
            win.destroy()
            self._refresh_payroll()
        tk.Button(frame, text='💾 保存', font=FONT_TEXT, command=do_update,
                  bg=self._c('accent'), fg='white', width=15, pady=3).pack(pady=10)

    def _calc_payroll(self):
        try:
            year = int(self.pr_year.get())
            month = int(self.pr_month.get())
        except ValueError:
            return
        results = acc.calculate_payroll(year, month)
        messagebox.showinfo('计算完成', f'已计算 {len(results)} 名员工的工资')
        self._refresh_payroll_records()

    def _confirm_payroll(self):
        sel = self.pr_tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请选择要确认的工资记录')
            return
        ids = []
        for item in sel:
            vals = self.pr_tree.item(item, 'values')
            if vals[10] in ('📝草稿', 'draft'):
                ids.append(int(vals[0]))
        if not ids:
            messagebox.showinfo('提示', '所选记录已经确认或已支付')
            return
        acc.confirm_payroll(ids)
        messagebox.showinfo('成功', f'已确认 {len(ids)} 条工资记录')
        self._refresh_payroll_records()

    def _gen_payroll_voucher(self):
        try:
            year = int(self.pr_year.get())
            month = int(self.pr_month.get())
        except ValueError:
            return
        result = acc.generate_payroll_voucher(year, month)
        if result.get('success'):
            messagebox.showinfo('成功', f'已生成凭证 #{result["voucher_no"]}')
            self._refresh_payroll_records()
        else:
            messagebox.showwarning('提示', result.get('error','生成失败'))
