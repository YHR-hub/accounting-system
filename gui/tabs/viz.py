from __future__ import annotations
"""数据可视化标签页 (Matplotlib Charts)。"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

class VizTabMixin:
    def _build_viz_tab(self):
        f = self.tabs['viz']
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            tk.Label(f, text='❌ 需要安装 matplotlib:\n   pip install matplotlib',
                     font=FONT_TEXT, bg=self._c('bg'), fg='red').pack(pady=50)
            return

        self.viz_canvas = None
        self._viz_current_fig = None

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)

        btn_cfg = [
            ('📊 收支柱状图', self._viz_bar, {'bg': '#7BC67E', 'fg': 'white'}),
            ('🥧 资产饼图', self._viz_pie, {'bg': '#7C3AED', 'fg': 'white'}),
            ('📈 趋势折线图', self._viz_line, {'bg': '#FFB347', 'fg': 'white'}),
            ('🔵 指标雷达图', self._viz_radar, {'bg': '#9C27B0', 'fg': 'white'}),
            ('📋 BI仪表盘', self._viz_dashboard, {'bg': '#FF6B6B', 'fg': 'white'}),
        ]
        for txt, cmd, kw in btn_cfg:
            btn_kw = {**kw, 'font': FONT_TEXT}
            tk.Button(top, text=txt, command=cmd, **btn_kw).pack(side=tk.LEFT, padx=3)

        tk.Label(top, text='年度:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(20, 2))
        self.viz_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.viz_year,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT)

        self.viz_frame = tk.Frame(f, bg='white')
        self.viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._viz_dashboard()

    def _viz_clear(self):
        if self.viz_canvas:
            self.viz_canvas.get_tk_widget().destroy()
            self.viz_canvas = None
        if self._viz_current_fig:
            if plt:
                plt.close(self._viz_current_fig)
            self._viz_current_fig = None

    def _viz_show(self, fig):
        self._viz_clear()
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self._viz_current_fig = fig
        self.viz_canvas = FigureCanvasTkAgg(fig, master=self.viz_frame)
        self.viz_canvas.draw()
        self.viz_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _viz_bar(self):
        year = int(self.viz_year.get())
        fig = acc.chart_income_expense(year)
        self._viz_show(fig)

    def _viz_pie(self):
        fig = acc.chart_balance_pie()
        self._viz_show(fig)

    def _viz_line(self):
        fig = acc.chart_trend_line()
        self._viz_show(fig)

    def _viz_radar(self):
        fig = acc.chart_ratio_radar()
        self._viz_show(fig)

    def _viz_dashboard(self):
        year = int(self.viz_year.get())
        fig = acc.chart_dashboard(year)
        self._viz_show(fig)
