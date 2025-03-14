import os
import sys
import argparse
import pydicom
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import re

class RTDicomValidator:
    def __init__(self, root=None):
        self.root = root
    
        # プログラムのあるディレクトリを取得
        script_dir = Path(__file__).parent.absolute()
    
        # 初期ディレクトリ設定
        self.original_dir = script_dir / 'input_dicom'
        self.anonymized_dir = script_dir / 'anonymous_dicom'
        self.report_dir = script_dir / 'validation_reports'
    
        # ディレクトリが存在しない場合は作成
        self.report_dir.mkdir(exist_ok=True)
    
        # ロガーの設定
        self.logger = self.setup_logger()
    
        # 検証ルールの設定
        self.define_validation_rules()
    
        if root:
            self.setup_gui()

        self.log_message("匿名化検証ツール初期化完了")
        self.log_message(f"原本ディレクトリ初期設定: {self.original_dir}")
        self.log_message(f"匿名化ディレクトリ初期設定: {self.anonymized_dir}")
        self.log_message(f"レポートディレクトリ初期設定: {self.report_dir}")
    
    def setup_logger(self):
        """ロガーをセットアップする"""
        logger = logging.getLogger("RTDicomValidator")
        logger.setLevel(logging.INFO)
        
        # 古いハンドラを削除（重複防止）
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def define_validation_rules(self):
        """検証ルールを定義する"""
        # 必ず匿名化されるべきタグのリスト
        self.must_anonymize_tags = [
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientAddress",
            "PatientTelephoneNumbers",
            "ReferringPhysicianName",
            "PhysiciansOfRecord",
            "PerformingPhysicianName",
            "InstitutionName",
            "InstitutionAddress",
            "StationName",
            "OperatorsName"
        ]
        
        # UIDタグのリスト
        self.uid_tags = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID"
        ]
        
        # データの構造が保持されるべきタグのリスト
        self.structure_tags = [
            "Modality",
            "SOPClassUID",
            "ImageType",
            "SamplesPerPixel",
            "PhotometricInterpretation",
            "BitsAllocated",
            "BitsStored",
            "HighBit",
            "PixelRepresentation",
            "NumberOfFrames"
        ]
        
        # 匿名化されるかどうかオプションのタグ
        self.optional_anonymize_tags = [
            "StudyDate",
            "SeriesDate",
            "AcquisitionDate",
            "ContentDate",
            "StudyTime",
            "SeriesTime",
            "AcquisitionTime",
            "ContentTime",
            "AccessionNumber",
            "StudyID",
            "SeriesNumber",
            "AcquisitionNumber",
            "InstanceNumber",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "DeviceSerialNumber"
        ]
        
        # RT構造特有のタグ
        self.rt_specific_tags = [
            "StructureSetLabel",
            "StructureSetName",
            "ROIName",
            "DoseComment",
            "PlanLabel"
        ]

    def setup_gui(self):
        """GUIのセットアップ"""
        self.root.title("RT DICOM匿名化検証ツール")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ディレクトリ選択部分
        dir_frame = ttk.LabelFrame(main_frame, text="ディレクトリ設定", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # 原本ディレクトリ
        ttk.Label(dir_frame, text="原本ディレクトリ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.original_dir_var = tk.StringVar(value=str(self.original_dir))
        ttk.Entry(dir_frame, textvariable=self.original_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_original_dir).grid(row=0, column=2, pady=5)
        
        # 匿名化ディレクトリ
        ttk.Label(dir_frame, text="匿名化ディレクトリ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.anonymized_dir_var = tk.StringVar(value=str(self.anonymized_dir))
        ttk.Entry(dir_frame, textvariable=self.anonymized_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_anonymized_dir).grid(row=1, column=2, pady=5)
        
        # レポートディレクトリ
        ttk.Label(dir_frame, text="レポートディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.report_dir_var = tk.StringVar(value=str(self.report_dir))
        ttk.Entry(dir_frame, textvariable=self.report_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_report_dir).grid(row=2, column=2, pady=5)
        
        # 検証設定部分
        settings_frame = ttk.LabelFrame(main_frame, text="検証設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 匿名化レベル
        ttk.Label(settings_frame, text="匿名化レベル確認:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        ttk.Radiobutton(settings_frame, text="完全匿名化", variable=self.anonymization_level, 
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="部分匿名化（日付・施設情報を保持）", variable=self.anonymization_level, 
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # プライベートタグの確認
        ttk.Label(settings_frame, text="プライベートタグ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.check_private_tags = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="プライベートタグの削除を確認", 
                        variable=self.check_private_tags).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # ファイル構造の保持確認
        ttk.Label(settings_frame, text="構造確認:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.check_file_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="ファイル構造の保持を確認", 
                       variable=self.check_file_structure).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # UID確認
        ttk.Label(settings_frame, text="UID確認:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.check_uid_changed = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="すべてのUIDが変更されていることを確認", 
                        variable=self.check_uid_changed).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 詳細レポート
        ttk.Label(settings_frame, text="レポートレベル:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.detailed_report = tk.BooleanVar(value=True)
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
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 詳細タブ
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="詳細")
        
        # ツリービュー
        self.tree = ttk.Treeview(details_frame)
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
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_original_dir(self):
        """原本ディレクトリを選択"""
        directory = filedialog.askdirectory(title="原本DICOMファイルがあるディレクトリを選択")
        if directory:
            self.original_dir_var.set(directory)
            self.log_message(f"原本ディレクトリを設定: {directory}")
    
    def browse_anonymized_dir(self):
        """匿名化ディレクトリを選択"""
        directory = filedialog.askdirectory(title="匿名化DICOMファイルがあるディレクトリを選択")
        if directory:
            self.anonymized_dir_var.set(directory)
            self.log_message(f"匿名化ディレクトリを設定: {directory}")
    
    def browse_report_dir(self):
        """レポートディレクトリを選択"""
        directory = filedialog.askdirectory(title="検証レポートの保存先ディレクトリを選択")
        if directory:
            self.report_dir_var.set(directory)
            self.log_message(f"レポートディレクトリを設定: {directory}")
    
    def log_message(self, message):
        """ログメッセージを表示"""
        try:
            if self.root:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            
            # 常にコンソールにもログを出力
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"ログ出力エラー: {str(e)}")
            
    def update_summary(self, message):
        """サマリーテキストを更新"""
        try:
            if self.root:
                self.summary_text.insert(tk.END, message + "\n")
                self.summary_text.see(tk.END)
                self.root.update_idletasks()
        except Exception as e:
            print(f"サマリー更新エラー: {str(e)}")
    
    def compare_directories(self):
        """ディレクトリの基本的な比較を行う"""
        try:
            if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
                messagebox.showerror("エラー", "原本ディレクトリと匿名化ディレクトリを選択してください。")
                return
                
            original_dir = Path(self.original_dir_var.get())
            anonymized_dir = Path(self.anonymized_dir_var.get())
            
            if not original_dir.exists() or not anonymized_dir.exists():
                messagebox.showerror("エラー", "指定されたディレクトリが存在しません。")
                return
                
            self.log_message(f"ディレクトリ比較: {original_dir} と {anonymized_dir}")
            
            # ファイル数をカウント
            original_files = []
            anonymized_files = []
            
            for root, _, files in os.walk(original_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # DICOMファイルとして読み込めるか確認
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        # SOPClassUIDがあるか確認
                        if hasattr(dcm, 'SOPClassUID'):
                            original_files.append(file_path)
                    except:
                        pass
            
            for root, _, files in os.walk(anonymized_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # DICOMファイルとして読み込めるか確認
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        # SOPClassUIDがあるか確認
                        if hasattr(dcm, 'SOPClassUID'):
                            anonymized_files.append(file_path)
                    except:
                        pass
            
            # 結果をログとサマリーに出力
            self.log_message(f"原本ディレクトリのDICOMファイル数: {len(original_files)}")
            self.log_message(f"匿名化ディレクトリのDICOMファイル数: {len(anonymized_files)}")
            
            self.summary_text.delete(1.0, tk.END)
            self.update_summary("=== ディレクトリ比較結果 ===")
            self.update_summary(f"原本ディレクトリ: {original_dir}")
            self.update_summary(f"匿名化ディレクトリ: {anonymized_dir}")
            self.update_summary(f"原本DICOMファイル数: {len(original_files)}")
            self.update_summary(f"匿名化DICOMファイル数: {len(anonymized_files)}")
            
            if len(original_files) == len(anonymized_files):
                self.update_summary("\n✅ ファイル数一致: 原本と匿名化ファイルの数が一致しています。")
            else:
                self.update_summary("\n⚠️ ファイル数不一致: 原本と匿名化ファイルの数が一致していません。")
                if len(original_files) > len(anonymized_files):
                    self.update_summary(f"  不足ファイル数: {len(original_files) - len(anonymized_files)}")
                else:
                    self.update_summary(f"  過剰ファイル数: {len(anonymized_files) - len(original_files)}")
            
            # モダリティの分布を取得
            original_modalities = {}
            anonymized_modalities = {}
            
            for file_path in original_files:
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True)
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                        if modality in original_modalities:
                            original_modalities[modality] += 1
                        else:
                            original_modalities[modality] = 1
                except:
                    pass
            
            for file_path in anonymized_files:
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True)
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                        if modality in anonymized_modalities:
                            anonymized_modalities[modality] += 1
                        else:
                            anonymized_modalities[modality] = 1
                except:
                    pass
            
            # モダリティ分布をグラフ化
            self.ax.clear()
            
            # データの準備
            modalities = list(set(list(original_modalities.keys()) + list(anonymized_modalities.keys())))
            original_counts = [original_modalities.get(m, 0) for m in modalities]
            anonymized_counts = [anonymized_modalities.get(m, 0) for m in modalities]
            
            # グラフのプロット
            x = np.arange(len(modalities))
            width = 0.35
            
            self.ax.bar(x - width/2, original_counts, width, label='原本')
            self.ax.bar(x + width/2, anonymized_counts, width, label='匿名化')
            
            self.ax.set_title('モダリティ分布の比較')
            self.ax.set_xlabel('モダリティ')
            self.ax.set_ylabel('ファイル数')
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(modalities)
            self.ax.legend()
            
            self.canvas.draw()
            
            # モダリティ分布をサマリーに追加
            self.update_summary("\n=== モダリティ分布 ===")
            for modality in modalities:
                orig_count = original_modalities.get(modality, 0)
                anon_count = anonymized_modalities.get(modality, 0)
                status = "✅" if orig_count == anon_count else "⚠️"
                self.update_summary(f"{status} {modality}: 原本 {orig_count}, 匿名化 {anon_count}")
            
            # ツリービューを更新
            self.tree.delete(*self.tree.get_children())
            
            # タグ分類ごとにグループを作成
            must_anonymize_group = self.tree.insert("", "end", text="必須匿名化タグ", open=True)
            uid_group = self.tree.insert("", "end", text="UIDタグ", open=True)
            structure_group = self.tree.insert("", "end", text="構造タグ", open=True)
            optional_group = self.tree.insert("", "end", text="オプション匿名化タグ", open=True)
            rt_group = self.tree.insert("", "end", text="RT特有タグ", open=True)
            
            # ディレクトリ比較の場合はダミーデータを表示
            for tag in self.must_anonymize_tags:
                self.tree.insert(must_anonymize_group, "end", text=tag, values=("(個別ファイル検証時に表示)", "(個別ファイル検証時に表示)", "-"))
            
            for tag in self.uid_tags:
                self.tree.insert(uid_group, "end", text=tag, values=("(個別ファイル検証時に表示)", "(個別ファイル検証時に表示)", "-"))
            
            for tag in self.structure_tags:
                self.tree.insert(structure_group, "end", text=tag, values=("(個別ファイル検証時に表示)", "(個別ファイル検証時に表示)", "-"))
            
            for tag in self.optional_anonymize_tags:
                self.tree.insert(optional_group, "end", text=tag, values=("(個別ファイル検証時に表示)", "(個別ファイル検証時に表示)", "-"))
            
            for tag in self.rt_specific_tags:
                self.tree.insert(rt_group, "end", text=tag, values=("(個別ファイル検証時に表示)", "(個別ファイル検証時に表示)", "-"))
            
            # 詳細タブに切り替え
            self.notebook.select(3)
            
        except Exception as e:
            error_msg = f"ディレクトリ比較中にエラーが発生しました: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            messagebox.showerror("エラー", error_msg)
    
    def compare_dicom_files(self, original_file, anonymized_file):
        """2つのDICOMファイルを比較して匿名化の状態を確認する"""
        try:
            # ファイルを読み込む
            original_dcm = pydicom.dcmread(str(original_file), force=True)
            anonymized_dcm = pydicom.dcmread(str(anonymized_file), force=True)
            
            results = {
                "must_anonymize": {},  # 必須匿名化タグの結果
                "uid_tags": {},        # UIDタグの結果
                "structure_tags": {},  # 構造タグの結果
                "optional_tags": {},   # オプションタグの結果
                "rt_specific_tags": {}, # RT特有タグの結果
                "private_tags": {      # プライベートタグの結果
                    "original_count": 0,
                    "anonymized_count": 0
                },
                "pixel_data": {        # ピクセルデータの比較結果
                    "original_shape": None,
                    "anonymized_shape": None,
                    "match": False
                }
            }
            
            # 必須匿名化タグを確認
            for tag in self.must_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # 匿名化されているかチェック
                anonymized = False
                if str(anonymized_value) == "N/A":
                    status = "削除済み"
                    anonymized = True
                elif str(anonymized_value) == "":
                    status = "空白化"
                    anonymized = True
                elif str(original_value) != str(anonymized_value):
                    status = "変更済み"
                    anonymized = True
                else:
                    status = "未変更"
                
                results["must_anonymize"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "anonymized": anonymized
                }
            
            # UIDタグを確認
            for tag in self.uid_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # UIDが変更されているかチェック
                changed = False
                if str(anonymized_value) == "N/A":
                    status = "削除済み"
                elif str(original_value) != str(anonymized_value):
                    status = "変更済み"
                    changed = True
                else:
                    status = "未変更"
                
                results["uid_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "changed": changed
                }
            
            # 構造タグを確認
            for tag in self.structure_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # 構造タグが保持されているかチェック
                preserved = False
                if str(original_value) == str(anonymized_value):
                    status = "保持"
                    preserved = True
                else:
                    status = "変更"
                
                results["structure_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "preserved": preserved
                }
            
            # オプションタグを確認
            for tag in self.optional_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # 匿名化設定に応じた確認
                if self.anonymization_level.get() == "full":
                    # 完全匿名化の場合は変更されるべき
                    changed = False
                    if str(anonymized_value) == "N/A":
                        status = "削除済み"
                        changed = True
                    elif str(original_value) != str(anonymized_value):
                        status = "変更済み"
                        changed = True
                    else:
                        status = "未変更"
                else:
                    # 部分匿名化の場合は保持されていてもよい
                    changed = True
                    if str(original_value) == str(anonymized_value):
                        status = "保持"
                    else:
                        status = "変更"
                
                results["optional_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "changed": changed
                }
            
            # RT特有タグを確認
            for tag in self.rt_specific_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # 臓器名は特殊処理（一部保持すべき）
                if tag == "ROIName":
                    status = "特殊処理"
                    # 特定の臓器名（例：heart, lung）は保持されるべき
                    if "N/A" not in str(original_value):
                        organs = ["lung", "heart", "liver", "kidney", "spinal", "brain"]
                        if any(organ in str(original_value).lower() for organ in organs):
                            if str(original_value) == str(anonymized_value):
                                status = "正しく保持"
                            else:
                                status = "保持すべき臓器名が変更"
                        else:
                            if str(original_value) != str(anonymized_value):
                                status = "正しく匿名化"
                            else:
                                status = "匿名化されていない"
                else:
                    # その他のRT特有タグは匿名化されるべき
                    if str(anonymized_value) == "N/A":
                        status = "削除済み"
                    elif str(original_value) != str(anonymized_value):
                        status = "変更済み"
                    else:
                        status = "未変更"
                
                results["rt_specific_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status
                }
            
            # プライベートタグの確認
            original_private_tags = [tag for tag in original_dcm.keys() if tag.is_private]
            anonymized_private_tags = [tag for tag in anonymized_dcm.keys() if tag.is_private]
            
            results["private_tags"]["original_count"] = len(original_private_tags)
            results["private_tags"]["anonymized_count"] = len(anonymized_private_tags)
            
            # ピクセルデータの比較（画像データがある場合）
            if hasattr(original_dcm, 'PixelData') and hasattr(anonymized_dcm, 'PixelData'):
                try:
                    original_pixel_array = original_dcm.pixel_array
                    anonymized_pixel_array = anonymized_dcm.pixel_array
                    
                    results["pixel_data"]["original_shape"] = original_pixel_array.shape
                    results["pixel_data"]["anonymized_shape"] = anonymized_pixel_array.shape
                    
                    # 形状が一致するか確認
                    if original_pixel_array.shape == anonymized_pixel_array.shape:
                        # ピクセル値が一致するか確認
                        if np.array_equal(original_pixel_array, anonymized_pixel_array):
                            results["pixel_data"]["match"] = True
                except Exception as e:
                    self.logger.warning(f"ピクセルデータの比較中にエラー: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"DICOM比較中にエラー: {e}")
            self.logger.error(traceback.format_exc())
            return None
            
    def validate_files(self, original_dir, anonymized_dir):
        """ディレクトリ内のファイルを検証する"""
        try:
            # 原本ディレクトリからDICOMファイルのリストを取得
            original_files = []
            for root, _, files in os.walk(original_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # DICOMファイルかどうかを確認
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        if hasattr(dcm, 'SOPClassUID'):
                            original_files.append(file_path)
                    except:
                        pass
            
            # 匿名化ディレクトリからDICOMファイルのリストを取得
            anonymized_files = []
            for root, _, files in os.walk(anonymized_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # DICOMファイルかどうかを確認
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        if hasattr(dcm, 'SOPClassUID'):
                            anonymized_files.append(file_path)
                    except:
                        pass
            
            self.log_message(f"原本DICOMファイル数: {len(original_files)}")
            self.log_message(f"匿名化DICOMファイル数: {len(anonymized_files)}")
            
            # 分析用の集計データ
            summary = {
                "total_files": len(original_files),
                "matched_files": 0,
                "must_anonymize_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.must_anonymize_tags},
                "uid_stats": {tag: {"changed": 0, "not_changed": 0} for tag in self.uid_tags},
                "structure_stats": {tag: {"preserved": 0, "not_preserved": 0} for tag in self.structure_tags},
                "private_tags_stats": {"removed": 0, "not_removed": 0},
                "modality_stats": {},
                "rt_specific_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rt_specific_tags},
                "patient_id_map": {},
            }
            
            # 詳細な結果保存用
            detailed_results = []
            
            # 匿名化前後のファイルをマッチングして検証
            progress_count = 0
            
            # マッチングの手法を選択（ここでは簡易的に同じ相対パスで比較）
            # 実際には、モダリティとシリーズ番号など、他の属性でマッチングする方が良い場合も
            original_files_map = {}
            
            # 原本ファイルをマップに追加
            for file_path in original_files:
                rel_path = file_path.relative_to(original_dir)
                original_files_map[str(rel_path)] = file_path
            
            # マッチングして検証
            for anon_file in anonymized_files:
                progress_count += 1
                
                # 進捗状況を更新
                if self.root:
                    progress = progress_count / len(anonymized_files) * 100
                    self.status_var.set(f"検証中... {progress_count}/{len(anonymized_files)} ({progress:.1f}%)")
                
                try:
                    # 相対パスでマッチング
                    rel_path = anon_file.relative_to(anonymized_dir)
                    
                    # マッチする原本ファイルを探す
                    if str(rel_path) in original_files_map:
                        orig_file = original_files_map[str(rel_path)]
                        
                        self.log_message(f"検証中: {rel_path}")
                        
                        # 2つのファイルを比較
                        results = self.compare_dicom_files(orig_file, anon_file)
                        
                        if results:
                            summary["matched_files"] += 1
                            
                            # モダリティ統計を更新
                            try:
                                orig_dcm = pydicom.dcmread(str(orig_file), force=True)
                                if hasattr(orig_dcm, 'Modality'):
                                    modality = orig_dcm.Modality
                                    if modality not in summary["modality_stats"]:
                                        summary["modality_stats"][modality] = 1
                                    else:
                                        summary["modality_stats"][modality] += 1
                            except:
                                pass
                            
                            # 必須匿名化タグの統計
                            for tag, info in results["must_anonymize"].items():
                                if info["anonymized"]:
                                    summary["must_anonymize_stats"][tag]["anonymized"] += 1
                                else:
                                    summary["must_anonymize_stats"][tag]["not_anonymized"] += 1
                            
                            # UIDタグの統計
                            for tag, info in results["uid_tags"].items():
                                if info["changed"]:
                                    summary["uid_stats"][tag]["changed"] += 1
                                else:
                                    summary["uid_stats"][tag]["not_changed"] += 1
                            
                            # 構造タグの統計
                            for tag, info in results["structure_tags"].items():
                                if info["preserved"]:
                                    summary["structure_stats"][tag]["preserved"] += 1
                                else:
                                    summary["structure_stats"][tag]["not_preserved"] += 1
                            
                            # プライベートタグの統計
                            if results["private_tags"]["anonymized_count"] == 0:
                                summary["private_tags_stats"]["removed"] += 1
                            else:
                                summary["private_tags_stats"]["not_removed"] += 1
                            
                            # 患者ID対応表の更新
                            if "PatientID" in results["must_anonymize"]:
                                orig_id = results["must_anonymize"]["PatientID"]["original"]
                                anon_id = results["must_anonymize"]["PatientID"]["anonymized"]
                                
                                if orig_id != "N/A" and anon_id != "N/A":
                                    summary["patient_id_map"][orig_id] = anon_id
                            
                            # 詳細結果を追加
                            if self.detailed_report.get():
                                detailed_results.append({
                                    "original_file": str(orig_file),
                                    "anonymized_file": str(anon_file),
                                    "results": results
                                })
                            
                            # ツリービューの更新（最新のファイル結果を表示）
                            if self.root:
                                self.update_treeview(results)
                    else:
                        self.log_message(f"マッチするファイルなし: {rel_path}")
                
                except Exception as e:
                    self.log_message(f"ファイル検証中にエラー: {str(e)}")
                    self.logger.error(traceback.format_exc())
            
            # サマリーレポートを生成
            report = self.generate_summary_report(summary)
            
            # 詳細レポートを保存
            if self.detailed_report.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                detailed_report_path = Path(self.report_dir_var.get()) / f"detailed_validation_report_{timestamp}.json"
                
                with open(detailed_report_path, 'w', encoding='utf-8') as f:
                    json.dump(detailed_results, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"詳細レポート保存完了: {detailed_report_path}")
            
            # グラフを描画
            self.draw_validation_graphs(summary)
            
            return report
            
        except Exception as e:
            error_msg = f"検証処理中にエラーが発生しました: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            return None
    
    def update_treeview(self, results):
        """ツリービューを結果で更新する"""
        try:
            self.tree.delete(*self.tree.get_children())
            
            # タグ分類ごとにグループを作成
            must_anonymize_group = self.tree.insert("", "end", text="必須匿名化タグ", open=True)
            uid_group = self.tree.insert("", "end", text="UIDタグ", open=True)
            structure_group = self.tree.insert("", "end", text="構造タグ", open=True)
            optional_group = self.tree.insert("", "end", text="オプション匿名化タグ", open=True)
            rt_group = self.tree.insert("", "end", text="RT特有タグ", open=True)
            
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
                
                self.tree.insert(must_anonymize_group, "end", text=tag, values=(orig_value, anon_value, status))
            
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
                
                self.tree.insert(uid_group, "end", text=tag, values=(orig_value, anon_value, status))
            
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
                
                self.tree.insert(structure_group, "end", text=tag, values=(orig_value, anon_value, status))
            
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
                
                self.tree.insert(optional_group, "end", text=tag, values=(orig_value, anon_value, status))
            
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
                
                self.tree.insert(rt_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # プライベートタグの情報を追加
            private_group = self.tree.insert("", "end", text="プライベートタグ", open=True)
            original_count = results["private_tags"]["original_count"]
            anonymized_count = results["private_tags"]["anonymized_count"]
            
            status = "✅ すべて削除" if anonymized_count == 0 else f"❌ {anonymized_count}個残存"
            self.tree.insert(private_group, "end", text="プライベートタグ数", 
                           values=(f"{original_count}個", f"{anonymized_count}個", status))
            
            # ピクセルデータの情報を追加（あれば）
            if results["pixel_data"]["original_shape"] is not None:
                pixel_group = self.tree.insert("", "end", text="画像データ", open=True)
                orig_shape = results["pixel_data"]["original_shape"]
                anon_shape = results["pixel_data"]["anonymized_shape"]
                
                shape_match = orig_shape == anon_shape
                pixel_match = results["pixel_data"]["match"]
                
                shape_status = "✅ 一致" if shape_match else "❌ 不一致"
                self.tree.insert(pixel_group, "end", text="画像サイズ", 
                               values=(str(orig_shape), str(anon_shape), shape_status))
                
                pixel_status = "✅ 一致" if pixel_match else "❌ 不一致"
                self.tree.insert(pixel_group, "end", text="ピクセル値", 
                               values=("原本データ", "匿名化データ", pixel_status))
            
        except Exception as e:
            self.log_message(f"ツリービュー更新中にエラー: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def generate_summary_report(self, summary):
        """検証結果のサマリーレポートを生成"""
        try:
            report = []
            
            report.append("=== 匿名化検証サマリーレポート ===")
            report.append(f"検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"総ファイル数: {summary['total_files']}")
            report.append(f"マッチングファイル数: {summary['matched_files']}")
            report.append("")
            
            # 全体の匿名化状況
            total_must_tags = len(self.must_anonymize_tags) * summary['matched_files']
            total_anonymized = sum(summary['must_anonymize_stats'][tag]['anonymized'] for tag in self.must_anonymize_tags)
            
            if total_must_tags > 0:
                anonymization_rate = total_anonymized / total_must_tags * 100
                report.append(f"必須タグ匿名化率: {anonymization_rate:.1f}%")
                
                if anonymization_rate >= 95:
                    report.append("✅ 匿名化状況: 良好（95%以上のタグが正しく匿名化されています）")
                elif anonymization_rate >= 80:
                    report.append("⚠️ 匿名化状況: 要確認（80-95%のタグが匿名化されています）")
                else:
                    report.append("❌ 匿名化状況: 不十分（匿名化率が80%未満です）")
            
            report.append("")
            report.append("--- 必須匿名化タグの状況 ---")
            for tag in self.must_anonymize_tags:
                anonymized = summary['must_anonymize_stats'][tag]['anonymized']
                not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
                total = anonymized + not_anonymized
                
                if total > 0:
                    rate = anonymized / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {anonymized}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- UIDタグの変更状況 ---")
            for tag in self.uid_tags:
                changed = summary['uid_stats'][tag]['changed']
                not_changed = summary['uid_stats'][tag]['not_changed']
                total = changed + not_changed
                
                if total > 0:
                    rate = changed / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {changed}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- 構造タグの保持状況 ---")
            for tag in self.structure_tags:
                preserved = summary['structure_stats'][tag]['preserved']
                not_preserved = summary['structure_stats'][tag]['not_preserved']
                total = preserved + not_preserved
                
                if total > 0:
                    rate = preserved / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {preserved}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- プライベートタグの削除状況 ---")
            removed = summary['private_tags_stats']['removed']
            not_removed = summary['private_tags_stats']['not_removed']
            total = removed + not_removed
            
            if total > 0:
                rate = removed / total * 100
                status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                report.append(f"{status} プライベートタグ削除: {removed}/{total} ({rate:.1f}%)")
            
            # モダリティ分布
            report.append("")
            report.append("--- モダリティ分布 ---")
            for modality, count in summary['modality_stats'].items():
                report.append(f"{modality}: {count}ファイル")
            
            # 患者ID対応表
            if summary['patient_id_map']:
                report.append("")
                report.append("--- 患者ID対応表 （最大10件表示） ---")
                count = 0
                for orig_id, anon_id in summary['patient_id_map'].items():
                    # 患者IDの一部をマスク
                    if len(orig_id) > 4:
                        masked_id = orig_id[:2] + "***" + orig_id[-2:]
                    else:
                        masked_id = "***"
                        
                    report.append(f"{masked_id} → {anon_id}")
                    count += 1
                    if count >= 10:
                        report.append(f"...他 {len(summary['patient_id_map']) - 10} 件")
                        break
            
            # レポートをファイルに保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = Path(self.report_dir_var.get()) / f"validation_summary_{timestamp}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))
            
            self.log_message(f"サマリーレポート保存完了: {report_path}")
            
            return "\n".join(report)
            
        except Exception as e:
            self.log_message(f"レポート生成中にエラー: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
    
    def draw_validation_graphs(self, summary):
        """検証結果をグラフで表示"""
        try:
            self.ax.clear()
            
            # 匿名化率を計算
            tags = self.must_anonymize_tags
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
            self.log_message(f"グラフ描画中にエラー: {str(e)}")
            self.logger.error(traceback.format_exc())
    
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
        
        # ログテキストをクリア
        self.log_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # 処理開始
        self.status_var.set("検証を開始しています...")
        self.log_message("検証処理を開始します...")
        
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
            report = self.validate_files(original_dir, anonymized_dir)
            
            if report:
                # サマリーテキストに結果を表示
                self.status_var.set("検証完了")
                self.update_summary(report)
                
                # サマリータブに切り替え
                if self.root:
                    self.notebook.select(1)
                    messagebox.showinfo("検証完了", "検証が完了しました。結果はサマリータブで確認できます。")
            else:
                self.status_var.set("検証エラー")
                messagebox.showerror("エラー", "検証中にエラーが発生しました。")
                
        except Exception as e:
            error_msg = f"検証スレッド内でエラーが発生しました: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            self.status_var.set("エラーが発生しました")
            messagebox.showerror("エラー", error_msg)


def main():
    """メイン関数"""
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description='RT DICOM匿名化検証プログラム')
    parser.add_argument('--nogui', action='store_true', help='GUIを使用せずにコマンドラインで実行')
    parser.add_argument('--original', help='原本DICOMディレクトリのパス')
    parser.add_argument('--anonymized', help='匿名化DICOMディレクトリのパス')
    parser.add_argument('--report', help='レポート出力ディレクトリのパス')
    args = parser.parse_args()
    
    if args.nogui:
        # コマンドラインモード
        print("コマンドラインモードで実行中...")
        validator = RTDicomValidator()
        
        # コマンドライン引数があれば設定
        if args.original:
            validator.original_dir = Path(args.original)
        if args.anonymized:
            validator.anonymized_dir = Path(args.anonymized)
        if args.report:
            validator.report_dir = Path(args.report)
            
        report = validator.validate_files(validator.original_dir, validator.anonymized_dir)
        if report:
            print("\n" + report)
    else:
        # GUIモード
        print("GUIモードで実行中...")
        root = tk.Tk()
        app = RTDicomValidator(root)
        root.mainloop()

if __name__ == '__main__':
    print("検証プログラムを開始します...")
    main()