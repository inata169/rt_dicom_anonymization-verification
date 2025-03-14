"""
検証ツールのGUIモジュール
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os

# 日本語フォント設定のインポート
from rt_dicom_toolkit.utils.matplotlib_utils import configure_matplotlib_for_japanese

# パッケージとしてインストールされている場合は以下のインポートを使用
from rt_dicom_toolkit.validator import RTDicomValidator
from rt_dicom_toolkit.validator.rules import ValidationRules

# パッケージとしてインストールされていない場合は相対パスを追加
if not "rt_dicom_toolkit" in sys.modules:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from validator import RTDicomValidator
    from validator.rules import ValidationRules

class ValidatorGUI:
    """検証ツールのGUIを提供するクラス"""
    
    def __init__(self, root):
        """
        検証ツールのGUIを初期化
        
        Args:
            root: TkinterのRootウィンドウ
        """
        self.root = root
        self.root.title("RT DICOM匿名化検証ツール")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 検証ツールのインスタンスを作成
        self.validator = RTDicomValidator(self.root)
        
        # GUIを設定
        self.setup_gui()
        
    def setup_gui(self):
        """GUIのセットアップ"""
        # 日本語フォント設定を適用
        configure_matplotlib_for_japanese()
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ディレクトリ選択部分
        dir_frame = ttk.LabelFrame(main_frame, text="ディレクトリ設定", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # 原本ディレクトリ
        ttk.Label(dir_frame, text="原本ディレクトリ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.original_dir_var = tk.StringVar(value=str(self.validator.original_dir))
        ttk.Entry(dir_frame, textvariable=self.original_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_original_dir).grid(row=0, column=2, pady=5)
        
        # 匿名化ディレクトリ
        ttk.Label(dir_frame, text="匿名化ディレクトリ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.anonymized_dir_var = tk.StringVar(value=str(self.validator.anonymized_dir))
        ttk.Entry(dir_frame, textvariable=self.anonymized_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_anonymized_dir).grid(row=1, column=2, pady=5)
        
        # レポートディレクトリ
        ttk.Label(dir_frame, text="レポートディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.report_dir_var = tk.StringVar(value=str(self.validator.report_dir))
        ttk.Entry(dir_frame, textvariable=self.report_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_report_dir).grid(row=2, column=2, pady=5)
        
        # 検証設定部分
        settings_frame = ttk.LabelFrame(main_frame, text="検証設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 匿名化レベル
        ttk.Label(settings_frame, text="匿名化レベル確認:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        self.validator.anonymization_level = self.anonymization_level
        ttk.Radiobutton(settings_frame, text="完全匿名化", variable=self.anonymization_level, 
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="部分匿名化（日付・施設情報を保持）", variable=self.anonymization_level, 
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # プライベートタグの確認
        ttk.Label(settings_frame, text="プライベートタグ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.check_private_tags = tk.BooleanVar(value=True)
        self.validator.check_private_tags = self.check_private_tags
        ttk.Checkbutton(settings_frame, text="プライベートタグの削除を確認", 
                        variable=self.check_private_tags).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # ファイル構造の保持確認
        ttk.Label(settings_frame, text="構造確認:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.check_file_structure = tk.BooleanVar(value=True)
        self.validator.check_file_structure = self.check_file_structure
        ttk.Checkbutton(settings_frame, text="ファイル構造の保持を確認", 
                       variable=self.check_file_structure).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # UID確認
        ttk.Label(settings_frame, text="UID確認:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.check_uid_changed = tk.BooleanVar(value=True)
        self.validator.check_uid_changed = self.check_uid_changed
        ttk.Checkbutton(settings_frame, text="すべてのUIDが変更されていることを確認", 
                        variable=self.check_uid_changed).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 詳細レポート
        ttk.Label(settings_frame, text="レポートレベル:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.detailed_report = tk.BooleanVar(value=True)
        self.validator.detailed_report = self.detailed_report
        ttk.Checkbutton(settings_frame, text="詳細なレポートを生成", 
                        variable=self.detailed_report).grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="検証実行", command=self.start_validation).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="ディレクトリ比較", command=self.compare_directories).pack(side=tk.RIGHT, padx=5)
        
        # ノートブック（タブ付きインターフェース）を作成
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ログタブ
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="ログ")
        
        # ログテキストエリア
        self.log_text = tk.Text(log_frame, height=15, width=70, wrap=tk.WORD)
        self.validator.log_text = self.log_text
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 結果サマリータブ
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="結果サマリー")
        
        # サマリーテキストエリア
        self.summary_text = tk.Text(summary_frame, height=15, width=70, wrap=tk.WORD)
        self.validator.summary_text = self.summary_text
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # スクロールバー
        summary_scrollbar = ttk.Scrollbar(self.summary_text, command=self.summary_text.yview)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.config(yscrollcommand=summary_scrollbar.set)
        
        # グラフタブ
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="グラフ")
        
        # グラフ用のキャンバス
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.validator.figure = self.figure
        self.validator.ax = self.ax
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.validator.canvas = self.canvas
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 詳細タブ
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="詳細")
        
        # ツリービュー
        self.tree = ttk.Treeview(details_frame)
        self.validator.tree = self.tree
        self.tree["columns"] = ("原本値", "匿名化値", "状態")
        self.tree.column("#0", width=200, minwidth=200)
        self.tree.column("原本値", width=200, minwidth=200)
        self.tree.column("匿名化値", width=200, minwidth=200)
        self.tree.column("状態", width=100, minwidth=100)
        
        self.tree.heading("#0", text="タグ名")
        self.tree.heading("原本値", text="原本値")
        self.tree.heading("匿名化値", text="匿名化値")
        self.tree.heading("状態", text="状態")
        
        # ツリービューにスクロールバーを追加
        tree_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # 配置
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        self.validator.status_var = self.status_var
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ツリービュー更新メソッドをvalidatorに追加
        self.validator.update_treeview = self.update_treeview
        
        # グラフ描画メソッドをvalidatorに追加
        self.validator.draw_validation_graphs = self.draw_validation_graphs
    
    def browse_original_dir(self):
        """原本ディレクトリを選択"""
        directory = filedialog.askdirectory(title="原本DICOMファイルがあるディレクトリを選択")
        if directory:
            self.original_dir_var.set(directory)
            self.validator.original_dir = Path(directory)
            self.validator.log_message(f"原本ディレクトリを設定: {directory}")
    
    def browse_anonymized_dir(self):
        """匿名化ディレクトリを選択"""
        directory = filedialog.askdirectory(title="匿名化DICOMファイルがあるディレクトリを選択")
        if directory:
            self.anonymized_dir_var.set(directory)
            self.validator.anonymized_dir = Path(directory)
            self.validator.log_message(f"匿名化ディレクトリを設定: {directory}")
    
    def browse_report_dir(self):
        """レポートディレクトリを選択"""
        directory = filedialog.askdirectory(title="検証レポートの保存先ディレクトリを選択")
        if directory:
            self.report_dir_var.set(directory)
            self.validator.report_dir = Path(directory)
            self.validator.log_message(f"レポートディレクトリを設定: {directory}")
    
    def update_treeview(self, results, clear=True):
        """ツリービューを結果で更新する"""
        try:
            # 初回のみツリービューをクリア
            if clear:
                self.tree.delete(*self.tree.get_children())
                
                # タグ分類ごとにグループを作成
                self.must_anonymize_group = self.tree.insert("", "end", text="必須匿名化タグ", open=True)
                self.uid_group = self.tree.insert("", "end", text="UIDタグ", open=True)
                self.structure_group = self.tree.insert("", "end", text="構造タグ", open=True)
                self.optional_group = self.tree.insert("", "end", text="オプション匿名化タグ", open=True)
                self.rt_group = self.tree.insert("", "end", text="RT特有タグ", open=True)
                self.private_group = self.tree.insert("", "end", text="プライベートタグ", open=True)
                self.pixel_group = self.tree.insert("", "end", text="画像データ", open=True)
            
            # 必須匿名化タグを追加
            for tag, info in results["must_anonymize"].items():
                # 表示する原本値を処理（長すぎる場合は省略）
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                # 表示する匿名化値を処理
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                # アイコンとステータスの設定
                status = info["status"]
                if info["anonymized"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.must_anonymize_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # UIDタグを追加
            for tag, info in results["uid_tags"].items():
                # UIDは長いので省略表示
                orig_value = info["original"]
                if len(orig_value) > 20:
                    orig_value = orig_value[:17] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 20:
                    anon_value = anon_value[:17] + "..."
                
                status = info["status"]
                if info["changed"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.uid_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # 構造タグを追加
            for tag, info in results["structure_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if info["preserved"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.structure_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # オプション匿名化タグを追加
            for tag, info in results["optional_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                # 匿名化レベルによってチェックマークが変わる
                if self.anonymization_level.get() == "full":
                    if info["changed"]:
                        status = "✅ " + status
                    else:
                        status = "❌ " + status
                else:
                    # 部分匿名化の場合は常にOK
                    status = "✅ " + status
                
                self.tree.insert(self.optional_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # RT特有タグを追加
            for tag, info in results["rt_specific_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if "正しく" in status:
                    status = "✅ " + status
                elif "未変更" in status or "保持すべき" in status or "匿名化されていない" in status:
                    status = "❌ " + status
                else:
                    status = "ℹ️ " + status
                
                self.tree.insert(self.rt_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # プライベートタグの情報を追加
            original_count = results["private_tags"]["original_count"]
            anonymized_count = results["private_tags"]["anonymized_count"]
            
            status = "✅ すべて削除" if anonymized_count == 0 else f"❌ {anonymized_count}個残存"
            self.tree.insert(self.private_group, "end", text="プライベートタグ数", 
                           values=(f"{original_count}個", f"{anonymized_count}個", status))
            
            # ピクセルデータの情報を追加（あれば）
            if results["pixel_data"]["original_shape"] is not None:
                orig_shape = results["pixel_data"]["original_shape"]
                anon_shape = results["pixel_data"]["anonymized_shape"]
                
                shape_match = orig_shape == anon_shape
                pixel_match = results["pixel_data"]["match"]
                
                shape_status = "✅ 一致" if shape_match else "❌ 不一致"
                self.tree.insert(self.pixel_group, "end", text="画像サイズ", 
                               values=(str(orig_shape), str(anon_shape), shape_status))
                
                pixel_status = "✅ 一致" if pixel_match else "❌ 不一致"
                self.tree.insert(self.pixel_group, "end", text="ピクセル値", 
                               values=("原本データ", "匿名化データ", pixel_status))
            
        except Exception as e:
            self.validator.log_message(f"ツリービュー更新中にエラー: {str(e)}")
    
    def draw_validation_graphs(self, summary):
        """検証結果をグラフで表示"""
        try:
            self.ax.clear()
            
            # 匿名化率を計算
            tags = self.validator.rules.must_anonymize_tags
            anonymized_rates = []
            
            for tag in tags:
                anonymized = summary['must_anonymize_stats'][tag]['anonymized']
                not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
                total = anonymized + not_anonymized
                
                if total > 0:
                    rate = anonymized / total * 100
                else:
                    rate = 0
                
                anonymized_rates.append(rate)
            
            # タグ名が長いので短縮
            short_tags = [tag[:15] + '...' if len(tag) > 15 else tag for tag in tags]
            
            # 棒グラフを描画
            bar_colors = ['green' if rate >= 95 else 'orange' if rate >= 80 else 'red' for rate in anonymized_rates]
            bars = self.ax.bar(short_tags, anonymized_rates, color=bar_colors)
            
            # グラフ設定
            self.ax.set_title('必須タグの匿名化率')
            self.ax.set_xlabel('タグ名')
            self.ax.set_ylabel('匿名化率 (%)')
            self.ax.set_ylim(0, 100)
            
            # X軸ラベルを回転
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            # 値を表示
            for bar in bars:
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', rotation=0)
            
            # 基準線を追加
            self.ax.axhline(y=95, color='green', linestyle='--', alpha=0.5)
            self.ax.axhline(y=80, color='orange', linestyle='--', alpha=0.5)
            
            self.ax.tick_params(axis='x', labelsize=8)
            self.figure.tight_layout()
            
            self.canvas.draw()
            
        except Exception as e:
            self.validator.log_message(f"グラフ描画中にエラー: {str(e)}")
    
    def compare_directories(self):
        """ディレクトリの基本的な比較を行う"""
        if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
            messagebox.showerror("エラー", "原本ディレクトリと匿名化ディレクトリを選択してください。")
            return
            
        # 最新のディレクトリパスを設定
        self.validator.original_dir = Path(self.original_dir_var.get())
        self.validator.anonymized_dir = Path(self.anonymized_dir_var.get())
        
        # バックグラウンドで比較処理を実行
        self.process_thread = threading.Thread(target=self._compare_directories_thread)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _compare_directories_thread(self):
        """ディレクトリ比較を実行するスレッド"""
        from rt_dicom_toolkit.utils.file_utils import compare_directory_structure
        
        try:
            # ディレクトリ比較を実行
            result = compare_directory_structure(
                self.validator.original_dir, 
                self.validator.anonymized_dir,
                self.validator.log_message
            )
            
            # 結果をUIに反映
            self.validator.summary_text.delete(1.0, tk.END)
            for line in result["summary"]:
                self.validator.update_summary(line)
            
            # グラフを描画
            if "modality_data" in result:
                self.validator.ax.clear()
                
                modalities = result["modality_data"]["modalities"]
                original_counts = result["modality_data"]["original_counts"]
                anonymized_counts = result["modality_data"]["anonymized_counts"]
                
                # グラフのプロット
                x = range(len(modalities))
                width = 0.35
                
                self.validator.ax.bar([i - width/2 for i in x], original_counts, width, label='原本')
                self.validator.ax.bar([i + width/2 for i in x], anonymized_counts, width, label='匿名化')
                
                self.validator.ax.set_title('モダリティ分布の比較')
                self.validator.ax.set_xlabel('モダリティ')
                self.validator.ax.set_ylabel('ファイル数')
                self.validator.ax.set_xticks(x)
                self.validator.ax.set_xticklabels(modalities)
                self.validator.ax.legend()
                
                self.validator.canvas.draw()
            
            # 詳細タブに切り替え
            self.notebook.select(3)
            
        except Exception as e:
            error_msg = f"ディレクトリ比較中にエラーが発生しました: {str(e)}"
            self.validator.log_message(error_msg)
            messagebox.showerror("エラー", error_msg)
    
    def start_validation(self):
        """検証処理を開始"""
        if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
            messagebox.showerror("エラー", "原本ディレクトリと匿名化ディレクトリを選択してください。")
            return
                
        original_dir = Path(self.original_dir_var.get())
        anonymized_dir = Path(self.anonymized_dir_var.get())
        
        if not original_dir.exists() or not anonymized_dir.exists():
            messagebox.showerror("エラー", "指定されたディレクトリが存在しません。")
            return
        
        # 前回の処理が終わっていない場合は処理しない
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            messagebox.showwarning("警告", "既に処理が実行中です。")
            return
        
        # 最新の設定を検証ツールに適用
        self.validator.original_dir = original_dir
        self.validator.anonymized_dir = anonymized_dir
        self.validator.report_dir = Path(self.report_dir_var.get())
        
        # ログテキストをクリア
        self.log_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # 処理開始
        self.status_var.set("検証を開始しています...")
        self.validator.log_message("検証処理を開始します...")
        
        # バックグラウンドで処理を実行
        self.process_thread = threading.Thread(
            target=self.run_validation_thread, 
            args=(original_dir, anonymized_dir)
        )
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def run_validation_thread(self, original_dir, anonymized_dir):
        """バックグラウンドで検証を実行するスレッド"""
        try:
            report = self.validator.validate_files(original_dir, anonymized_dir)
            
            if report:
                # サマリーテキストに結果を表示
                self.status_var.set("検証完了")
                self.validator.update_summary(report)
                
                # サマリータブに切り替え
                self.notebook.select(1)
                messagebox.showinfo("検証完了", "検証が完了しました。結果はサマリータブで確認できます。")
            else:
                self.status_var.set("検証エラー")
                messagebox.showerror("エラー", "検証中にエラーが発生しました。")
                
        except Exception as e:
            error_msg = f"検証スレッド内でエラーが発生しました: {str(e)}"
            self.validator.log_message(error_msg)
            self.status_var.set("エラーが発生しました")
            messagebox.showerror("エラー", error_msg)


def run_validator_gui():
    """検証ツールのGUIを実行"""
    root = tk.Tk()
    app = ValidatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_validator_gui()
