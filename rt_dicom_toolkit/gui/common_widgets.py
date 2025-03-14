"""
共通のGUIウィジェットを提供するモジュール
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DirectorySelector(ttk.Frame):
    """ディレクトリ選択フレーム"""
    
    def __init__(self, parent, label_text, initial_dir, browse_command):
        """
        ディレクトリ選択フレームを初期化
        
        Args:
            parent: 親ウィジェット
            label_text: ラベルテキスト
            initial_dir: 初期ディレクトリ
            browse_command: 参照ボタンのコマンド
        """
        super().__init__(parent)
        
        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=5)
        
        self.dir_var = tk.StringVar(value=str(initial_dir))
        ttk.Entry(self, textvariable=self.dir_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(self, text="参照...", command=browse_command).pack(side=tk.LEFT)
    
    def get(self):
        """選択されたディレクトリパスを取得"""
        return Path(self.dir_var.get())
    
    def set(self, path):
        """ディレクトリパスを設定"""
        self.dir_var.set(str(path))


class LogTextFrame(ttk.LabelFrame):
    """ログテキスト表示フレーム"""
    
    def __init__(self, parent, title="ログ"):
        """
        ログテキスト表示フレームを初期化
        
        Args:
            parent: 親ウィジェット
            title: フレームタイトル
        """
        super().__init__(parent, text=title, padding="5")
        
        self.text = tk.Text(self, height=15, width=70, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(self.text, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)
    
    def append(self, message):
        """メッセージを追加"""
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
    
    def clear(self):
        """テキストをクリア"""
        self.text.delete(1.0, tk.END)


class GraphFrame(ttk.LabelFrame):
    """グラフ表示フレーム"""
    
    def __init__(self, parent, title="グラフ", figsize=(8, 6)):
        """
        グラフ表示フレームを初期化
        
        Args:
            parent: 親ウィジェット
            title: フレームタイトル
            figsize: グラフのサイズ
        """
        super().__init__(parent, text=title, padding="5")
        
        self.figure, self.ax = plt.subplots(figsize=figsize)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def draw(self):
        """グラフを描画"""
        self.canvas.draw()
    
    def clear(self):
        """グラフをクリア"""
        self.ax.clear()
        self.draw()