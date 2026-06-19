from __future__ import annotations
"""财务预警系统标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class AlertsTabMixin:
    def _build_alerts_tab(self):
        f = self.tabs['alerts']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='🔔 财务预警系统', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_alerts,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='✅ 检查预警', font=FONT_TEXT, command=self._check_alerts_now,
                  bg=self._c('warn'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='➕ 添加规则', font=FONT_TEXT, command=self._add_alert_rule_dialog,
                  bg=self._c('accent'), fg='white').pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.VERTICAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        rtop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(rtop, height=150)
        tk.Label(rtop, text='📏 预警规则', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        cols = ('id', 'name', 'indicator', 'op', 'threshold', 'level', 'enabled')
        self.ar_tree = ttk.Treeview(rtop, columns=cols, show='headings', height=6)
        self.ar_tree.heading('id', text='ID')
        self.ar_tree.heading('name', text='规则名称')
        self.ar_tree.heading('indicator', text='指标')
        self.ar_tree.heading('op', text='条件')
        self.ar_tree.heading('threshold', text='阈值')
        self.ar_tree.heading('level', text='级别')
        self.ar_tree.heading('enabled', text='启用')
        self.ar_tree.column('id', width=40, anchor='center')
        self.ar_tree.column('name', width=130)
        self.ar_tree.column('indicator', width=120, anchor='center')
        self.ar_tree.column('op', width=60, anchor='center')
        self.ar_tree.column('threshold', width=80, anchor='center')
        self.ar_tree.column('level', width=60, anchor='center')
        self.ar_tree.column('enabled', width=50, anchor='center')
        self.ar_tree.pack(fill=tk.BOTH, expand=True)
        op_map = {'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<=', 'eq': '='}
        ind_map = {'current_ratio':'流动比率','quick_ratio':'速动比率','debt_ratio':'资产负债率','net_profit_margin':'净利润率','gross_margin':'毛利率','roe':'ROE','roa':'ROA','inventory_turnover':'存货周转率','receivable_turnover':'应收周转率'}
        self._alert_op_map = op_map
        self._alert_ind_map = ind_map

        htop = tk.Frame(panes, bg=self._c('bg'))
        panes.add(htop)
        row1 = tk.Frame(htop, bg=self._c('bg'))
        row1.pack(fill=tk.X)
        tk.Label(row1, text='📜 预警历史', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT)
        self.alert_unresolved = tk.BooleanVar(value=False)
        tk.Checkbutton(row1, text='仅未解决', variable=self.alert_unresolved,
                       font=FONT_TEXT, bg=self._c('bg'), command=self._refresh_alert_history).pack(side=tk.LEFT, padx=10)
        tk.Button(row1, text='✅ 标记已解决', font=FONT_TEXT, command=self._resolve_alert,
                  bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=5)
        cols2 = ('id', 'time', 'rule', 'message', 'level', 'resolved')
        self.ah_tree = ttk.Treeview(htop, columns=cols2, show='headings', height=8)
        self.ah_tree.heading('id', text='ID')
        self.ah_tree.heading('time', text='时间')
        self.ah_tree.heading('rule', text='规则')
        self.ah_tree.heading('message', text='消息')
        self.ah_tree.heading('level', text='级别')
        self.ah_tree.heading('resolved', text='已解决')
        for c in cols2:
            w = 40 if c in ('id','resolved') else 60 if c=='level' else 120 if c=='rule' else 250 if c=='message' else 140
            self.ah_tree.column(c, width=w, anchor='center' if c in ('id','level','resolved') else 'w')
        self.ah_tree.pack(fill=tk.BOTH, expand=True)
        self._refresh_alerts()

    def _refresh_alerts(self):
        for item in self.ar_tree.get_children():
            self.ar_tree.delete(item)
        rules = acc.get_alert_rules()
        for r in rules:
            op = self._alert_op_map.get(r['operator'], r['operator'])
            ind = self._alert_ind_map.get(r['indicator'], r['indicator'])
            level_cn = {'warning':'⚠️警告','critical':'🚨严重'}.get(r['level'], r['level'])
            enabled = '✅' if r['enabled'] else '❌'
            self.ar_tree.insert('', tk.END, values=(
                r['id'], r['name'], ind, op, r['threshold'], level_cn, enabled,
            ))
        self._refresh_alert_history()

    def _refresh_alert_history(self):
        for item in self.ah_tree.get_children():
            self.ah_tree.delete(item)
        rows = acc.get_alert_history(unresolved_only=self.alert_unresolved.get())
        for r in rows:
            resolved = '✅' if r['resolved'] else '❌'
            lvl = {'warning':'⚠️','critical':'🚨'}.get(r['level'], r['level'])
            self.ah_tree.insert('', tk.END, values=(
                r['id'], r['created_at'], r['rule_name'], r['message'], lvl, resolved,
            ))

    def _check_alerts_now(self):
        results = acc.check_alerts()
        n = len(results)
        if n == 0:
            messagebox.showinfo('检查完成', '✅ 所有指标正常，未触发预警')
        else:
            msg = '\n'.join(f"{r['level']}: {r['message']}" for r in results)
            messagebox.showwarning('预警触发', f'共 {n} 条预警\n\n{msg}')
        self._refresh_alerts()

    def _resolve_alert(self):
        sel = self.ah_tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请选择要解决的预警')
            return
        for item in sel:
            vals = self.ah_tree.item(item, 'values')
            acc.resolve_alert(int(vals[0]))
        self._refresh_alert_history()

    def _add_alert_rule_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('添加预警规则')
        win.geometry('450x350')
        win.resizable(False, False)
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text='➕ 添加预警规则', font=FONT_SUB, bg=self._c('bg')).pack(pady=(0,10))

        tk.Label(frame, text='规则名称:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        name_var = tk.StringVar()
        tk.Entry(frame, textvariable=name_var, font=FONT_TEXT).pack(fill=tk.X, pady=(0,5))

        tk.Label(frame, text='指标:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        ind_var = tk.StringVar()
        inds = list(self._alert_ind_map.values())
        ind_cb = ttk.Combobox(frame, textvariable=ind_var, values=inds, font=FONT_TEXT, state='readonly', width=40)
        ind_cb.pack(fill=tk.X, pady=(0,5))
        ind_rev = {v: k for k, v in self._alert_ind_map.items()}

        row = tk.Frame(frame, bg=self._c('bg'))
        row.pack(fill=tk.X)
        tk.Label(row, text='条件:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT)
        op_var = tk.StringVar(value='lt')
        ops = [('小于 lt', 'lt'), ('大于 gt', 'gt'), ('小于等于 lte', 'lte'), ('大于等于 gte', 'gte'), ('等于 eq', 'eq')]
        op_cb = ttk.Combobox(row, textvariable=op_var, values=[o[0] for o in ops], font=FONT_TEXT, state='readonly', width=15)
        op_cb.pack(side=tk.LEFT, padx=5)
        tk.Label(row, text='阈值:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10,2))
        th_var = tk.StringVar(value='0')
        tk.Entry(row, textvariable=th_var, font=FONT_TEXT, width=10).pack(side=tk.LEFT)

        tk.Label(frame, text='级别:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(5,2))
        lv_var = tk.StringVar(value='warning')
        lv_frame = tk.Frame(frame, bg=self._c('bg'))
        lv_frame.pack(fill=tk.X)
        tk.Radiobutton(lv_frame, text='⚠️ 警告', variable=lv_var, value='warning', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT)
        tk.Radiobutton(lv_frame, text='🚨 严重', variable=lv_var, value='critical', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=20)

        def do_add():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning('提示', '请输入规则名称')
                return
            ind_key = ind_rev.get(ind_var.get(), 'current_ratio')
            op_raw = op_var.get().split()[-1]
            try:
                th = float(th_var.get())
            except ValueError:
                messagebox.showerror('错误', '阈值必须是数字')
                return
            r = acc.add_alert_rule(name, ind_key, op_raw, th, lv_var.get())
            if r.get('success'):
                messagebox.showinfo('成功', '规则已添加')
                win.destroy()
                self._refresh_alerts()
            else:
                messagebox.showerror('错误', r.get('error',''))

        tk.Button(frame, text='💾 保存', font=FONT_TEXT, command=do_add,
                  bg=self._c('primary'), fg='white', width=15, pady=3).pack(pady=10)
