from __future__ import annotations
"""多币种汇率管理标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class CurrencyTabMixin:
    def _build_currency_tab(self):
        f = self.tabs['currency']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=10)
        tk.Button(top, text='🌐 在线更新汇率', font=FONT_TEXT, command=self._update_rates,
                  bg=self._c('primary'), fg='white', width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='✏️ 手动输入汇率', font=FONT_TEXT, command=self._manual_rate,
                  bg='#C084FC', fg='white', width=16).pack(side=tk.LEFT, padx=5)

        cols = ('currency', 'date', 'rate')
        self.c_tree = ttk.Treeview(f, columns=cols, show='headings', height=10)
        self.c_tree.heading('currency', text='币种')
        self.c_tree.heading('date', text='日期')
        self.c_tree.heading('rate', text='汇率 (1 CNY = ?)')
        self.c_tree.column('currency', width=100)
        self.c_tree.column('date', width=120)
        self.c_tree.column('rate', width=200)
        self.c_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._refresh_rates()

    def _refresh_rates(self):
        for item in self.c_tree.get_children():
            self.c_tree.delete(item)
        conn = acc.get_conn()
        rows = conn.execute(
            'SELECT currency, date, rate FROM exchange_rates ORDER BY currency, date DESC').fetchall()
        conn.close()
        seen = set()
        for r in rows:
            if r['currency'] not in seen:
                seen.add(r['currency'])
                self.c_tree.insert('', tk.END, values=(r['currency'], r['date'], f"{r['rate']:.6f}"))

    def _update_rates(self):
        self.c_tree.delete(*self.c_tree.get_children())
        self.c_tree.insert('', tk.END, values=('...', '获取中', '...'))
        self.root.update()
        rates = acc.fetch_exchange_rates()
        if rates:
            today = date.today().isoformat()
            conn = acc.get_conn()
            for cur, rate in rates.items():
                conn.execute('INSERT OR REPLACE INTO exchange_rates (currency, date, rate) VALUES (?,?,?)',
                             (cur, today, rate))
            conn.commit()
            conn.close()
            messagebox.showinfo('成功', f'已更新 {len(rates)} 种币种汇率')
            self._refresh_rates()
        else:
            self._refresh_rates()
            messagebox.showwarning('提示', '获取在线汇率失败，请手动输入')

    def _manual_rate(self):
        cur = simpledialog.askstring('手动输入', '币种代码 (如 USD):').strip()
        if not cur:
            return
        cur = cur.upper()
        rate_str = simpledialog.askstring('手动输入', f'1 CNY = ? {cur}:')
        if not rate_str:
            return
        try:
            rate = float(rate_str)
            if rate <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('错误', '无效汇率')
            return
        conn = acc.get_conn()
        conn.execute('INSERT OR REPLACE INTO exchange_rates (currency, date, rate) VALUES (?,?,?)',
                     (cur, date.today().isoformat(), rate))
        conn.commit()
        conn.close()
        messagebox.showinfo('成功', f'汇率已保存: 1 CNY = {rate:.4f} {cur}')
        self._refresh_rates()
