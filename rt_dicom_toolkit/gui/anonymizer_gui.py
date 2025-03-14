"""
匿名化ツールのGUIモジュール
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
from rt_dicom_toolkit.anonymizer import RTDicomAnonymizer

# パッケージとしてインストールされていない場合は相対パスを追加
if not "rt_dicom_toolkit" in sys.modules:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from anonymizer import RTDicomAnonymizer

class AnonymizerGUI:
    """匿名化ツールのGUIを提供するクラス"""
    
    def __init__(self, root):
        """
        匿名化ツールのGUIを初期化
        
        Args:
            root: TkinterのRootウィンドウ
        """
        self.root = root
        self.root.title("RT DICOM匿名化ツール")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # 匿名化ツールのインスタンスを作成
        self.anonymizer = RTDicomAnonymizer(self.root)
        
        # GUIを設定
        self.setup_gui()
        
    def setup_gui(self):
        """GUIコンポーネントの設定"""
        # 日本語フォント設定を適用
        configure_matplotlib_for_japanese()
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ディレクトリ選択部分
        dir_frame = ttk.LabelFrame(main_frame, text="ディレクトリ設定", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # 入力ディレクトリ
        ttk.Label(dir_frame, text="入力ディレクトリ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=str(self.anonymizer.input_dir))
        ttk.Entry(dir_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_input_dir).grid(row=0, column=2, pady=5)

        # 出力ディレクトリ
        ttk.Label(dir_frame, text="出力ディレクトリ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(self.anonymizer.output_dir))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_output_dir).grid(row=1, column=2, pady=5)

        # ログディレクトリ
        ttk.Label(dir_frame, text="ログディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_dir_var = tk.StringVar(value=str(self.anonymizer.log_dir))
        ttk.Entry(dir_frame, textvariable=self.log_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_log_dir).grid(row=2, column=2, pady=5)
        
        # 匿名化設定部分
        settings_frame = ttk.LabelFrame(main_frame, text="匿名化設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 匿名化レベル
        ttk.Label(settings_frame, text="匿名化レベル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        ttk.Radiobutton(settings_frame, text="完全匿名化", variable=self.anonymization_level, 
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="部分匿名化（日付・施設情報を保持）", variable=self.anonymization_level, 
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # プライベートタグの処理
        ttk.Label(settings_frame, text="プライベートタグ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.private_tags = tk.StringVar(value="remove")
        ttk.Radiobutton(settings_frame, text="すべて削除", variable=self.private_tags, 
                       value="remove").grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="保持", variable=self.private_tags, 
                       value="keep").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # UID管理
        ttk.Label(settings_frame, text="UID処理:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.uid_handling = tk.StringVar(value="consistent")
        ttk.Radiobutton(settings_frame, text="一貫性を保つ", variable=self.uid_handling, 
                       value="consistent").grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="すべて新規生成", variable=self.uid_handling, 
                       value="generate").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # ディレクトリ構造の保持
        ttk.Label(settings_frame, text="ディレクトリ構造:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.keep_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="元のディレクトリ構造を保持", 
                        variable=self.keep_structure).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 患者ID変換方法
        ttk.Label(settings_frame, text="患者ID変換:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.patient_id_method = tk.StringVar(value="hash")
        ttk.Radiobutton(settings_frame, text="ハッシュ化", variable=self.patient_id_method, 
                       value="hash").grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="連番（Patient_001など）", variable=self.patient_id_method, 
                       value="sequential").grid(row=4, column=2, sticky=tk.W, pady=5)
        
        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="匿名化実行", command=self.start_processing).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="ディレクトリ調査", command=self.check_directory).pack(side=tk.RIGHT, padx=5)
        
        # 進捗表示
        progress_frame = ttk.LabelFrame(main_frame, text="処理状況", padding="5")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 進捗バー
        self.progress_var = tk.DoubleVar()
        self.anonymizer.progress_var = self.progress_var
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, 
                                           mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # ログテキストエリア
        self.log_text = tk.Text(progress_frame, height=15, width=70, wrap=tk.WORD)
        self.anonymizer.log_text = self.log_text
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        self.anonymizer.status_var = self.status_var
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_input_dir(self):
        """入力ディレクトリを選択"""
        directory = filedialog.askdirectory(title="DICOMファイルがあるディレクトリを選択")
        if directory:
            self.input_dir_var.set(directory)
            self.anonymizer.input_dir = Path(directory)
            self.anonymizer.log_message(f"入力ディレクトリを設定: {directory}")
    
    def browse_output_dir(self):
        """出力ディレクトリを選択"""
        directory = filedialog.askdirectory(title="匿名化ファイルの保存先ディレクトリを選択")
        if directory:
            self.output_dir_var.set(directory)
            self.anonymizer.output_dir = Path(directory)
            self.anonymizer.log_message(f"出力ディレクトリを設定: {directory}")
    
    def browse_log_dir(self):
        """ログディレクトリを選択"""
        directory = filedialog.askdirectory(title="ログファイルの保存先ディレクトリを選択")
        if directory:
            self.log_dir_var.set(directory)
            self.anonymizer.log_dir = Path(directory)
            self.anonymizer.log_message(f"ログディレクトリを設定: {directory}")
    
    def check_directory(self):
        """ディレクトリの内容を調査するデバッグ用関数"""
        if not self.input_dir_var.get():
            messagebox.showerror("エラー", "入力ディレクトリを選択してください。")
            return
            
        input_dir = Path(self.input_dir_var.get())
        if not input_dir.exists():
            messagebox.showerror("エラー", "入力ディレクトリが存在しません。")
            return
            
        self.anonymizer.log_message(f"ディレクトリ '{input_dir}' の調査を開始します...")
        
        # バックグラウンドでディレクトリ調査を実行
        self.process_thread = threading.Thread(target=self._check_directory_thread, args=(input_dir,))
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _check_directory_thread(self, input_dir):
        """ディレクトリ調査を実行するスレッド"""
        from rt_dicom_toolkit.utils.file_utils import find_dicom_files
        from rt_dicom_toolkit.utils.dicom_utils import get_dicom_info
        
        try:
            # ディレクトリ内のDICOMファイルを検索
            files = find_dicom_files(input_dir)
            self.anonymizer.log_message(f"合計 {len(files)} 個のファイルが見つかりました")
            
            # DICOMファイルの情報を取得
            dicom_count = 0
            for file_path in files[:20]:  # 最初の20ファイルのみ詳細表示
                try:
                    info = get_dicom_info(file_path)
                    if info:
                        dicom_count += 1
                        modality = info.get('Modality', 'Unknown')
                        patient_id = info.get('PatientID', 'Unknown')
                        
                        # 患者IDをマスク処理
                        if patient_id != 'Unknown':
                            id_str = str(patient_id)
                            if len(id_str) > 4:
                                patient_id = id_str[:2] + "***" + id_str[-2:]
                            else:
                                patient_id = "***"
                        
                        self.anonymizer.log_message(f"DICOM: {file_path.name}, モダリティ: {modality}, 患者ID: {patient_id}")
                except Exception as e:
                    self.anonymizer.log_message(f"ファイル読み込みエラー {file_path.name}: {str(e)}")
            
            if len(files) > 20:
                self.anonymizer.log_message(f"... 他 {len(files) - 20} ファイル")
            
            self.anonymizer.log_message(f"調査完了: 合計 {len(files)} ファイル, うち {dicom_count} がDICOMファイル")
            
            if dicom_count == 0:
                self.anonymizer.log_message("警告: DICOMファイルが見つかりませんでした。")
                messagebox.showwarning("警告", "入力ディレクトリにDICOMファイルが見つかりませんでした。")
        
        except Exception as e:
            self.anonymizer.log_message(f"ディレクトリ調査中にエラー: {str(e)}")
    
    def start_processing(self):
        """匿名化処理を開始"""
        # 前回の処理が終わっていない場合は処理しない
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            messagebox.showwarning("警告", "既に処理が実行中です。")
            return
        
        # 入力チェック
        if not self.input_dir_var.get():
            messagebox.showerror("エラー", "入力ディレクトリを選択してください。")
            return
        
        if not self.output_dir_var.get():
            messagebox.showerror("エラー", "出力ディレクトリを選択してください。")
            return
        
        if not self.log_dir_var.get():
            messagebox.showerror("エラー", "ログディレクトリを選択してください。")
            return
        
        # 最新の設定をアノニマイザーに適用
        self.anonymizer.input_dir = Path(self.input_dir_var.get())
        self.anonymizer.output_dir = Path(self.output_dir_var.get())
        self.anonymizer.log_dir = Path(self.log_dir_var.get())
        self.anonymizer.anonymization_level = self.anonymization_level.get()
        self.anonymizer.private_tags = self.private_tags.get()
        self.anonymizer.uid_handling = self.uid_handling.get()
        self.anonymizer.keep_structure = self.keep_structure.get()
        self.anonymizer.patient_id_method = self.patient_id_method.get()
        
        # ログテキストをクリア
        self.log_text.delete(1.0, tk.END)
        
        # 処理開始
        self.status_var.set("処理を開始しています...")
        self.progress_var.set(0)
        self.anonymizer.log_message("処理スレッドを起動します...")
        
        # バックグラウンドで処理を実行
        self.process_thread = threading.Thread(target=self.anonymizer.process_directory)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # スレッドが起動したことを確認
        self.anonymizer.log_message(f"処理スレッド起動状態: {'実行中' if self.process_thread.is_alive() else '起動失敗'}")


def run_anonymizer_gui():
    """匿名化ツールのGUIを実行"""
    root = tk.Tk()
    app = AnonymizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_anonymizer_gui()
