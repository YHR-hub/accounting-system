from __future__ import annotations
"""项目会计标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class ProjectsTabMixin:
    def _build_projects_tab(self):
        f = self.tabs['projects']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='🏗️ 项目会计', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='➕ 新建项目', font=FONT_TEXT, command=self._add_project_dialog,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_projects,
                  bg=self._c('bg'), fg=self._c('accent')).pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.VERTICAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ptop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(ptop, height=180)
        tk.Label(ptop, text='📋 项目列表 (双击查看损益)', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        cols = ('id', 'code', 'name', 'budget', 'start', 'end', 'status')
        self.pj_tree = ttk.Treeview(ptop, columns=cols, show='headings', height=7)
        self.pj_tree.heading('id', text='ID')
        self.pj_tree.heading('code', text='项目编码')
        self.pj_tree.heading('name', text='项目名称')
        self.pj_tree.heading('budget', text='预算')
        self.pj_tree.heading('start', text='开始日期')
        self.pj_tree.heading('end', text='结束日期')
        self.pj_tree.heading('status', text='状态')
        self.pj_tree.column('id', width=40, anchor='center')
        self.pj_tree.column('code', width=80, anchor='center')
        self.pj_tree.column('name', width=180)
        self.pj_tree.column('budget', width=110, anchor='e')
        self.pj_tree.column('start', width=100, anchor='center')
        self.pj_tree.column('end', width=100, anchor='center')
        self.pj_tree.column('status', width=60, anchor='center')
        self.pj_tree.pack(fill=tk.BOTH, expand=True)
        self.pj_tree.bind('<Double-1>', self._show_project_pnl)

        btop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(btop)
        tk.Label(btop, text='📊 项目损益', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        self.pnl_text = tk.Text(btop, font=('Consolas', 11), relief=tk.SUNKEN,
                                 bg=self._c('bg'), state=tk.DISABLED, height=6)
        self.pnl_text.pack(fill=tk.BOTH, expand=True, pady=2)
        self._refresh_projects()

    def _refresh_projects(self):
        for item in self.pj_tree.get_children():
            self.pj_tree.delete(item)
        projects = acc.get_all_projects()
        for p in projects:
            status_cn = {'active':'进行中','completed':'已完成','suspended':'暂停'}.get(p['status'], p['status'])
            self.pj_tree.insert('', tk.END, values=(
                p['id'], p['code'], p['name'],
                f"{p['budget']:,.2f}", p['start_date'], p['end_date'], status_cn,
            ))

    def _add_project_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('新建项目')
        win.geometry('400x350')
        win.resizable(False, False)
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text='➕ 新建项目', font=FONT_SUB, bg=self._c('bg')).pack(pady=(0,10))
        labels = [('项目编码:', 'code'), ('项目名称:', 'name'), ('预算金额:', 'budget'),
                  ('开始日期:', 'start'), ('结束日期:', 'end')]
        vars_ = {}
        for lbl, key in labels:
            tk.Label(frame, text=lbl, font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
            v = tk.StringVar(value=date.today().isoformat() if key=='start' else ('0' if key=='budget' else ''))
            vars_[key] = v
            tk.Entry(frame, textvariable=v, font=FONT_TEXT).pack(fill=tk.X, pady=(0,3))
        def do_add():
            try:
                budget = float(vars_['budget'].get() or 0)
            except ValueError:
                messagebox.showerror('错误', '预算必须是数字')
                return
            r = acc.add_project(vars_['code'].get(), vars_['name'].get(), budget,
                                vars_['start'].get(), vars_['end'].get())
            if r.get('success'):
                messagebox.showinfo('成功', '项目已创建')
                win.destroy()
                self._refresh_projects()
            else:
                messagebox.showerror('错误', r.get('error',''))
        tk.Button(frame, text='💾 保存', font=FONT_TEXT, command=do_add,
                  bg=self._c('primary'), fg='white', width=15, pady=3).pack(pady=10)

    def _show_project_pnl(self, event=None):
        sel = self.pj_tree.selection()
        if not sel:
            return
        vals = self.pj_tree.item(sel[0], 'values')
        pid = int(vals[0])
        pnl = acc.get_project_pnl(pid)
        self.pnl_text.config(state=tk.NORMAL)
        self.pnl_text.delete('1.0', tk.END)
        self.pnl_text.insert(tk.END, f"项目: {vals[2]} ({vals[1]})\n")
        self.pnl_text.insert(tk.END, f"{'─'*40}\n")
        self.pnl_text.insert(tk.END, f"收入: {pnl['revenue']:>12,.2f}\n")
        self.pnl_text.insert(tk.END, f"成本: {pnl['cost']:>12,.2f}\n")
        self.pnl_text.insert(tk.END, f"{'─'*40}\n")
        profit = pnl['profit']
        sign = '+' if profit >= 0 else ''
        self.pnl_text.insert(tk.END, f"利润: {sign}{profit:>12,.2f}\n")
        if pnl['revenue'] > 0:
            margin = profit / pnl['revenue'] * 100
            self.pnl_text.insert(tk.END, f"利润率: {margin:>10.1f}%\n")
        self.pnl_text.config(state=tk.DISABLED)
