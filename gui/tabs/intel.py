from __future__ import annotations
"""智能分析标签页 (财务指标, 异常检测, 智能建议, 趋势分析, 财务预测)。"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class IntelTabMixin:
    def _build_intel_tab(self):
        f = self.tabs['intel']

        sub = ttk.Notebook(f)
        sub.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        intel_pages = [
            ('ratio', '  财务指标  '),
            ('anomaly', '  异常检测  '),
            ('suggest', '  智能建议  '),
            ('trend', '  趋势分析  '),
            ('predict', '  财务预测  '),
        ]
        self.intel_frames = {}
        for key, label in intel_pages:
            frame = tk.Frame(sub, bg=self._c('bg'))
            sub.add(frame, text=label)
            self.intel_frames[key] = frame

        self._build_ratio_page()
        self._build_anomaly_page()
        self._build_suggest_page()
        self._build_trend_page()
        self._build_predict_page()

    def _build_ratio_page(self):
        f = self.intel_frames['ratio']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📊 财务指标分析', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Label(top, text='年度:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(20, 2))
        self.ra_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.ra_year,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT)
        tk.Button(top, text='分析', font=FONT_TEXT, command=self._calc_ratios,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        self.ratio_text = tk.Text(f, font=('Consolas', 10), relief=tk.SUNKEN,
                                  bg='#FFF0F5', state=tk.DISABLED)
        self.ratio_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _calc_ratios(self):
        ratios = acc.calc_financial_ratios()
        self.ratio_text.config(state=tk.NORMAL)
        self.ratio_text.delete('1.0', tk.END)
        if not ratios:
            self.ratio_text.insert(tk.END, '⚠️ 数据不足，无法计算财务指标\n')
        else:
            self.ratio_text.insert(tk.END, '📊 财务指标分析\n{"─"*40}\n\n')
            keys_display = [
                ('流动比率', '流动比率', '{:.2f}', '＞1.5 较好'),
                ('速动比率', '速动比率', '{:.2f}', '＞1.0 较好'),
                ('资产负债率', '资产负债率', '{:.2f}%', '40%-60% 合理'),
                ('毛利率', '毛利率', '{:.2f}%', '越高越好'),
                ('净利率', '净利率', '{:.2f}%', '越高越好'),
                ('净资产收益率(ROE)', '净资产收益率(ROE)', '{:.2f}%', '越高越好'),
                ('总资产报酬率(ROA)', '总资产报酬率(ROA)', '{:.2f}%', '越高越好'),
            ]
            for display_name, key, fmt, note in keys_display:
                val = ratios.get(key, 0)
                self.ratio_text.insert(tk.END, f'{display_name:14s}  {fmt.format(val):>10s}    ({note})\n')
        self.ratio_text.config(state=tk.DISABLED)

    def _build_anomaly_page(self):
        f = self.intel_frames['anomaly']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='🔍 异常交易检测', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='阈值(倍):', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(20, 2))
        self.an_thresh = tk.StringVar(value='3.0')
        tk.Spinbox(top, from_=1.0, to=10.0, increment=0.5, textvariable=self.an_thresh,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT)
        tk.Button(top, text='检测', font=FONT_TEXT, command=self._detect_anomalies,
                  bg='#FFB347', fg='white').pack(side=tk.LEFT, padx=10)

        self.an_text = tk.Text(f, font=('Consolas', 10), relief=tk.SUNKEN,
                               bg='#FFF0F5', state=tk.DISABLED)
        self.an_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _detect_anomalies(self):
        results = acc.detect_anomalies()
        self.an_text.config(state=tk.NORMAL)
        self.an_text.delete('1.0', tk.END)
        if not results:
            self.an_text.insert(tk.END, '✅ 未检测到异常交易\n')
        else:
            self.an_text.insert(tk.END, f'⚠️ 发现 {len(results)} 条异常交易\n{"─"*60}\n\n')
            for i, r in enumerate(results[:20], 1):
                detail = r.get("detail", r.get("note", ""))
                self.an_text.insert(tk.END, f'#{i} {r["date"]} | {r["summary"][:20]:20s} | '
                                             f'{r["amount"]:>10,.2f} | {r.get("type","")}\n')
                self.an_text.insert(tk.END, f'   备注: {detail}\n\n')
            if len(results) > 20:
                self.an_text.insert(tk.END, f'... 还有 {len(results)-20} 条\n')
        self.an_text.config(state=tk.DISABLED)

    def _build_suggest_page(self):
        f = self.intel_frames['suggest']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='💡 智能财务建议', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='生成建议', font=FONT_TEXT, command=self._gen_suggestions,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        self.sug_text = tk.Text(f, font=('Consolas', 10), relief=tk.SUNKEN,
                                bg='#FFF0F5', state=tk.DISABLED)
        self.sug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _gen_suggestions(self):
        suggs = acc.get_smart_suggestions()
        self.sug_text.config(state=tk.NORMAL)
        self.sug_text.delete('1.0', tk.END)
        if not suggs:
            self.sug_text.insert(tk.END, '💡 暂无财务建议（数据不足）\n')
        else:
            self.sug_text.insert(tk.END, '💡 智能财务分析与建议\n{"─"*40}\n\n')
            for s in suggs:
                self.sug_text.insert(tk.END, f'  • {s}\n')
            self.sug_text.insert(tk.END, '\n')
        self.sug_text.config(state=tk.DISABLED)

    def _build_trend_page(self):
        f = self.intel_frames['trend']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📈 月度趋势分析', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='年度:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(20, 2))
        self.tr_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.tr_year,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT)
        tk.Button(top, text='分析趋势', font=FONT_TEXT, command=self._show_trend,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=10)

        self.tr_text = tk.Text(f, font=('Consolas', 10), relief=tk.SUNKEN,
                               bg='#FFF0F5', state=tk.DISABLED)
        self.tr_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _show_trend(self):
        trend = acc.get_trend_data(12)
        self.tr_text.config(state=tk.NORMAL)
        self.tr_text.delete('1.0', tk.END)
        if not trend or not trend.get('labels'):
            self.tr_text.insert(tk.END, '⚠️ 数据不足，无法分析趋势\n')
        else:
            self.tr_text.insert(tk.END, '📈 月度收入/支出趋势\n{"─"*55}\n')
            header = f'{"月份":>8s}  {"收入":>10s}  {"支出":>10s}  {"净利润":>10s}'
            self.tr_text.insert(tk.END, header + '\n')
            self.tr_text.insert(tk.END, '─'*55 + '\n')
            labels = trend['labels']
            revenues = trend['revenue']
            expenses = trend['expense']
            profits = trend['profit']
            for i in range(len(labels)):
                arr = '↑' if i > 0 and profits[i] > profits[i-1] else ('↓' if i > 0 else '→')
                self.tr_text.insert(tk.END, f'{labels[i]:>8s}  {revenues[i]:>10,.2f}  '
                                             f'{expenses[i]:>10,.2f}  {profits[i]:>10,.2f}  {arr:>4s}\n')
            self.tr_text.insert(tk.END, '\n')
        self.tr_text.config(state=tk.DISABLED)

    def _build_predict_page(self):
        f = self.intel_frames['predict']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='🔮 财务预测', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='预测月数:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(20, 2))
        self.pr_months = tk.StringVar(value='3')
        tk.Spinbox(top, from_=1, to=12, textvariable=self.pr_months,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT)
        tk.Button(top, text='预测', font=FONT_TEXT, command=self._run_predict,
                  bg='#9C27B0', fg='white').pack(side=tk.LEFT, padx=10)

        self.pr_text = tk.Text(f, font=('Consolas', 10), relief=tk.SUNKEN,
                               bg='#FFF0F5', state=tk.DISABLED)
        self.pr_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _run_predict(self):
        try:
            months = int(self.pr_months.get())
            if months < 1 or months > 12:
                raise ValueError
        except ValueError:
            months = 3
        pred = acc.predict_next_month(months)
        self.pr_text.config(state=tk.NORMAL)
        self.pr_text.delete('1.0', tk.END)
        if not pred:
            self.pr_text.insert(tk.END, '⚠️ 数据不足，无法进行预测（至少需要2个月数据）\n')
        else:
            self.pr_text.insert(tk.END, f'🔮 未来 {months} 个月财务预测\n{"─"*50}\n\n')
            header = f'{"期次":>8s}  {"收入(预测)":>12s}  {"支出(预测)":>12s}  {"净利润":>12s}'
            self.pr_text.insert(tk.END, header + '\n')
            self.pr_text.insert(tk.END, '─'*50 + '\n')
            for row in pred:
                self.pr_text.insert(tk.END, f'{row["period"]:>8s}  {row["predicted_revenue"]:>12,.2f}  '
                                             f'{row["predicted_expense"]:>12,.2f}  '
                                             f'{row["predicted_profit"]:>12,.2f}\n')
        self.pr_text.config(state=tk.DISABLED)
