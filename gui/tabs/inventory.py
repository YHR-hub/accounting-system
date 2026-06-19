from __future__ import annotations
"""库存管理(进销存)标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class InventoryTabMixin:
    def _build_inventory_tab(self):
        f = self.tabs['inventory']
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📦 库存管理 (进销存)', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text='➕ 新增商品', font=FONT_TEXT, command=self._add_product_dialog,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📥 入库', font=FONT_TEXT, command=self._inventory_in_dialog,
                  bg=self._c('accent'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='📤 出库', font=FONT_TEXT, command=self._inventory_out_dialog,
                  bg='#FF8A65', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_inventory,
                  bg=self._c('bg'), fg=self._c('accent')).pack(side=tk.LEFT, padx=5)

        panes = tk.PanedWindow(f, orient=tk.VERTICAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        top_frame = tk.Frame(panes, bg=self._c('bg'))
        panes.add(top_frame, height=250)

        tk.Label(top_frame, text='📋 商品列表', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        cols = ('code', 'name', 'category', 'unit', 'price', 'qty', 'min_stock', 'value')
        self.inv_tree = ttk.Treeview(top_frame, columns=cols, show='headings', height=8)
        self.inv_tree.heading('code', text='编码')
        self.inv_tree.heading('name', text='名称')
        self.inv_tree.heading('category', text='分类')
        self.inv_tree.heading('unit', text='单位')
        self.inv_tree.heading('price', text='单价')
        self.inv_tree.heading('qty', text='数量')
        self.inv_tree.heading('min_stock', text='最低库存')
        self.inv_tree.heading('value', text='库存价值')
        for c in cols:
            self.inv_tree.column(c, width=90 if c in ('code','unit','qty') else 120, anchor='e' if c in ('price','qty','value') else 'w')
        self.inv_tree.column('name', width=150)
        self.inv_tree.pack(fill=tk.BOTH, expand=True)
        self.inv_tree.tag_configure('low_stock', foreground='#FF4757')
        self.inv_tree.bind('<Double-1>', self._inv_product_detail)
        self.inv_tree.bind('<Delete>', self._inv_delete_product)

        bot_frame = tk.Frame(panes, bg=self._c('bg'))
        panes.add(bot_frame, height=180)

        tk.Label(bot_frame, text='📋 最近流水', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        tcols = ('time', 'product', 'type', 'qty', 'price', 'note')
        self.inv_trans_tree = ttk.Treeview(bot_frame, columns=tcols, show='headings', height=6)
        self.inv_trans_tree.heading('time', text='时间')
        self.inv_trans_tree.heading('product', text='商品')
        self.inv_trans_tree.heading('type', text='类型')
        self.inv_trans_tree.heading('qty', text='数量')
        self.inv_trans_tree.heading('price', text='单价')
        self.inv_trans_tree.heading('note', text='备注')
        for c in tcols:
            self.inv_trans_tree.column(c, width=80 if c in ('type','qty') else 120)
        self.inv_trans_tree.column('time', width=140)
        self.inv_trans_tree.pack(fill=tk.BOTH, expand=True)
        self._refresh_inventory()

    def _refresh_inventory(self):
        for t in (self.inv_tree, self.inv_trans_tree):
            for i in t.get_children():
                t.delete(i)
        items = acc.get_inventory_summary()
        for it in items:
            tags = ('low_stock',) if float(it['min_stock']) > 0 and float(it['quantity']) < float(it['min_stock']) else ()
            self.inv_tree.insert('', tk.END, values=(
                it['code'], it['name'], it['category'], it['unit'],
                f"{it['unit_price']:,.2f}", f"{it['quantity']:.2f}",
                f"{it['min_stock']:.1f}", f"{it['stock_value']:,.2f}",
            ), tags=tags)
        trans = acc.get_inventory_transactions(limit=50)
        type_labels = {'in': '入库', 'out': '出库', 'adjust': '调整'}
        for t in trans:
            self.inv_trans_tree.insert('', 0, values=(
                t['created_at'][:19], f"{t['product_code']} {t['product_name']}",
                type_labels.get(t['trans_type'], t['trans_type']),
                f"{t['quantity']:.2f}", f"{t['unit_price']:,.2f}", t['note'],
            ))

    def _get_product_choices(self):
        return [f"{p['code']} {p['name']}" for p in acc.get_all_products()]

    def _add_product_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('新增商品')
        win.geometry('450x350')
        win.resizable(False, False)
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = {}
        row_data = [
            ('编码:', 'code'), ('名称:', 'name'), ('分类:', 'category'),
            ('单位:', 'unit'), ('单价:', 'unit_price'), ('最低库存:', 'min_stock'),
        ]
        for i, (label, key) in enumerate(row_data):
            tk.Label(frame, text=label, font=FONT_TEXT, bg=self._c('bg')).grid(row=i, column=0, sticky='w', pady=2)
            var = tk.StringVar()
            tk.Entry(frame, textvariable=var, font=('Consolas', 10)).grid(row=i, column=1, sticky='ew', pady=2, padx=5)
            fields[key] = var
        frame.grid_columnconfigure(1, weight=1)

        def do_add():
            code = fields['code'].get().strip()
            name = fields['name'].get().strip()
            if not code or not name:
                messagebox.showwarning('提示', '编码和名称为必填')
                return
            r = acc.add_product(code, name, fields['category'].get(), fields['unit'].get() or '个',
                                float(fields['unit_price'].get() or 0), float(fields['min_stock'].get() or 0))
            if r['success']:
                messagebox.showinfo('成功', f'商品已添加 (ID: {r["id"]})')
                win.destroy()
                self._refresh_inventory()
            else:
                messagebox.showerror('错误', r.get('error', '添加失败'))

        tk.Button(frame, text='✅ 添加', font=FONT_TEXT, command=do_add,
                  bg=self._c('primary'), fg='white', width=15).grid(row=len(row_data), column=0, columnspan=2, pady=15)

    def _inventory_in_dialog(self):
        choices = self._get_product_choices()
        if not choices:
            messagebox.showinfo('提示', '请先添加商品')
            return
        win = tk.Toplevel(self.root)
        win.title('入库')
        win.geometry('400x250')
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='商品:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        prod_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=prod_var, values=choices, font=FONT_TEXT).pack(fill=tk.X, pady=2)
        tk.Label(frame, text='数量:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10,2))
        qty_var = tk.StringVar(value='1')
        tk.Entry(frame, textvariable=qty_var, font=('Consolas', 11)).pack(fill=tk.X)
        tk.Label(frame, text='单价:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10,2))
        price_var = tk.StringVar(value='0')
        tk.Entry(frame, textvariable=price_var, font=('Consolas', 11)).pack(fill=tk.X)

        def do_in():
            if not prod_var.get():
                return
            pid = next(p['id'] for p in acc.get_all_products() if f"{p['code']} {p['name']}" == prod_var.get())
            acc.inventory_in(pid, float(qty_var.get()), float(price_var.get()), note='手动入库')
            messagebox.showinfo('成功', '入库完成')
            win.destroy()
            self._refresh_inventory()

        tk.Button(frame, text='📥 确认入库', font=FONT_TEXT, command=do_in,
                  bg=self._c('primary'), fg='white', width=15).pack(pady=15)

    def _inventory_out_dialog(self):
        choices = self._get_product_choices()
        if not choices:
            messagebox.showinfo('提示', '请先添加商品')
            return
        win = tk.Toplevel(self.root)
        win.title('出库')
        win.geometry('400x250')
        frame = tk.Frame(win, bg=self._c('bg'), padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='商品:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w')
        prod_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=prod_var, values=choices, font=FONT_TEXT).pack(fill=tk.X, pady=2)
        tk.Label(frame, text='数量:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10,2))
        qty_var = tk.StringVar(value='1')
        tk.Entry(frame, textvariable=qty_var, font=('Consolas', 11)).pack(fill=tk.X)
        tk.Label(frame, text='备注:', font=FONT_TEXT, bg=self._c('bg')).pack(anchor='w', pady=(10,2))
        note_var = tk.Entry(frame, font=('Consolas', 10))
        note_var.pack(fill=tk.X)

        def do_out():
            if not prod_var.get():
                return
            pid = next(p['id'] for p in acc.get_all_products() if f"{p['code']} {p['name']}" == prod_var.get())
            r = acc.inventory_out(pid, float(qty_var.get()), note=note_var.get())
            if r.get('success'):
                messagebox.showinfo('成功', f'出库完成 成本: {r["cost"]:.2f}')
            else:
                messagebox.showerror('错误', r.get('error', '出库失败'))
            win.destroy()
            self._refresh_inventory()

        tk.Button(frame, text='📤 确认出库', font=FONT_TEXT, command=do_out,
                  bg='#FF8A65', fg='white', width=15).pack(pady=15)

    def _inv_product_detail(self, event):
        sel = self.inv_tree.selection()
        if not sel:
            return
        item = self.inv_tree.item(sel[0])
        vals = item['values']
        if not vals:
            return
        code = vals[0]
        prod = acc.get_all_products()
        p = next((x for x in prod if x['code'] == code), None)
        if not p:
            return
        detail = "\n".join([
            f"商品编码: {p['code']}",
            f"商品名称: {p['name']}",
            f"分类: {p['category']}",
            f"单位: {p['unit']}",
            f"单价: {p['unit_price']:,.2f}",
            f"库存: {p['quantity']:.2f}",
            f"最低库存: {p['min_stock']:.1f}",
            f"库存价值: {p['quantity']*p['unit_price']:,.2f}",
        ])
        messagebox.showinfo('商品详情', detail)

    def _inv_delete_product(self, event):
        sel = self.inv_tree.selection()
        if not sel:
            return
        if messagebox.askyesno('确认', '确定要删除该商品吗？'):
            item = self.inv_tree.item(sel[0])
            code = item['values'][0]
            prod = next(p for p in acc.get_all_products() if p['code'] == code)
            acc.update_product(prod['id'], is_active=0)
            self._refresh_inventory()
