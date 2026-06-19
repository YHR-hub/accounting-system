from __future__ import annotations
"""审计日志标签页。"""
import tkinter as tk
from tkinter import ttk
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class AuditTabMixin:
    def _build_audit_tab(self):
        f = self.tabs['audit']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📋 审计日志', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='筛选:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15,2))
        self.audit_type = tk.StringVar(value='')
        ttypes = ['', 'voucher', 'user', 'database', 'system', 'attachment', 'payroll']
        tnames = ['全部', '凭证', '用户', '数据库', '系统', '附件', '薪资']
        self.audit_type_cb = ttk.Combobox(top, textvariable=self.audit_type, values=ttypes,
                                           font=FONT_TEXT, width=12, state='readonly')
        self.audit_type_cb.bind('<<ComboboxSelected>>', lambda e: self._refresh_audit())
        self.audit_type_cb.pack(side=tk.LEFT, padx=2)
        self._audit_type_map = dict(zip(ttypes, tnames))
        tk.Label(top, text='条数:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10,2))
        self.audit_limit = tk.StringVar(value='200')
        tk.Spinbox(top, from_=50, to=1000, increment=50, textvariable=self.audit_limit,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_audit,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        cols = ('id', 'time', 'user', 'action', 'target_type', 'target_id', 'detail')
        self.audit_tree = ttk.Treeview(f, columns=cols, show='headings', height=22)
        self.audit_tree.heading('id', text='ID')
        self.audit_tree.heading('time', text='时间')
        self.audit_tree.heading('user', text='用户')
        self.audit_tree.heading('action', text='操作')
        self.audit_tree.heading('target_type', text='对象类型')
        self.audit_tree.heading('target_id', text='对象ID')
        self.audit_tree.heading('detail', text='详情')
        self.audit_tree.column('id', width=40, anchor='center')
        self.audit_tree.column('time', width=150, anchor='center')
        self.audit_tree.column('user', width=80, anchor='center')
        self.audit_tree.column('action', width=80, anchor='center')
        self.audit_tree.column('target_type', width=80, anchor='center')
        self.audit_tree.column('target_id', width=60, anchor='center')
        self.audit_tree.column('detail', width=350)
        self.audit_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.audit_tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.audit_tree.configure(yscrollcommand=sb.set)
        self._refresh_audit()

    def _refresh_audit(self):
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
        try:
            limit = int(self.audit_limit.get())
        except ValueError:
            limit = 200
        tt = self.audit_type.get()
        rows = acc.get_audit_logs(limit=limit, target_type=tt)
        for r in rows:
            tname = self._audit_type_map.get(r['target_type'], r['target_type'])
            self.audit_tree.insert('', tk.END, values=(
                r['id'], r['created_at'], r['username'], r['action'],
                tname, r['target_id'], r['detail'],
            ))
