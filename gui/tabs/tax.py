from __future__ import annotations
"""税务计算标签页。"""
import tkinter as tk
from tkinter import messagebox
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class TaxTabMixin:
    def _build_tax_tab(self):
        f = self.tabs['tax']
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        vat_f = tk.LabelFrame(f, text='增值税计算', font=FONT_SUB, bg=self._c('bg'), padx=10, pady=10)
        vat_f.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        tk.Label(vat_f, text='纳税人类型 / 适用税率:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        self.vat_type = tk.StringVar(value='0.13')
        for v, label in [
            ('0.13', '一般纳税人 13% — 销售货物 / 加工修理修配 / 有形动产租赁 / 进口货物'),
            ('0.09', '一般纳税人 9% — 交通运输 / 邮政 / 建筑 / 不动产租赁销售 / 农产品'),
            ('0.06', '一般纳税人 6% — 现代服务 / 金融服务 / 生活服务 / 销售无形资产'),
            ('0.03', '小规模纳税人 3% — 标准征收率'),
            ('0.01', '小规模纳税人 1% — 现行优惠征收率'),
        ]:
            tk.Radiobutton(vat_f, text=label, variable=self.vat_type, value=v,
                           font=FONT_SMALL, bg=self._c('bg'), anchor='w', justify='left').pack(anchor='w', fill='x')

        tk.Label(vat_f, text='含税销售额:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10, 2))
        self.vat_revenue = tk.Entry(vat_f, font=FONT_TEXT, width=24)
        self.vat_revenue.pack(anchor='w')

        tk.Button(vat_f, text='计算增值税', font=FONT_TEXT, command=self._calc_vat_gui,
                  bg=self._c('primary'), fg='white').pack(pady=10, anchor='w')
        self.vat_result = tk.Text(vat_f, font=('Consolas', 11), height=6, width=40, state=tk.DISABLED, bg='#FFF0F5')
        self.vat_result.pack(fill=tk.BOTH, expand=True)

        pit_f = tk.LabelFrame(f, text='个人所得税计算', font=FONT_SUB, bg=self._c('bg'), padx=10, pady=10)
        pit_f.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

        tk.Label(pit_f, text='月应纳税所得额:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        tk.Label(pit_f, text='(税前收入 - 五险一金 - 5000)', font=FONT_SMALL, bg=self._c('bg'), fg='gray').pack(anchor='w')
        self.pit_income = tk.Entry(pit_f, font=FONT_TEXT, width=24)
        self.pit_income.pack(anchor='w', pady=5)

        tk.Button(pit_f, text='计算个人所得税', font=FONT_TEXT, command=self._calc_pit_gui,
                  bg=self._c('primary'), fg='white').pack(pady=10, anchor='w')
        self.pit_result = tk.Text(pit_f, font=('Consolas', 11), height=6, width=40, state=tk.DISABLED, bg='#FFF0F5')
        self.pit_result.pack(fill=tk.BOTH, expand=True)

    def _calc_vat_gui(self):
        try:
            rate = float(self.vat_type.get())
            rev = float(self.vat_revenue.get().strip())
            if rev <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('错误', '请输入有效的销售额')
            return

        r = acc.compute_vat(rev, rate)
        result = (
            f'增值税计算明细\n'
            f'{"─"*36}\n'
            f'税率:              {r["rate"]*100:.0f}%\n'
            f'含税销售额:        {r["revenue"]:>12.2f}\n'
            f'不含税销售额:      {r["tax_exclusive"]:>12.2f}\n'
            f'增值税额:          {r["tax_amount"]:>12.2f}\n'
            f'{"─"*36}'
        )
        self.vat_result.config(state=tk.NORMAL)
        self.vat_result.delete('1.0', tk.END)
        self.vat_result.insert(tk.END, result)
        self.vat_result.config(state=tk.DISABLED)

    def _calc_pit_gui(self):
        try:
            income = float(self.pit_income.get().strip())
        except ValueError:
            messagebox.showerror('错误', '请输入有效金额')
            return
        if income <= 0:
            messagebox.showinfo('提示', '应纳税所得额 ≤ 0，无需缴税')
            return

        r = acc.compute_pit(income)
        result = f'个人所得税计算明细\n{"─"*48}\n应纳税所得额: {r["income"]:>12.2f}\n{"─"*48}\n'
        result += f'{"级距":<18} {"税率":<8} {"应纳税额":<12} {"税款":<10}\n'
        for b in r['brackets']:
            if b['taxable'] > 0:
                level = (f'{int(b["lower"]):,}-{int(b["upper"]):,}'
                         if b['upper'] != float('inf') else f'{int(b["lower"]):,}以上')
                result += f'  {level:<16} {b["rate"]*100:.0f}%{"":<4} {b["taxable"]:>8.2f}  {b["tax"]:>8.2f}\n'
        result += f'{"─"*48}\n'
        result += f'应缴个人所得税:                   {r["total_tax"]:>8.2f}\n'
        result += f'税后收入:                         {r["after_tax"]:>8.2f}\n'
        result += f'{"─"*48}'

        self.pit_result.config(state=tk.NORMAL)
        self.pit_result.delete('1.0', tk.END)
        self.pit_result.insert(tk.END, result)
        self.pit_result.config(state=tk.DISABLED)
