from __future__ import annotations
"""AI 智能财务助手标签页。"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.constants import FONT_SUB, FONT_TEXT, FONT_SMALL, FONT_CUTE
import accsys as acc

class AITabMixin:
    def _build_ai_tab(self):
        f = self.tabs['ai']

        top = tk.Frame(f, bg=self._c('bg'))
        top.pack(fill=tk.X, pady=5)

        tk.Label(top, text='🤖 AI 智能财务助手', font=FONT_SUB, bg=self._c('bg')).pack(side=tk.LEFT, padx=10)

        cfg = acc.load_ai_config()
        status_color = '#7BC67E' if cfg.get('enabled') else '#FF4757'
        status_text = '已启用' if cfg.get('enabled') else '未配置'
        self.ai_status = tk.Label(top, text=f'状态: {status_text}', font=FONT_TEXT,
                                  bg=self._c('bg'), fg=status_color)
        self.ai_status.pack(side=tk.LEFT, padx=10)

        tk.Button(top, text='⚙ 配置AI', font=FONT_TEXT, command=self._show_ai_config,
                  bg='#C084FC', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🗑 清空对话', font=FONT_TEXT, command=self._ai_clear,
                  bg='#E8D5F5').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='🗄️ 数据库查询(RAG)', font=FONT_CUTE, command=self._ai_rag_query,
                  bg='#7BC67E', fg='white').pack(side=tk.LEFT, padx=5)

        chat_frame = tk.Frame(f, bg=self._c('bg'))
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.ai_chat = tk.Text(chat_frame, font=('Consolas', 10),
                               relief=tk.SUNKEN, bg='#FFF0F5', state=tk.DISABLED,
                               wrap=tk.WORD)
        self.ai_chat.pack(fill=tk.BOTH, expand=True)

        inp_frame = tk.Frame(f, bg=self._c('bg'))
        inp_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.ai_input = tk.Text(inp_frame, font=('Consolas', 10), height=3,
                                relief=tk.SUNKEN, wrap=tk.WORD)
        self.ai_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.ai_input.bind('<Return>', self._ai_send_event)
        self.ai_input.bind('<Control-Return>', lambda e: None)

        tk.Button(inp_frame, text='发送', font=('微软雅黑', 11, 'bold'),
                  command=self._ai_send, bg=self._c('primary'), fg='white',
                  width=8, height=2).pack(side=tk.RIGHT)

        self.ai_history = []
        self._ai_add_message('system', '欢迎使用AI财务助手！你可以问我关于财务状况的问题，\n例如：\n'
                                      '  \u2022 \"本月收入多少？\"\n'
                                      '  \u2022 \"分析我的资产负债结构\"\n'
                                      '  \u2022 \"生成财务分析报告\"\n'
                                      '  \u2022 \"我的现金流状况如何？\"\n')

    def _ai_add_message(self, role, content):
        self.ai_chat.config(state=tk.NORMAL)
        if role == 'system':
            prefix = '🤖 '
            tag = 'system'
        elif role == 'user':
            prefix = '👤 '
            tag = 'user'
        elif role == 'assistant':
            prefix = '🤖 '
            tag = 'assistant'
        elif role == 'error':
            prefix = '❌ '
            tag = 'error'
        else:
            prefix = ''
            tag = ''

        self.ai_chat.insert(tk.END, f'{prefix}{content}\n\n', tag)
        self.ai_chat.see(tk.END)
        self.ai_chat.config(state=tk.DISABLED)

        self.ai_chat.tag_configure('system', foreground='#888888')
        self.ai_chat.tag_configure('user', foreground='#7C3AED')
        self.ai_chat.tag_configure('assistant', foreground='#7BC67E')
        self.ai_chat.tag_configure('error', foreground='#FF4757')

    def _ai_send_event(self, event):
        if not event.state & 0x0001:  # Shift not held
            self._ai_send()
            return 'break'

    def _ai_send(self):
        text = self.ai_input.get('1.0', tk.END).strip()
        if not text:
            return
        self.ai_input.delete('1.0', tk.END)

        self._ai_add_message('user', text)
        self.ai_history.append({"role": "user", "content": text})
        self.root.update()

        cfg = acc.load_ai_config()
        if not cfg.get('enabled') or not cfg.get('api_key'):
            self._ai_add_message('error', '请先点击\"配置AI\"填写API密钥并启用')
            return

        try:
            response = acc.call_ai(self.ai_history[-5:])  # last 5 messages for context
            self._ai_add_message('assistant', response)
            self.ai_history.append({"role": "assistant", "content": response})
        except Exception as e:
            self._ai_add_message('error', f'调用失败: {e}')

    def _ai_clear(self):
        self.ai_chat.config(state=tk.NORMAL)
        self.ai_chat.delete('1.0', tk.END)
        self.ai_chat.config(state=tk.DISABLED)
        self.ai_history = []
        self._ai_add_message('system', '对话已清空，可以开始新的咨询。')

    def _ai_rag_query(self):
        text = self.ai_input.get('1.0', tk.END).strip()
        if not text:
            messagebox.showinfo('提示', '请输入查询问题')
            return
        self._ai_add_message('user', f'[数据库查询] {text}')
        self.root.update()
        result = acc.ai_query_database(text)
        self._ai_add_message('assistant', f'📊 查询结果:\n{result}')

    def _show_ai_config(self):
        win = tk.Toplevel(self.root)
        win.title('AI 配置')
        win.geometry('500x400')
        win.resizable(False, False)

        cfg = acc.load_ai_config()

        frame = tk.Frame(win, bg=self._c('bg'), padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text='🤖 云端AI模型配置', font=FONT_SUB,
                 bg=self._c('bg')).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        row = 1
        self.ai_cfg_enabled = tk.BooleanVar(value=cfg.get('enabled', False))
        tk.Checkbutton(frame, text='启用AI助手', variable=self.ai_cfg_enabled,
                       font=FONT_TEXT, bg=self._c('bg')).grid(row=row, column=0, columnspan=2, sticky='w')
        row += 1

        fields = [
            ('provider', '提供商:', cfg.get('provider', 'openai')),
            ('endpoint', 'API地址:', cfg.get('endpoint', '')),
            ('api_key', 'API密钥:', cfg.get('api_key', '')),
            ('model', '模型名称:', cfg.get('model', 'gpt-3.5-turbo')),
            ('max_tokens', '最大Token:', str(cfg.get('max_tokens', 2048))),
            ('temperature', '温度(0-2):', str(cfg.get('temperature', 0.7))),
        ]
        self.ai_cfg_vars = {}
        for key, label, default in fields:
            tk.Label(frame, text=label, font=FONT_TEXT, bg=self._c('bg')).grid(
                row=row, column=0, sticky='w', pady=3)
            if key == 'api_key':
                var = tk.StringVar(value=default)
                ent = tk.Entry(frame, textvariable=var, font=('Consolas', 10),
                               width=40, show='*')
            else:
                var = tk.StringVar(value=default)
                ent = tk.Entry(frame, textvariable=var, font=('Consolas', 10), width=40)
            ent.grid(row=row, column=1, pady=3)
            self.ai_cfg_vars[key] = var
            row += 1

        preset_frame = tk.Frame(frame, bg=self._c('bg'))
        preset_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tk.Label(preset_frame, text='快速选择:', font=FONT_TEXT, bg=self._c('bg')).pack(side=tk.LEFT)

        presets = {
            'OpenAI': ('https://api.openai.com/v1/chat/completions', 'gpt-3.5-turbo'),
            'Doubao(火山引擎)': ('https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'doubao-chat-128k'),
            'DeepSeek': ('https://api.deepseek.com/v1/chat/completions', 'deepseek-chat'),
        }
        for name, (ep, model) in presets.items():
            btn = tk.Button(preset_frame, text=name, font=FONT_SMALL, bd=1,
                            command=lambda e=ep, m=model: self._ai_preset(e, m))
            btn.pack(side=tk.LEFT, padx=3)
        row += 1

        btn_frame = tk.Frame(frame, bg=self._c('bg'))
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text='💾 保存', font=FONT_TEXT, command=lambda: self._ai_save_cfg(win),
                  bg=self._c('primary'), fg='white', width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='测试连接', font=FONT_TEXT, command=self._ai_test,
                  bg='#C084FC', fg='white', width=12).pack(side=tk.LEFT, padx=5)

    def _ai_preset(self, endpoint, model):
        self.ai_cfg_vars['endpoint'].set(endpoint)
        self.ai_cfg_vars['model'].set(model)

    def _ai_save_cfg(self, win):
        cfg = {
            'enabled': self.ai_cfg_enabled.get(),
            'provider': self.ai_cfg_vars['provider'].get(),
            'endpoint': self.ai_cfg_vars['endpoint'].get().strip(),
            'api_key': self.ai_cfg_vars['api_key'].get().strip(),
            'model': self.ai_cfg_vars['model'].get().strip(),
            'max_tokens': int(self.ai_cfg_vars['max_tokens'].get() or 2048),
            'temperature': float(self.ai_cfg_vars['temperature'].get() or 0.7),
        }
        if acc.save_ai_config(cfg):
            messagebox.showinfo('成功', 'AI配置已保存')
            win.destroy()
            sc = '#7BC67E' if cfg['enabled'] else '#FF4757'
            st = '已启用' if cfg['enabled'] else '未配置'
            self.ai_status.config(text=f'状态: {st}', fg=sc)
        else:
            messagebox.showerror('错误', '保存失败')

    def _ai_test(self):
        cfg = {
            'enabled': self.ai_cfg_enabled.get(),
            'endpoint': self.ai_cfg_vars['endpoint'].get().strip(),
            'api_key': self.ai_cfg_vars['api_key'].get().strip(),
            'model': self.ai_cfg_vars['model'].get().strip(),
            'max_tokens': 128,
            'temperature': 0.3,
        }
        if not cfg['api_key']:
            messagebox.showwarning('提示', '请先填写API密钥')
            return
        old_cfg = acc.load_ai_config()
        acc.save_ai_config(cfg)
        try:
            result = acc.call_ai([{"role": "user", "content": "回复'连接成功'四个字"}])
            if '失败' in result or '错误' in result or '请先配置' in result:
                acc.save_ai_config(old_cfg)
                messagebox.showerror('测试失败', result[:200])
            else:
                messagebox.showinfo('测试成功', f'AI返回: {result[:100]}')
                if hasattr(self, 'ai_status'):
                    sc = '#7BC67E' if cfg['enabled'] else '#FF4757'
                    st = '已启用' if cfg['enabled'] else '未配置'
                    self.ai_status.config(text=f'状态: {st}', fg=sc)
        except Exception as e:
            acc.save_ai_config(old_cfg)
            messagebox.showerror('测试错误', str(e))
