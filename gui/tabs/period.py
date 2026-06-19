from __future__ import annotations
"""期末处理标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class PeriodTabMixin:
    def _build_period_tab(self):
        f = self.tabs['period']
        acc.ensure_period_table()

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=10)

        tk.Label(top, text='📅 会计年度:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=5)
        self.per_year_var = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.per_year_var,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(top, text='月份:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=2)
        self.per_month_var = tk.StringVar(value=str(date.today().month))
        tk.Spinbox(top, from_=1, to=12, textvariable=self.per_month_var,
                   font=FONT_TEXT, width=6).pack(side=tk.LEFT, padx=2)

        btn_frame = tk.Frame(f, bg=self._c('bg'))
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text='🔍 检查期间', font=FONT_TEXT, width=14,
                  command=self._check_period, bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='🔒 期末关账', font=FONT_TEXT, width=14,
                  command=self._close_period, bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='🔄 一键自动结转', font=FONT_TEXT, width=16,
                  command=self._auto_close_period, bg='#FFB347', fg='white').pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='📋 结转日志', font=FONT_TEXT, width=14,
                  command=self._show_close_log, bg='#E8D5F5').pack(side=tk.LEFT, padx=3)

        self.per_status = tk.Text(f, font=FONT_TEXT, height=12, relief=tk.SUNKEN, bg='#FFF0F5')
        self.per_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        h_bar = tk.Frame(f, bg=self._c('bg'))
        h_bar.pack(fill=tk.X, padx=10)
        self.per_progress = ttk.Progressbar(h_bar, mode='indeterminate', length=300)
        self.per_progress.pack(side=tk.LEFT, pady=5)
        tk.Label(h_bar, text='自动结转: 生成损益结转凭证 + 计提折旧 + 期末关账', font=FONT_SMALL,
                 bg=self._c('bg'), fg='gray').pack(side=tk.LEFT, padx=10)

    def _check_period(self):
        year = int(self.per_year_var.get())
        month = int(self.per_month_var.get())
        status = acc.get_period_status(year, month)
        self.per_status.delete('1.0', tk.END)
        if status['closed']:
            self.per_status.insert(tk.END, f'期间 {year}年{month:02d}月 状态: ✅ 已关账\n')
            self.per_status.insert(tk.END, f'关账时间: {status["close_time"]}\n')
        else:
            self.per_status.insert(tk.END, f'期间 {year}年{month:02d}月 状态: ⏸ 未关账\n')

    def _close_period(self):
        year = int(self.per_year_var.get())
        month = int(self.per_month_var.get())
        ok = acc.close_period(year, month)
        if ok:
            self.per_status.delete('1.0', tk.END)
            self.per_status.insert(tk.END, f'✅ 期间 {year}年{month:02d}月 关账成功\n')
            messagebox.showinfo('成功', '关账成功')
        else:
            messagebox.showerror('错误', '关账失败，请检查日志')

    def _auto_close_period(self):
        year = int(self.per_year_var.get())
        month = int(self.per_month_var.get())

        if not messagebox.askyesno('确认', f'一键自动结转:\n  1. 计提折旧\n  2. 生成损益结转凭证\n  3. 关账\n\n确认处理 {year}年{month:02d}月?'):
            return

        self.per_progress.start()
        self.root.update()
        self.per_status.delete('1.0', tk.END)
        self.per_status.insert(tk.END, '🔄 开始自动结转...\n')
        self.root.update()

        self.per_status.insert(tk.END, '步骤1/3: 计提折旧...\n')
        self.root.update()
        depr_count = acc.run_depreciation(year, month)
        self.per_status.insert(tk.END, f'  → 折旧凭证 {depr_count} 条\n')
        self.root.update()

        self.per_status.insert(tk.END, '步骤2/3: 结转损益...\n')
        self.root.update()
        result = acc.auto_close_period(year, month)
        if 'income_total' in result:
            vs = ', '.join(result.get('vouchers', []))
            self.per_status.insert(tk.END, f'  ✅ 结转成功，凭证: {vs}\n')
            self.per_status.insert(tk.END, f'     收入: {result["income_total"]:.2f}, '
                                             f'费用: {result["expense_total"]:.2f}, '
                                             f'利润: {result["profit"]:.2f}\n')
        else:
            self.per_status.insert(tk.END, f'  ⚠️ 结转完成（无可结转项目）\n')
        self.root.update()

        self.per_status.insert(tk.END, '步骤3/3: 期末关账...\n')
        self.root.update()
        if acc.close_period(year, month):
            self.per_status.insert(tk.END, f'\n🎉 {year}年{month:02d}月 自动结转完成！\n')
        else:
            self.per_status.insert(tk.END, '  ❌ 关账失败\n')

        self.per_progress.stop()

    def _show_close_log(self):
        log = acc.get_close_log(limit=20)
        self.per_status.delete('1.0', tk.END)
        if not log:
            self.per_status.insert(tk.END, '暂无结转日志\n')
            return
        self.per_status.insert(tk.END, '📋 近期结转日志:\n\n')
        for l in log:
            icon = '✅' if l['status'] == 'success' else '❌'
            self.per_status.insert(tk.END, f'{icon} {l["time"]} | {l["period"]} | {l["action"]}\n')
