from __future__ import annotations
"""附件管理标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.constants import FONT_SUB, FONT_TEXT
import accsys as acc

class AttachmentsTabMixin:
    def _build_attachments_tab(self):
        f = self.tabs['attachments']
        acc.init_attachment_dir()
        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text='📎 附件管理', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        tk.Label(top, text='凭证ID:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT, padx=(15,2))
        self.att_vid = tk.StringVar(value='')
        tk.Entry(top, textvariable=self.att_vid, font=FONT_TEXT, width=8).pack(side=tk.LEFT)
        tk.Button(top, text='📎 上传附件', font=FONT_TEXT, command=self._attach_file,
                  bg=self._c('primary'), fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🔄 刷新', font=FONT_TEXT, command=self._refresh_attachments,
                  bg=self._c('bg'), fg=self._c('accent')).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🗑️ 删除选中', font=FONT_TEXT, command=self._delete_attachment,
                  bg='#FF4757', fg='white').pack(side=tk.LEFT, padx=5)

        cols = ('id', 'vid', 'filename', 'size', 'type', 'created')
        self.att_tree = ttk.Treeview(f, columns=cols, show='headings', height=18)
        self.att_tree.heading('id', text='ID')
        self.att_tree.heading('vid', text='凭证ID')
        self.att_tree.heading('filename', text='文件名')
        self.att_tree.heading('size', text='大小')
        self.att_tree.heading('type', text='类型')
        self.att_tree.heading('created', text='上传时间')
        self.att_tree.column('id', width=40, anchor='center')
        self.att_tree.column('vid', width=70, anchor='center')
        self.att_tree.column('filename', width=300)
        self.att_tree.column('size', width=90, anchor='e')
        self.att_tree.column('type', width=60, anchor='center')
        self.att_tree.column('created', width=150, anchor='center')
        self.att_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._refresh_attachments()

    def _refresh_attachments(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        try:
            vid = int(self.att_vid.get()) if self.att_vid.get().strip() else 0
        except ValueError:
            vid = 0
        rows = acc.get_attachments(voucher_id=vid)
        for r in rows:
            sz = r['file_size']
            if sz > 1024 * 1024:
                sz_str = f"{sz/1024/1024:.1f} MB"
            elif sz > 1024:
                sz_str = f"{sz/1024:.1f} KB"
            else:
                sz_str = f"{sz} B"
            self.att_tree.insert('', tk.END, values=(
                r['id'], r['voucher_id'], r['filename'], sz_str,
                r['file_type'], r['created_at'],
            ))

    def _attach_file(self):
        vid_str = self.att_vid.get().strip()
        if not vid_str:
            messagebox.showwarning('提示', '请输入凭证ID')
            return
        try:
            vid = int(vid_str)
        except ValueError:
            messagebox.showerror('错误', '凭证ID必须是数字')
            return
        fname = filedialog.askopenfilename(title='选择要上传的文件')
        if not fname:
            return
        result = acc.attach_file(vid, fname)
        if result.get('success'):
            messagebox.showinfo('成功', '附件已上传')
            self._refresh_attachments()
        else:
            messagebox.showerror('错误', result.get('error','上传失败'))

    def _delete_attachment(self):
        sel = self.att_tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请选择要删除的附件')
            return
        if not messagebox.askyesno('确认', '确定要删除选中的附件吗？'):
            return
        for item in sel:
            vals = self.att_tree.item(item, 'values')
            acc.delete_attachment(int(vals[0]))
        self._refresh_attachments()
