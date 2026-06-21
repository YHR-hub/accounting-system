from __future__ import annotations

from typing import Dict

FONT_TITLE = ('微软雅黑', 16, 'bold')
FONT_SUB = ('微软雅黑', 12, 'bold')
FONT_TEXT = ('微软雅黑', 11)
FONT_SMALL = ('微软雅黑', 10)
FONT_CUTE = ('微软雅黑', 10, 'bold')

COLOR_BG = '#F4F5F7'
COLOR_PRIMARY = '#6C5CE7'
COLOR_SUCCESS = '#00B894'
COLOR_WARN = '#FDCB6E'
COLOR_ALT = '#EEF0FF'
COLOR_ACCENT = '#5A4BD1'
COLOR_VIOLET = '#5A4BD1'
COLOR_PURPLE = '#8E7CF0'

MOOD_COLORS: Dict = {}

# 特性开关：实验性/探索性模块（区块链账本、ESG、AI 助手）。
# True=显示全部功能（演示广度）；False=只保留核心会计功能（聚焦演示）。
# 可在此切换，或设环境变量 SHOW_EXPERIMENTAL=0 关闭。
import os as _os
SHOW_EXPERIMENTAL = _os.environ.get('SHOW_EXPERIMENTAL', '1') != '0'
EXPERIMENTAL_TABS = ('blockchain', 'esg', 'ai')
