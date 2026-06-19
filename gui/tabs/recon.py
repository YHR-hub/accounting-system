from __future__ import annotations
"""银企对账标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class ReconTabMixin:
    def _build_recon_tab(self):
        f = self.tabs['recon']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='🏦 银企对账', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='📥 导入银行流水', font=FONT_TEXT, command=self._import_bank_stmt,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🤖 自动对账', font=FONT_TEXT, command=self._auto_reconcile,
                  bg=self._c('accent'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_recon,
                  bg=self._c('bg'), fg=self._c('accent')).pack(side=tk.LEFT, padx=5)

        self.recon_status = tk.Label(f, text='', font=FONT_TEXT, bg=self._c('bg'), fg=self._c('accent'))
        self.recon_status.pack(anchor='w', padx=15, pady=2)

        cols = ('id', 'date', 'desc', 'amount', 'balance', 'ref', 'matched', 'voucher')
        self.recon_tree = ttk.Treeview(f, columns=cols, show='headings', height=20)
        self.recon_tree.heading('id', text='ID')
        self.recon_tree.heading('date', text='日期')
        self.recon_tree.heading('desc', text='摘要')
        self.recon_tree.heading('amount', text='金额')
        self.recon_tree.heading('balance', text='余额')
        self.recon_tree.heading('ref', text='参考号')
        self.recon_tree.heading('matched', text='已对账')
        self.recon_tree.heading('voucher', text='凭证号')
        self.recon_tree.column('id', width=40, anchor='center')
        self.recon_tree.column('date', width=100, anchor='center')
        self.recon_tree.column('desc', width=250)
        self.recon_tree.column('amount', width=110, anchor='e')
        self.recon_tree.column('balance', width=110, anchor='e')
        self.recon_tree.column('ref', width=100, anchor='center')
        self.recon_tree.column('matched', width=60, anchor='center')
        self.recon_tree.column('voucher', width=100, anchor='center')
        self.recon_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_recon()

    def _refresh_recon(self):
        for item in self.recon_tree.get_children():
            self.recon_tree.delete(item)
        status = acc.get_reconciliation_status()
        self.recon_status.config(text=f"📊 银行流水: {status['total']} 条  |  已对账: {status['reconciled']}  |  未对账: {status['pending']}")
        rows = acc.get_balance_sheet()
        for r in rows:
            matched = '✅' if r.get('voucher_id') else '❌'
            vno = r.get('voucher_no', '')
            self.recon_tree.insert('', tk.END, values=(
                r['id'], r['transaction_date'], r['description'],
                f"{r['amount']:,.2f}", f"{r.get('balance',0):,.2f}",
                r.get('ref_no',''), matched, vno,
            ))

    def _import_bank_stmt(self):
        fname = filedialog.askopenfilename(title='选择银行流水文件', filetypes=[('CSV','*.csv'),('所有文件','*.*')])
        if not fname:
            return
        try:
            items = []
            with open(fname, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    items.append({
                        'transaction_date': row.get('date','') or row.get('日期',''),
                        'description': row.get('description','') or row.get('摘要',''),
                        'amount': float(row.get('amount',0) or row.get('金额',0)),
                        'balance': float(row.get('balance',0) or row.get('余额',0)),
                        'ref_no': row.get('ref_no','') or row.get('参考号',''),
                    })
            if not items:
                messagebox.showwarning('提示', '未读取到有效数据，请检查CSV格式')
                return
            result = acc.import_bank_statement(items)
            messagebox.showinfo('导入完成', f'成功导入 {result["imported"]} 条记录')
            self._refresh_recon()
        except Exception as e:
            messagebox.showerror('导入失败', str(e))

    def _auto_reconcile(self):
        result = acc.auto_reconcile()
        messagebox.showinfo('对账完成', f'自动匹配 {result["matched"]} 条记录\n未匹配: {result["total"] - result["matched"]} 条')
        self._refresh_recon()
