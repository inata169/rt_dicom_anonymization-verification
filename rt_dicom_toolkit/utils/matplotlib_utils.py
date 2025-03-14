"""
matplotlibの設定ユーティリティ
"""

import matplotlib.pyplot as plt
import matplotlib
import os
import sys
import platform

def configure_matplotlib_for_japanese():
    """
    matplotlibで日本語を表示するための設定を行う
    """
    # フォント設定
    if platform.system() == 'Windows':
        # Windowsの場合
        font_family = 'MS Gothic'
        matplotlib.rcParams['font.family'] = font_family
    elif platform.system() == 'Darwin':
        # macOSの場合
        font_family = 'AppleGothic'
        matplotlib.rcParams['font.family'] = font_family
    else:
        # Linux/その他の場合
        try:
            # IPAフォントがインストールされている場合
            font_family = 'IPAGothic'
            matplotlib.rcParams['font.family'] = font_family
        except:
            # フォールバック: sans-serifを使用
            matplotlib.rcParams['font.family'] = ['sans-serif']
            # 日本語が含まれる場合はフォントを指定しない
            pass
    
    # 文字化け防止のためのエンコーディング設定
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    
    # 日本語を表示するためのフォント設定
    matplotlib.rcParams['axes.unicode_minus'] = False  # マイナス記号を正しく表示
    
    return True
