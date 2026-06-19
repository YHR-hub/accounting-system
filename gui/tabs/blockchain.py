from __future__ import annotations
"""区块链账本标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class BlockchainTabMixin:
    def _build_blockchain_tab(self):
        f = self.tabs['blockchain']
        acc.init_blockchain()

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)

        btns = [
            ('🔄 初始化链', self._bc_init, self._c('primary'), 'white'),
            ('➕ 哈希所有凭证', self._bc_hash_all, '#FFB347', 'white'),
            ('✅ 完整性验证', self._bc_validate, '#7BC67E', 'white'),
            ('📤 导出JSON', self._bc_export, '#7C3AED', 'white'),
            ('📥 导入JSON', self._bc_import, '#FF8A65', 'white'),
        ]
        for txt, cmd, bgc, fgc in btns:
            tk.Button(top, text=txt, font=FONT_TEXT, command=cmd,
                      bg=bgc, fg=fgc).pack(side=tk.LEFT, padx=3)

        panes = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=self._c('bg'))
        panes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = tk.Frame(panes, bg=self._c('bg'))
        panes.add(left, width=350)

        tk.Label(left, text='📋 区块列表', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        cols = ('idx', 'hash', 'voucher')
        self.bc_tree = ttk.Treeview(left, columns=cols, show='headings', height=16)
        self.bc_tree.heading('idx', text='索引')
        self.bc_tree.heading('hash', text='Hash(前8位)')
        self.bc_tree.heading('voucher', text='凭证号')
        self.bc_tree.column('idx', width=50)
        self.bc_tree.column('hash', width=120)
        self.bc_tree.column('voucher', width=140)
        self.bc_tree.pack(fill=tk.BOTH, expand=True)
        self.bc_tree.bind('<<TreeviewSelect>>', self._bc_show_detail)

        right = tk.Frame(panes, bg=self._c('bg'))
        panes.add(right, width=500)

        tk.Label(right, text='📄 区块详情', font=FONT_SUB, bg=self._c('bg')).pack(anchor='w')
        self.bc_detail = tk.Text(right, font=('Consolas', 10), height=20,
                                 relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED)
        self.bc_detail.pack(fill=tk.BOTH, expand=True)

        self._bc_refresh()

    def _bc_refresh(self):
        for item in self.bc_tree.get_children():
            self.bc_tree.delete(item)
        chain = acc.get_chain(limit=200)
        for b in chain:
            h_short = b['hash'][:8] + '...' if b['hash'] else ''
            v_no = b.get('voucher_no', '') or ''
            self.bc_tree.insert('', tk.END, iid=str(b['index_no']),
                                values=(b['index_no'], h_short, v_no))
        self._bc_show_stats()

    def _bc_show_stats(self):
        stats = acc.get_chain_stats()
        self.bc_detail.config(state=tk.NORMAL)
        self.bc_detail.delete('1.0', tk.END)
        self.bc_detail.insert(tk.END, '📊 区块链状态\n')
        self.bc_detail.insert(tk.END, f'区块总数: {stats["total_blocks"]}\n')
        self.bc_detail.insert(tk.END, f'末块索引: {stats["last_block_index"]}\n')
        self.bc_detail.insert(tk.END, f'末块Hash: {stats["last_block_hash"]}\n')
        if stats['total_blocks'] > 0:
            valid = acc.validate_chain()
            status = '✅ 链完整' if valid['valid'] else '❌ 链损坏'
            self.bc_detail.insert(tk.END, f'完整性: {status}\n')
        self.bc_detail.config(state=tk.DISABLED)

    def _bc_show_detail(self, event=None):
        selected = self.bc_tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        b = acc.get_block_by_index(idx)
        self.bc_detail.config(state=tk.NORMAL)
        self.bc_detail.delete('1.0', tk.END)
        if b:
            self.bc_detail.insert(tk.END, f'索引: {b["index_no"]}\n')
            self.bc_detail.insert(tk.END, f'时间戳: {b["timestamp"]}\n')
            self.bc_detail.insert(tk.END, f'前驱Hash: {b["previous_hash"]}\n')
            self.bc_detail.insert(tk.END, f'自身Hash: {b["hash"]}\n')
            self.bc_detail.insert(tk.END, f'Nonce: {b["nonce"]}\n')
            self.bc_detail.insert(tk.END, f'凭证ID: {b.get("voucher_id", "")}\n')
            self.bc_detail.insert(tk.END, f'凭证号: {b.get("voucher_no", "")}\n')
            self.bc_detail.insert(tk.END, f'数据: {b.get("data", "{}")}\n')
        else:
            self.bc_detail.insert(tk.END, '未找到区块\n')
        self.bc_detail.config(state=tk.DISABLED)

    def _bc_init(self):
        acc.init_blockchain()
        self._bc_refresh()
        messagebox.showinfo('区块链', '初始化完成（创始区块已创建）')

    def _bc_hash_all(self):
        result = acc.add_all_vouchers_to_chain()
        self._bc_refresh()
        messagebox.showinfo('哈希完成', f'新增 {result["added"]} 个区块\n总区块数: {result["total_blocks"]}')

    def _bc_validate(self):
        result = acc.validate_chain()
        if result['valid']:
            messagebox.showinfo('验证结果', f'✅ 区块链完整无误 ({result["blocks"]} 个区块)')
        else:
            msg = '❌ 发现以下问题:\n' + '\n'.join(result['errors'])
            messagebox.showerror('验证结果', msg)

    def _bc_export(self):
        path = filedialog.asksaveasfilename(defaultextension='.json',
                                            initialfile='blockchain.json',
                                            filetypes=[('JSON', '*.json')])
        if not path:
            return
        result = acc.export_chain_json(path)
        if 'error' in result:
            messagebox.showerror('错误', result['error'])
        else:
            messagebox.showinfo('导出成功', result['message'])
            self._bc_refresh()

    def _bc_import(self):
        path = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if not path:
            return
        result = acc.import_chain_json(path)
        if 'error' in result:
            messagebox.showerror('错误', result['error'])
        else:
            messagebox.showinfo('导入成功', result['message'])
            self._bc_refresh()
