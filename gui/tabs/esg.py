from __future__ import annotations
"""ESG 可持续发展报告标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL
import accsys as acc

class ESGTabMixin:
    def _build_esg_tab(self):
        f = self.tabs['esg']
        acc.init_esg_tables()

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)

        tk.Label(top, text='📊 ESG 可持续发展报告', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Label(top, text='年度:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(10, 2))
        self.esg_year = tk.StringVar(value=str(date.today().year))
        tk.Spinbox(top, from_=2020, to=2099, textvariable=self.esg_year,
                   font=FONT_TEXT, width=8).pack(side=tk.LEFT)

        tk.Button(top, text='🔄 刷新评分', font=FONT_TEXT, command=self._esg_refresh_scores,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=10)

        self.esg_score_label = tk.Label(top, text='综合评分: -- | 评级: --',
                                        font=('微软雅黑', 12, 'bold'), bg=self._c('bg'), fg='#7BC67E')
        self.esg_score_label.pack(side=tk.LEFT, padx=20)

        esg_sub = ttk.Notebook(f)
        esg_sub.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.esg_sub_frames = {}
        for key, label in [('env', '  环境(E)  '), ('social', '  社会(S)  '),
                           ('gov', '  治理(G)  '), ('report', '  报告  ')]:
            frame = tk.Frame(esg_sub, bg=self._c('bg'))
            esg_sub.add(frame, text=label)
            self.esg_sub_frames[key] = frame

        self._build_esg_entry_page('env', 'environment')
        self._build_esg_entry_page('social', 'social')
        self._build_esg_entry_page('gov', 'governance')
        self._build_esg_report_page()

        self._esg_refresh_scores()

    def _build_esg_entry_page(self, frame_key, cat_key):
        f = self.esg_sub_frames[frame_key]

        scroll = tk.Frame(f, bg=self._c('bg'))
        scroll.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll, bg=self._c('bg'), highlightthickness=0)
        vsb = ttk.Scrollbar(scroll, orient=tk.VERTICAL, command=canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=vsb.set)

        inner = tk.Frame(canvas, bg=self._c('bg'))
        canvas.create_window((0, 0), window=inner, anchor='nw')

        def _configure_inner(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        inner.bind('<Configure>', _configure_inner)

        cat_info = acc.ESG_INDICATORS.get(cat_key, {})
        metrics = cat_info.get("metrics", [])

        entries = {}
        for ind_key, ind_label, ind_unit, ind_note in metrics:
            frame_row = tk.Frame(inner, bg=self._c('bg'))
            frame_row.pack(fill=tk.X, padx=10, pady=3)

            tk.Label(frame_row, text=f'{ind_label} ({ind_unit}):', font=FONT_TEXT,
                     bg=self._c('bg'), width=22, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar(value='0')
            ent = tk.Entry(frame_row, textvariable=var, font=FONT_TEXT, width=14)
            ent.pack(side=tk.LEFT, padx=5)

            tk.Label(frame_row, text=ind_note, font=FONT_SMALL, bg=self._c('bg'),
                     fg='gray').pack(side=tk.LEFT, padx=5)

            data = acc.get_esg_data(cat_key, int(self.esg_year.get()), ind_key)
            if data:
                var.set(str(data[0]['value']))

            entries[ind_key] = (var, ind_label, ind_unit)

        btn_frame = tk.Frame(inner, bg=self._c('bg'))
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text=f'💾 保存{cat_info.get("label","")}数据', font=FONT_TEXT,
                  command=lambda c=cat_key, e=entries: self._esg_save(c, e),
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)

        if not hasattr(self, '_esg_entries'):
            self._esg_entries = {}
        self._esg_entries[cat_key] = entries

    def _esg_save(self, cat_key, entries):
        year = int(self.esg_year.get())
        ok_count = 0
        for ind_key, (var, label, unit) in entries.items():
            try:
                val = float(var.get().strip())
            except ValueError:
                messagebox.showwarning('提示', f'{label}: 请输入有效数字')
                continue
            if acc.upsert_esg_data(cat_key, year, ind_key, val):
                ok_count += 1
        if ok_count:
            messagebox.showinfo('成功', f'已保存 {ok_count} 项{cat_key}数据')
            self._esg_refresh_scores()
        else:
            messagebox.showerror('错误', '保存失败')

    def _build_esg_report_page(self):
        f = self.esg_sub_frames['report']

        top_bar = tk.Frame(f, bg=self._c('bg'))
        top_bar.pack(fill=tk.X, pady=5)
        tk.Button(top_bar, text='📄 生成报告', font=FONT_TEXT,
                  command=self._esg_gen_report, bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top_bar, text='📤 导出报告', font=FONT_TEXT,
                  command=self._esg_export_report, bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top_bar, text='📊 评分雷达图', font=FONT_TEXT,
                  command=self._esg_show_radar, bg='#9C27B0', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top_bar, text='📈 历年趋势图', font=FONT_TEXT,
                  command=self._esg_show_trend, bg='#7C3AED', fg='white').pack(side=tk.LEFT, padx=5)

        self.esg_report_text = tk.Text(f, font=('Consolas', 10), height=20,
                                       relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.esg_report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _esg_refresh_scores(self):
        year = int(self.esg_year.get())
        scores = acc.calc_esg_scores(year)
        self.esg_score_label.config(text=f'综合评分: {scores["overall"]} | 评级: {scores["rating"]}')
        for cat_key in ['environment', 'social', 'governance']:
            data_map = acc.get_esg_data_map(cat_key, year)
            entries = getattr(self, '_esg_entries', {}).get(cat_key, {})
            for ind_key, (var, _, _) in entries.items():
                if ind_key in data_map:
                    var.set(str(data_map[ind_key]))

    def _esg_gen_report(self):
        year = int(self.esg_year.get())
        report = acc.generate_esg_report(year)
        self.esg_report_text.config(state=tk.NORMAL)
        self.esg_report_text.delete('1.0', tk.END)
        self.esg_report_text.insert(tk.END, report)
        self.esg_report_text.config(state=tk.DISABLED)

    def _esg_export_report(self):
        year = int(self.esg_year.get())
        path = filedialog.asksaveasfilename(defaultextension='.txt',
                                            initialfile=f'ESG_{year}.txt',
                                            filetypes=[('Text', '*.txt')])
        if not path:
            return
        result = acc.export_esg_report_to_file(year, path)
        if 'error' in result:
            messagebox.showerror('错误', result['error'])
        else:
            messagebox.showinfo('成功', result['message'])

    def _esg_show_radar(self):
        year = int(self.esg_year.get())
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            messagebox.showwarning('提示', '需要安装 matplotlib')
            return
        fig = acc.chart_esg_radar(year)
        win = tk.Toplevel(self.root)
        win.title(f'ESG评分雷达图 - {year}年')
        win.geometry('600x600')
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tk.Button(win, text='关闭', command=win.destroy).pack(pady=5)

    def _esg_show_trend(self):
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            messagebox.showwarning('提示', '需要安装 matplotlib')
            return
        fig = acc.chart_esg_trend()
        win = tk.Toplevel(self.root)
        win.title('ESG历年趋势图')
        win.geometry('800x500')
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tk.Button(win, text='关闭', command=win.destroy).pack(pady=5)
