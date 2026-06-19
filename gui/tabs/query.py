from __future__ import annotations
"""凭证查询标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import io, sys
from gui.constants import FONT_TEXT
import accsys as acc

class QueryTabMixin:
    def _build_query_tab(self):
        f = self.tabs['query']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=8)
        tk.Label(top, text='年份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.q_year = tk.Entry(top, font=FONT_TEXT, width=8)
        self.q_year.pack(side=tk.LEFT, padx=2)
        tk.Label(top, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.q_month = tk.Entry(top, font=FONT_TEXT, width=6)
        self.q_month.pack(side=tk.LEFT, padx=2)
        tk.Button(top, text='查询', font=FONT_TEXT, command=self._refresh_voucher_list,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='查看详情', font=FONT_TEXT, command=self._show_voucher_detail,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        tk.Button(top, text='📤 导出CSV', font=FONT_TEXT, command=lambda: self._batch_export('csv'),
                  bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=2)
        tk.Button(top, text='📤 导出Excel', font=FONT_TEXT, command=lambda: self._batch_export('xlsx'),
                  bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=2)
        tk.Button(top, text='📤 导出PDF', font=FONT_TEXT, command=lambda: self._batch_export('pdf'),
                  bg='#26A69A', fg='white').pack(side=tk.LEFT, padx=2)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        tk.Button(top, text='📥 导入凭证', font=FONT_TEXT, command=self._import_vouchers,
                  bg='#FF8A65', fg='white').pack(side=tk.LEFT, padx=2)

        cols = ('no', 'date', 'summary', 'count')
        self.q_tree = ttk.Treeview(f, columns=cols, show='headings', height=18)
        self.q_tree.heading('no', text='凭证号')
        self.q_tree.heading('date', text='日期')
        self.q_tree.heading('summary', text='摘要')
        self.q_tree.heading('count', text='分录数')
        self.q_tree.column('no', width=180)
        self.q_tree.column('date', width=110)
        self.q_tree.column('summary', width=300)
        self.q_tree.column('count', width=70)
        self.q_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.q_tree.bind('<Double-1>', lambda e: self._show_voucher_detail())

        self.q_detail = tk.Text(f, font=('Consolas', 10), height=10, state=tk.DISABLED, bg='#FFF0F5')
        self.q_detail.pack(fill=tk.BOTH, padx=5, pady=5)

        self._refresh_voucher_list()

    def _refresh_voucher_list(self):
        for item in self.q_tree.get_children():
            self.q_tree.delete(item)
        self.q_detail.config(state=tk.NORMAL)
        self.q_detail.delete('1.0', tk.END)
        self.q_detail.config(state=tk.DISABLED)

        y = self.q_year.get().strip()
        m = self.q_month.get().strip()
        conn = acc.get_conn()
        query = 'SELECT * FROM vouchers'
        params = []
        conds = []
        if y:
            conds.append('fiscal_year=?')
            params.append(int(y))
        if m:
            conds.append('fiscal_month=?')
            params.append(int(m))
        if conds:
            query += ' WHERE ' + ' AND '.join(conds)
        query += ' ORDER BY voucher_no DESC LIMIT 100'
        rows = conn.execute(query, params).fetchall()
        conn.close()

        for r in rows:
            conn2 = acc.get_conn()
            cnt = conn2.execute(
                'SELECT COUNT(*) as c FROM journal_entries WHERE voucher_id=?', (r['id'],)).fetchone()['c']
            conn2.close()
            self.q_tree.insert('', tk.END, iid=str(r['id']),
                               values=(r['voucher_no'], r['date'], r['summary'], cnt))

    def _show_voucher_detail(self):
        selected = self.q_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择一张凭证')
            return
        vid = int(selected[0])
        conn = acc.get_conn()
        self.q_detail.config(state=tk.NORMAL)
        self.q_detail.delete('1.0', tk.END)

        old = sys.stdout
        sys.stdout = buf = io.StringIO()
        acc.show_voucher(vid, conn)
        sys.stdout = old
        self.q_detail.insert(tk.END, buf.getvalue())
        self.q_detail.config(state=tk.DISABLED)
        conn.close()

    def _batch_export(self, fmt):
        y = self.q_year.get().strip()
        m = self.q_month.get().strip()
        fname = f'凭证导出_{y}_{m}.{fmt}' if y else f'凭证导出_all.{fmt}'
        path = filedialog.asksaveasfilename(defaultextension=f'.{fmt}', initialfile=fname,
                                            filetypes=[(fmt.upper(), f'*.{fmt}')])
        if not path:
            return
        result = acc.batch_export_vouchers(path, fmt=fmt, year=y, month=m)
        if 'error' in result:
            messagebox.showerror('错误', result['error'])
        else:
            messagebox.showinfo('成功', result.get('message', f'已导出到 {path}'))

    def _import_vouchers(self):
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv'), ('Excel', '*.xlsx')])
        if not path:
            return
        result = acc.import_vouchers(path)
        if 'error' in result:
            messagebox.showerror('错误', result['error'])
        else:
            count = result.get('count', 0)
            messagebox.showinfo('成功', f'已导入 {count} 张凭证')
            self._refresh_voucher_list()
