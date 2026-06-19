from __future__ import annotations
"""固定资产标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import io, sys
from gui.constants import FONT_TEXT
import accsys as acc

class AssetsTabMixin:
    def _build_assets_tab(self):
        f = self.tabs['assets']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=8)
        tk.Button(top, text='➕ 新增资产', font=FONT_TEXT, command=self._add_asset_gui,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_assets,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📊 计提折旧', font=FONT_TEXT, command=self._run_depreciation_gui,
                  bg='#FFD54F').pack(side=tk.LEFT, padx=5)

        cols = ('id', 'name', 'original', 'residual', 'life', 'method', 'deprec')
        self.as_tree = ttk.Treeview(f, columns=cols, show='headings', height=14)
        self.as_tree.heading('id', text='ID')
        self.as_tree.heading('name', text='资产名称')
        self.as_tree.heading('original', text='原值')
        self.as_tree.heading('residual', text='残值')
        self.as_tree.heading('life', text='年限(月)')
        self.as_tree.heading('method', text='折旧方法')
        self.as_tree.heading('deprec', text='累计折旧')
        self.as_tree.column('id', width=40)
        self.as_tree.column('name', width=140)
        self.as_tree.column('original', width=100)
        self.as_tree.column('residual', width=90)
        self.as_tree.column('life', width=80)
        self.as_tree.column('method', width=100)
        self.as_tree.column('deprec', width=100)
        self.as_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._refresh_assets()

    def _refresh_assets(self):
        for item in self.as_tree.get_children():
            self.as_tree.delete(item)
        conn = acc.get_conn()
        rows = conn.execute("SELECT * FROM fixed_assets WHERE is_active=1 ORDER BY id").fetchall()
        conn.close()
        method_names = {'straight': '直线法', 'double': '双倍余额递减法', 'sum-of-years': '年数总和法'}
        for r in rows:
            self.as_tree.insert('', tk.END, values=(
                r['id'], r['name'], f"{r['original_value']:.2f}", f"{r['residual_value']:.2f}",
                r['useful_life_months'], method_names.get(r['depreciation_method'], r['depreciation_method']),
                f"{r['accumulated_deprec']:.2f}"
            ))

    def _add_asset_gui(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('新增固定资产')
        dialog.geometry('450x350+500+250')
        dialog.resizable(False, False)

        fields = []
        for label, key in [('资产名称:', 'name'), ('原值:', 'original'), ('残值 (留空=0):', 'residual'),
                           ('使用年限(月):', 'life'), ('购入日期 (留空=今天):', 'date')]:
            tk.Label(dialog, text=label, font=FONT_TEXT).pack(pady=(8, 2))
            e = tk.Entry(dialog, font=FONT_TEXT, width=30)
            e.pack()
            if key == 'date':
                e.insert(0, date.today().isoformat())
            fields.append((key, e))

        tk.Label(dialog, text='折旧方法:', font=FONT_TEXT).pack(pady=(8, 2))
        method_var = tk.StringVar(value='straight')
        mf = tk.Frame(dialog)
        mf.pack()
        for v, label in [('straight', '直线法'), ('double', '双倍余额递减法'), ('sum-of-years', '年数总和法')]:
            tk.Radiobutton(mf, text=label, variable=method_var, value=v, font=FONT_TEXT).pack(side=tk.LEFT, padx=5)

        def submit():
            data = {k: e.get().strip() for k, e in fields}
            if not data['name']:
                messagebox.showwarning('提示', '请输入资产名称')
                return
            try:
                orig = float(data['original'])
                resid = float(data['residual'] or '0')
                life = int(data['life'])
                if orig <= 0 or life <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror('错误', '原值和年限必须为正数')
                return
            purch = data['date'] if data['date'] else date.today().isoformat()
            method = method_var.get()
            conn = acc.get_conn()
            conn.execute(
                "INSERT INTO fixed_assets (name, original_value, residual_value, useful_life_months, depreciation_method, purchase_date) "
                "VALUES (?,?,?,?,?,?)", (data['name'], orig, resid, life, method, purch))
            conn.commit()
            conn.close()
            depr = acc.calc_depreciation(orig, resid, life, method)
            messagebox.showinfo('成功', f"资产已添加\n月折旧额: {depr:.2f}")
            dialog.destroy()
            self._refresh_assets()

        tk.Button(dialog, text='确认添加', font=FONT_TEXT, command=submit,
                  bg=self._c('primary'), fg='white').pack(pady=15)

    def _run_depreciation_gui(self):
        try:
            old = sys.stdout
            sys.stdout = buf = io.StringIO()
            acc.run_depreciation()
            sys.stdout = old
            messagebox.showinfo('完成', buf.getvalue())
            self._refresh_assets()
            self._refresh_balances()
        except Exception as e:
            messagebox.showerror('错误', f'折旧计提失败: {e}')
