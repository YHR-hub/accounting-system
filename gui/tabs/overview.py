from __future__ import annotations
"""概览（首页）标签页：KPI 大数字 + 关键财务比率 + 报表导出。"""
import tkinter as tk
from tkinter import messagebox

import accsys as acc
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL

try:
    import matplotlib
    matplotlib.use("TkAgg")
except Exception:
    matplotlib = None


class OverviewTabMixin:
    def _build_overview_tab(self):
        f = self.tabs['overview']
        f.configure(bg=self._c('bg'))

        tk.Label(f, text='📊 财务概览', font=FONT_SUB, bg=self._c('bg'),
                 fg=self._c('violet')).pack(anchor='w', padx=18, pady=(16, 10))

        # —— 计算指标（复用 accsys 稳定函数）——
        try:
            accts = acc.load_accounts_from_db()
            bal = acc.calc_balances(accts)

            def _sum(cat):
                return sum(float(bal.get(a['code'], 0)) for a in accts if a['category'] == cat)

            assets = _sum('asset')
            liab = _sum('liability')
            income = _sum('income')
            expense = _sum('expense')
            net = income - expense
            equity = assets - liab
            ratios = acc.calc_financial_ratios()
            conn = acc.get_conn()
            vcount = conn.execute('SELECT COUNT(*) FROM vouchers').fetchone()[0]
            conn.close()
        except Exception:
            assets = liab = equity = net = 0.0
            ratios = {}
            vcount = 0

        # —— KPI 卡片 ——
        cards = tk.Frame(f, bg=self._c('bg'))
        cards.pack(fill=tk.X, padx=18)
        kpis = [
            ('总资产', f'{assets:,.0f}', self._c('primary')),
            ('总负债', f'{liab:,.0f}', '#D63031'),
            ('净资产', f'{equity:,.0f}', '#00B894'),
            ('净利润', f'{net:,.0f}', self._c('accent')),
            ('凭证数', f'{vcount}', self._c('violet')),
        ]
        for i, (label, val, color) in enumerate(kpis):
            cards.columnconfigure(i, weight=1)
            card = tk.Frame(cards, bg=self._c('text_bg'), padx=18, pady=14,
                            highlightbackground='#E3E5F0', highlightthickness=1)
            card.grid(row=0, column=i, padx=6, sticky='nsew')
            tk.Label(card, text=label, font=FONT_SMALL, bg=self._c('text_bg'),
                     fg='#8A8A99').pack(anchor='w')
            tk.Label(card, text=val, font=('微软雅黑', 19, 'bold'),
                     bg=self._c('text_bg'), fg=color).pack(anchor='w', pady=(4, 0))

        # —— 关键财务比率 ——
        rframe = tk.LabelFrame(f, text='  关键财务比率  ', font=FONT_TEXT,
                               bg=self._c('bg'), fg=self._c('fg'), padx=14, pady=12)
        rframe.pack(fill=tk.X, padx=18, pady=16)
        for i, k in enumerate(['流动比率', '速动比率', '资产负债率', '毛利率', '净利率']):
            v = ratios.get(k, 0)
            cell = tk.Frame(rframe, bg=self._c('bg'))
            cell.grid(row=0, column=i, padx=18)
            tk.Label(cell, text=k, font=FONT_SMALL, bg=self._c('bg'), fg='#8A8A99').pack()
            tk.Label(cell, text=f'{v}', font=FONT_SUB, bg=self._c('bg'),
                     fg=self._c('violet')).pack(pady=(2, 0))

        # —— 导出 ——
        tk.Button(f, text='📥 导出报表 Excel', font=FONT_TEXT, bg=self._c('primary'),
                  fg='white', command=self._overview_export).pack(anchor='w', padx=18, pady=(0, 14))
        tk.Label(f, text='提示：左侧标签页可查看凭证、报表、库存、薪资、项目等全部功能。',
                 font=FONT_SMALL, bg=self._c('bg'), fg='#9AA0B5').pack(anchor='w', padx=18)

        # —— 嵌入收支柱状图（失败则跳过，不影响首页）——
        try:
            from datetime import date
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            chart_box = tk.Frame(f, bg='white', highlightbackground='#E3E5F0', highlightthickness=1)
            chart_box.pack(fill=tk.BOTH, expand=True, padx=18, pady=(8, 14))
            fig = acc.chart_income_expense(date.today().year)
            canvas = FigureCanvasTkAgg(fig, master=chart_box)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception:
            pass

    def _overview_export(self):
        try:
            acc.export_excel()
            messagebox.showinfo('导出成功', f'报表已导出到:\n{acc.get_excel_path()}')
        except Exception as e:
            messagebox.showerror('导出失败', str(e))
