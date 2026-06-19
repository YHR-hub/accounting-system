from __future__ import annotations
"""创业工具标签页 (大学生报税, 小微记账, 考证规划)。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class StartupTabMixin:
    def _build_startup_tab(self):
        f = self.tabs['startup']

        sub = ttk.Notebook(f)
        sub.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.st_pages = {}
        for key, label in [('tax', '  大学生报税  '), ('ledger', '  小微记账  '), ('exam', '  考证规划  ')]:
            frame = tk.Frame(sub, bg=self._c('bg'))
            sub.add(frame, text=label)
            self.st_pages[key] = frame

        self._build_student_tax_page()
        self._build_micro_ledger_page()
        self._build_exam_planner_page()

    def _build_student_tax_page(self):
        f = self.st_pages['tax']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='💰 大学生报税助手', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Label(top, text='年收入(元):', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.st_income = tk.Entry(top, font=FONT_TEXT, width=12)
        self.st_income.pack(side=tk.LEFT, padx=2)
        self.st_income.insert(0, '30000')
        tk.Button(top, text='计算税负', font=FONT_TEXT, command=self._st_calc_tax,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📖 报税指南', font=FONT_TEXT, command=self._st_show_guide,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)

        self.st_result = tk.Text(f, font=('Consolas', 10), height=10,
                                 relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.st_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _st_calc_tax(self):
        try:
            income = float(self.st_income.get().strip())
        except ValueError:
            messagebox.showwarning('提示', '请输入有效收入金额')
            return
        r = acc.calc_student_tax(income)
        self.st_result.config(state=tk.NORMAL)
        self.st_result.delete('1.0', tk.END)
        self.st_result.insert(tk.END, f'{"="*50}\n')
        self.st_result.insert(tk.END, f'  大学生个税测算\n')
        self.st_result.insert(tk.END, f'{"="*50}\n\n')
        self.st_result.insert(tk.END, f'年收入:         {r["total_income"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'基本减除费用:   {r["standard_deduction"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'应纳税所得额:   {r["taxable_income"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'应缴税款:       {r["tax"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'预估已预缴:     {r["estimated_withheld"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'预计可退税:     {r["refund"]:>10,.2f} 元\n')
        self.st_result.insert(tk.END, f'实际税负率:     {r["effective_rate"]:>9.2f}%\n\n')
        if r['refund_eligible']:
            self.st_result.insert(tk.END, '✅ 你有退税资格！请在个税APP办理汇算清缴\n')
        self.st_result.config(state=tk.DISABLED)

    def _st_show_guide(self):
        guide = acc.get_student_tax_guide()
        self.st_result.config(state=tk.NORMAL)
        self.st_result.delete('1.0', tk.END)
        self.st_result.insert(tk.END, guide)
        self.st_result.config(state=tk.DISABLED)

    def _build_micro_ledger_page(self):
        f = self.st_pages['ledger']
        acc.init_micro_ledger()

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📒 小微企业流水账', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Label(top, text='年:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.ml_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.ml_year, width=6,
                   font=FONT_TEXT).pack(side=tk.LEFT)
        tk.Label(top, text='月:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.ml_month = tk.StringVar(value=str(date.today().month))
        tk.Spinbox(top, from_=0, to=12, textvariable=self.ml_month, width=4,
                   font=FONT_TEXT).pack(side=tk.LEFT)
        tk.Button(top, text='刷新', font=FONT_TEXT, command=self._ml_refresh,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)

        form = tk.Frame(f, bg=self._c('bg'))
        form.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(form, text='日期(YYYY-MM-DD):', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.ml_date = tk.Entry(form, font=FONT_TEXT, width=12)
        self.ml_date.pack(side=tk.LEFT, padx=2)
        self.ml_date.insert(0, date.today().isoformat())

        self.ml_type_var = tk.StringVar(value='income')
        tk.Radiobutton(form, text='收入', variable=self.ml_type_var, value='income',
                       font=FONT_TEXT, bg=self._c('bg'), fg='#7BC67E').pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(form, text='支出', variable=self.ml_type_var, value='expense',
                       font=FONT_TEXT, bg=self._c('bg'), fg='#FF4757').pack(side=tk.LEFT, padx=2)

        self.ml_cat_var = tk.StringVar()
        ml_cats = [c for cats in acc.MICRO_CATEGORIES.values() for c in cats]
        ttk.Combobox(form, textvariable=self.ml_cat_var, values=ml_cats,
                     width=10, font=FONT_TEXT).pack(side=tk.LEFT, padx=2)
        self.ml_cat_var.set('销售收入')

        self.ml_amt = tk.Entry(form, font=FONT_TEXT, width=10)
        self.ml_amt.pack(side=tk.LEFT, padx=2)
        self.ml_amt.insert(0, '0.00')

        self.ml_note = tk.Entry(form, font=FONT_TEXT, width=12)
        self.ml_note.pack(side=tk.LEFT, padx=2)
        self.ml_note.insert(0, '备注')

        tk.Button(form, text='添加', font=FONT_TEXT, command=self._ml_add,
                  bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = tk.Frame(panes, bg=self._c('bg'))
        panes.add(left, width=400)
        cols = ('id', 'date', 'type', 'cat', 'amount', 'note')
        self.ml_tree = ttk.Treeview(left, columns=cols, show='headings', height=12)
        self.ml_tree.heading('id', text='ID')
        self.ml_tree.heading('date', text='日期')
        self.ml_tree.heading('type', text='类型')
        self.ml_tree.heading('cat', text='分类')
        self.ml_tree.heading('amount', text='金额')
        self.ml_tree.heading('note', text='备注')
        for c in cols:
            self.ml_tree.column(c, width=60 if c in ('id','type') else 80)
        self.ml_tree.column('date', width=100)
        self.ml_tree.pack(fill=tk.BOTH, expand=True)
        self.ml_tree.bind('<Delete>', self._ml_delete)

        right = tk.Frame(panes, bg=self._c('bg'))
        panes.add(right, width=200)
        self.ml_summary = tk.Text(right, font=('Consolas', 10), height=10,
                                  relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.ml_summary.pack(fill=tk.BOTH, expand=True)

        self._ml_refresh()

    def _ml_refresh(self):
        for item in self.ml_tree.get_children():
            self.ml_tree.delete(item)
        year = int(self.ml_year.get())
        month = int(self.ml_month.get())
        entries = acc.get_micro_entries(year, month)
        for e in entries:
            tag = 'income' if e['type'] == 'income' else 'expense'
            self.ml_tree.insert('', tk.END, iid=str(e['id']),
                                values=(e['id'], e['date'], '收入' if e['type']=='income' else '支出',
                                        e['category'], f'{e["amount"]:.2f}', e.get('note','')),
                                tags=(tag,))
        self.ml_tree.tag_configure('income', foreground='#7BC67E')
        self.ml_tree.tag_configure('expense', foreground='#FF4757')

        summary = acc.calc_micro_summary(year, month)
        self.ml_summary.config(state=tk.NORMAL)
        self.ml_summary.delete('1.0', tk.END)
        period = f'{year}年{month:02d}月' if month else f'{year}年'
        self.ml_summary.insert(tk.END, f'📊 {period}汇总\n{"─"*25}\n\n')
        self.ml_summary.insert(tk.END, f'总收入: {summary["total_income"]:>8,.2f}\n')
        self.ml_summary.insert(tk.END, f'总支出: {summary["total_expense"]:>8,.2f}\n')
        self.ml_summary.insert(tk.END, f'净利润: {summary["profit"]:>8,.2f}\n')
        self.ml_summary.insert(tk.END, f'笔数:   {summary["count"]:>8d}\n')
        self.ml_summary.config(state=tk.DISABLED)

    def _ml_add(self):
        date_str = self.ml_date.get().strip()
        e_type = self.ml_type_var.get()
        cat = self.ml_cat_var.get().strip()
        try:
            amt = float(self.ml_amt.get().strip())
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('提示', '金额必须为正数')
            return
        note = self.ml_note.get().strip()
        if acc.add_micro_entry(date_str, e_type, cat, amt, note):
            self._ml_refresh()
            self.ml_amt.delete(0, tk.END)
            self.ml_amt.insert(0, '0.00')
        else:
            messagebox.showerror('错误', '添加失败')

    def _ml_delete(self, event=None):
        selected = self.ml_tree.selection()
        if not selected:
            return
        if messagebox.askyesno('确认', '删除选中记录？'):
            for item in selected:
                eid = int(item)
                acc.delete_micro_entry(eid)
            self._ml_refresh()

    def _build_exam_planner_page(self):
        f = self.st_pages['exam']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📚 考证时间规划器', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        cert_names = {k: v['name'] for k, v in acc.CERT_EXAMS.items()}
        self.ex_cert_var = tk.StringVar()
        cert_list = list(cert_names.values())
        ttk.Combobox(top, textvariable=self.ex_cert_var, values=cert_list,
                     width=20, font=FONT_TEXT, state='readonly').pack(side=tk.LEFT, padx=5)
        if cert_list:
            self.ex_cert_var.set(cert_list[0])

        tk.Label(top, text='开始日期:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.ex_start = tk.Entry(top, font=FONT_TEXT, width=12)
        self.ex_start.pack(side=tk.LEFT, padx=2)
        self.ex_start.insert(0, date.today().isoformat())

        tk.Label(top, text='每日学时:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.ex_hours = tk.StringVar(value='2.0')
        tk.Spinbox(top, from_=0.5, to=8.0, increment=0.5, textvariable=self.ex_hours,
                   font=FONT_TEXT, width=5).pack(side=tk.LEFT)

        tk.Button(top, text='生成计划', font=FONT_TEXT, command=self._ex_generate,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = tk.Frame(panes, bg=self._c('bg'))
        panes.add(left, width=250)
        self.ex_info = tk.Text(left, font=('Consolas', 10), height=8,
                               relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.ex_info.pack(fill=tk.BOTH, expand=True)

        right = tk.Frame(panes, bg=self._c('bg'))
        panes.add(right, width=500)
        self.ex_plan = tk.Text(right, font=('Consolas', 10), height=20,
                               relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.ex_plan.pack(fill=tk.BOTH, expand=True)

        self._ex_show_info()

    def _ex_show_info(self, event=None):
        name = self.ex_cert_var.get()
        cert_key = None
        for k, v in acc.CERT_EXAMS.items():
            if v['name'] == name:
                cert_key = k
                break
        if not cert_key:
            return
        info = acc.CERT_EXAMS[cert_key]
        self.ex_info.config(state=tk.NORMAL)
        self.ex_info.delete('1.0', tk.END)
        self.ex_info.insert(tk.END, f'📋 {info["name"]}\n')
        self.ex_info.insert(tk.END, f'难度: {info["difficulty"]}\n')
        self.ex_info.insert(tk.END, f'考试时间: {info["typical_date"]}\n')
        self.ex_info.insert(tk.END, f'报名时间: {info["registration"]}\n')
        self.ex_info.insert(tk.END, f'总学时: {info["total_hours"]}h\n')
        self.ex_info.insert(tk.END, f'科目数: {len(info["subjects"])}\n')
        self.ex_info.insert(tk.END, f'简介: {info["description"]}\n')
        self.ex_info.insert(tk.END, '\n📖 科目:\n')
        for s in info['subjects']:
            h = info['study_hours'].get(s, 0)
            self.ex_info.insert(tk.END, f'  {s}: {h}h\n')
        self.ex_info.config(state=tk.DISABLED)

    def _ex_generate(self):
        name = self.ex_cert_var.get()
        cert_key = None
        for k, v in acc.CERT_EXAMS.items():
            if v['name'] == name:
                cert_key = k
                break
        if not cert_key:
            return
        start = self.ex_start.get().strip()
        try:
            hours = float(self.ex_hours.get())
        except ValueError:
            hours = 2.0
        plan = acc.format_study_plan(cert_key, start, hours)
        self.ex_plan.config(state=tk.NORMAL)
        self.ex_plan.delete('1.0', tk.END)
        self.ex_plan.insert(tk.END, plan)
        self.ex_plan.config(state=tk.DISABLED)
