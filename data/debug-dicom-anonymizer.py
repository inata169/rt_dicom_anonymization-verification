import os
import sys
import argparse
import pydicom
import hashlib
import uuid
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import logging
from pydicom.uid import generate_uid

class RTDicomAnonymizer:
    def __init__(self, root=None):
        self.root = root
    
        # プログラムのあるディレクトリを取得
        script_dir = Path(__file__).parent.absolute()
    
        # 初期ディレクトリ設定（プログラムと同じ階層を優先）
        self.input_dir = script_dir / 'input_dicom'
        self.output_dir = script_dir / 'anonymous_dicom'
        self.log_dir = script_dir / 'logs'
    
        # ディレクトリが存在しない場合は作成
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
    
        # 匿名化プロファイルの設定
        self.define_anonymization_profile()
    
        # ロガーの設定
        self.logger = self.setup_logger()
    
        if root:
            self.setup_gui()

        self.log_message("匿名化ツール初期化完了")
        self.log_message(f"入力ディレクトリ初期設定: {self.input_dir}")
        self.log_message(f"出力ディレクトリ初期設定: {self.output_dir}")
        self.log_message(f"ログディレクトリ初期設定: {self.log_dir}")
    
    def setup_logger(self):
        """ロガーをセットアップする"""
        logger = logging.getLogger("RTDicomAnonymizer")
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
    
    def define_anonymization_profile(self):
        """匿名化プロファイルの定義"""
        # キーは属性のタグ、値は変換方法（値または関数）
        self.anonymization_profile = {
            # 基本的な患者情報
            "PatientName": "ANONYMOUS",
            "PatientID": lambda x: self.generate_anonymous_id(x),
            "PatientBirthDate": "19000101",
            "PatientSex": "O",  # Other
            "PatientAge": "000Y",
            "PatientWeight": "",
            "PatientAddress": "",
            "PatientTelephoneNumbers": "",
            
            # 研究・施設情報
            "StudyID": lambda x: hashlib.md5(str(x).encode()).hexdigest()[:8],
            "AccessionNumber": "",
            "InstitutionName": "ANONYMOUS_INSTITUTION",
            "InstitutionAddress": "",
            "ReferringPhysicianName": "ANONYMOUS_PHYSICIAN",
            "PhysiciansOfRecord": "",
            "PerformingPhysicianName": "",
            "OperatorsName": "",
            
            # 識別子
            "StudyInstanceUID": lambda x: generate_uid(),
            "SeriesInstanceUID": lambda x: generate_uid(),
            "SOPInstanceUID": lambda x: generate_uid(),
            "FrameOfReferenceUID": lambda x: generate_uid(),
            
            # 日付と時刻（日付の年を2000年に設定、月日はそのまま）
            "StudyDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "SeriesDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "AcquisitionDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "ContentDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "StudyTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "SeriesTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "AcquisitionTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "ContentTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            
            # その他の識別情報
            "DeviceSerialNumber": "",
            "StationName": "ANONYMOUS_STATION",
            "ManufacturerModelName": "",  # メーカー情報はそのまま残してもよい
            
            # RT特有の属性
            "StructureSetLabel": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
            "StructureSetName": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
            "ROIName": lambda x: f"ROI_{str(x)[-10:]}" if not any(organ in str(x).lower() for organ in ["lung", "heart", "liver", "kidney", "spinal", "brain"]) else str(x),
            "DoseComment": "ANONYMIZED",
            "PlanLabel": lambda x: f"ANONYMOUS_PLAN_{str(x)[-5:]}",
        }
    
    def generate_anonymous_id(self, original_id):
        """
        オリジナルの患者IDから9で始まる7桁の匿名化IDを生成する
        同じ患者には常に同じIDを割り当てる
        
        Args:
            original_id: 元の患者ID
            
        Returns:
            9で始まる7桁の数字ID文字列
        """
        # 患者IDの一貫性を保つためのマッピングを使用
        if not hasattr(self, 'patient_id_map'):
            self.patient_id_map = {}
            
        # すでに変換済みの場合はそれを返す
        if str(original_id) in self.patient_id_map:
            return self.patient_id_map[str(original_id)]
        
        # 次の連番IDを生成（9000001からスタート）
        if not hasattr(self, 'next_patient_id'):
            self.next_patient_id = 9000001
        else:
            self.next_patient_id += 1
            
        # 9999999を超えないようにする
        if self.next_patient_id > 9999999:
            # 万が一ID枯渇した場合は先頭の9以外を使用（通常はここに到達しない）
            # 最後の6桁をハッシュ化して使用
            hash_id = int(hashlib.md5(str(original_id).encode()).hexdigest(), 16) % 1000000
            new_id = f"9{hash_id:06d}"
        else:
            new_id = str(self.next_patient_id)
            
        # マッピングを保存
        self.patient_id_map[str(original_id)] = new_id
        
        return new_id
    
    def setup_gui(self):
        """GUIのセットアップ"""
        self.root.title("RT DICOM匿名化ツール")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ディレクトリ選択部分
        dir_frame = ttk.LabelFrame(main_frame, text="ディレクトリ設定", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # 入力ディレクトリ
        ttk.Label(dir_frame, text="入力ディレクトリ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=str(self.input_dir))
        ttk.Entry(dir_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_input_dir).grid(row=0, column=2, pady=5)

        # 出力ディレクトリ
        ttk.Label(dir_frame, text="出力ディレクトリ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_output_dir).grid(row=1, column=2, pady=5)

        # ログディレクトリ
        ttk.Label(dir_frame, text="ログディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_dir_var = tk.StringVar(value=str(self.log_dir))
        ttk.Entry(dir_frame, textvariable=self.log_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="参照...", command=self.browse_log_dir).grid(row=2, column=2, pady=5)
        
        # 匿名化設定部分
        settings_frame = ttk.LabelFrame(main_frame, text="匿名化設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 匿名化の詳細度を選択
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
        
        # ファイル構造の保持
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
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # ログテキストエリア
        self.log_text = tk.Text(progress_frame, height=15, width=70, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_directory(self):
        """ディレクトリの内容を調査するデバッグ用関数"""
        if not self.input_dir_var.get():
            messagebox.showerror("エラー", "入力ディレクトリを選択してください。")
            return
            
        input_dir = Path(self.input_dir_var.get())
        if not input_dir.exists():
            messagebox.showerror("エラー", "入力ディレクトリが存在しません。")
            return
            
        self.log_message(f"ディレクトリ '{input_dir}' の調査を開始します...")
        
        # ディレクトリ内のファイル一覧を取得
        file_count = 0
        dicom_count = 0
        
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = Path(root) / file
                file_count += 1
                
                try:
                    # DICOMファイルとして読み込めるか確認
                    dcm = pydicom.dcmread(str(file_path), force=False)
                    dicom_count += 1
                    
                    # モダリティ情報があれば表示
                    modality = "Unknown"
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                    
                    # 患者ID情報があれば表示（一部マスク）
                    patient_id = "Unknown"
                    if hasattr(dcm, 'PatientID') and dcm.PatientID:
                        id_str = str(dcm.PatientID)
                        if len(id_str) > 4:
                            patient_id = id_str[:2] + "***" + id_str[-2:]
                        else:
                            patient_id = "***"
                    
                    self.log_message(f"DICOM: {file_path.name}, モダリティ: {modality}, 患者ID: {patient_id}")
                    
                except:
                    pass
        
        self.log_message(f"調査完了: 合計 {file_count} ファイル, うち {dicom_count} がDICOMファイル")
        
        if dicom_count == 0:
            self.log_message("警告: DICOMファイルが見つかりませんでした。")
            messagebox.showwarning("警告", "入力ディレクトリにDICOMファイルが見つかりませんでした。")
    
    def browse_input_dir(self):
        """入力ディレクトリを選択"""
        directory = filedialog.askdirectory(title="DICOMファイルがあるディレクトリを選択")
        if directory:
            self.input_dir_var.set(directory)
            self.log_message(f"入力ディレクトリを設定: {directory}")
    
    def browse_output_dir(self):
        """出力ディレクトリを選択"""
        directory = filedialog.askdirectory(title="匿名化ファイルの保存先ディレクトリを選択")
        if directory:
            self.output_dir_var.set(directory)
            self.log_message(f"出力ディレクトリを設定: {directory}")
    
    def browse_log_dir(self):
        """ログディレクトリを選択"""
        directory = filedialog.askdirectory(title="ログファイルの保存先ディレクトリを選択")
        if directory:
            self.log_dir_var.set(directory)
            self.log_message(f"ログディレクトリを設定: {directory}")
    
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
    
    def get_modified_anonymization_profile(self):
        """
        現在のGUI設定に基づいて匿名化プロファイルを調整する
        """
        profile = self.anonymization_profile.copy()
        
        # GUIが存在する場合、そこから設定を取得
        if self.root:
            # 匿名化レベルに応じた設定
            if self.anonymization_level.get() == "partial":
                # 日付と施設情報を保持する場合
                for key in ["StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
                          "StudyTime", "SeriesTime", "AcquisitionTime", "ContentTime",
                          "InstitutionName", "StationName"]:
                    if key in profile:
                        del profile[key]
            
            # UID処理
            if self.uid_handling.get() == "consistent":
                # 一貫性を保つためのUID管理を実装
                # (ここでは単純にハッシュベースの一貫したUIDを生成)
                uid_map = {}
                for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"]:
                    if uid_tag in profile:
                        profile[uid_tag] = lambda x, tag=uid_tag: uid_map.setdefault(
                            f"{tag}_{x}", generate_uid())
            
            # 患者ID変換方法
            if self.patient_id_method.get() == "sequential":
                # 患者IDを連番で管理
                self.patient_counter = 0
                def sequential_id(x):
                    self.patient_counter += 1
                    return f"Patient_{self.patient_counter:03d}"
                profile["PatientID"] = sequential_id
        
        return profile

    def anonymize_dicom(self, dcm, anonymization_profile, remove_private_tags=True):
        """
        DICOMファイルを匿名化する
        
        Args:
            dcm (pydicom.dataset.FileDataset): 匿名化するDICOMデータセット
            anonymization_profile (dict): 匿名化プロファイル
            remove_private_tags (bool): プライベートタグを削除するかどうか
            
        Returns:
            dict: 変更されたタグとその値のディクショナリ
        """
        self.log_message(f"匿名化処理を開始: {dcm.filename if hasattr(dcm, 'filename') else 'Unknown'}")
        changes = {}
        
        # プライベートタグの処理
        if remove_private_tags:
            private_tags = [tag for tag in dcm.keys() if tag.is_private]
            for tag in private_tags:
                if tag in dcm:
                    del dcm[tag]
            
            self.log_message(f"{len(private_tags)}個のプライベートタグを削除しました")
        
        # 匿名化プロファイルに従ってタグを処理
        processed_tags = 0
        for tag_name, replacement in anonymization_profile.items():
            # タグが存在するか確認
            if hasattr(dcm, tag_name):
                try:
                    original_value = getattr(dcm, tag_name)
                    
                    # 置換値が関数の場合は実行し、そうでない場合はそのまま使用
                    if callable(replacement):
                        try:
                            new_value = replacement(original_value)
                        except Exception as e:
                            self.logger.warning(f"タグ {tag_name} の処理中にエラーが発生: {e}")
                            continue
                    else:
                        new_value = replacement
                    
                    # 値を設定
                    try:
                        setattr(dcm, tag_name, new_value)
                        changes[tag_name] = {
                            "元の値": str(original_value),
                            "変更後の値": str(new_value)
                        }
                        processed_tags += 1
                    except Exception as e:
                        self.logger.warning(f"タグ {tag_name} の値設定中にエラーが発生: {e}")
                except Exception as e:
                    self.logger.warning(f"タグ {tag_name} の処理中にエラーが発生: {e}")
        
        self.log_message(f"{processed_tags}個のタグを匿名化しました")
        return changes
    
    def process_directory(self):
        """
        指定されたディレクトリ内のDICOMファイルを全て匿名化し、変更内容をログファイルに記録する
        """
        try:
            self.log_message("処理を開始します...")
            
            # 入力・出力ディレクトリのパスを設定
            if self.root:
                input_dir = Path(self.input_dir_var.get())
                output_dir = Path(self.output_dir_var.get())
                log_dir = Path(self.log_dir_var.get())
                keep_structure = self.keep_structure.get()
                remove_private_tags = self.private_tags.get() == "remove"
                
                # ディレクトリが選択されているか確認
                if not input_dir.exists():
                    error_msg = f"入力ディレクトリが存在しません: {input_dir}"
                    self.log_message(error_msg)
                    messagebox.showerror("エラー", error_msg)
                    return
                    
                self.log_message(f"入力ディレクトリ: {input_dir}")
                self.log_message(f"出力ディレクトリ: {output_dir}")
                self.log_message(f"ログディレクトリ: {log_dir}")
            else:
                input_dir = Path('input_dicom')
                output_dir = Path('anonymous_dicom')
                log_dir = Path('logs')
                keep_structure = True
                remove_private_tags = True
            
            # 出力ディレクトリとログディレクトリが存在しない場合は作成
            output_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)
            
            self.log_message(f"出力ディレクトリを作成/確認: {output_dir}")
            self.log_message(f"ログディレクトリを作成/確認: {log_dir}")
            
            # UID対応マップの初期化
            self.uid_map = {}
            
            # 患者IDマッピングの辞書
            self.patient_id_map = {}
            self.patient_counter = 0
            
            # ログファイルのパスを設定
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"rt_anonymization_log_{timestamp}.txt"
            summary_path = log_dir / f"rt_anonymization_summary_{timestamp}.json"
            
            self.log_message(f"ログファイル: {log_path}")
            self.log_message(f"サマリーファイル: {summary_path}")
            
            # ファイルハンドラーをロガーに追加
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # 処理サマリー
            summary = {
                "処理開始時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "処理ファイル数": 0,
                "成功": 0,
                "スキップ": 0,
                "エラー": 0,
                "ファイル詳細": [],
                "患者ID対応表": {}
            }
            
            # 対象ファイルのリストを取得（サブディレクトリを含む）
            self.log_message("ファイルの検索を開始...")
            dicom_files = []
            for root, _, files in os.walk(input_dir):
                for file in files:
                    file_path = Path(root) / file
                    dicom_files.append(file_path)
            
            total_files = len(dicom_files)
            self.log_message(f"検索完了: {total_files}ファイルが見つかりました")
            
            if total_files == 0:
                self.log_message("処理対象のファイルが見つかりません。")
                if self.root:
                    self.status_var.set("ファイルが見つかりません")
                    messagebox.showinfo("情報", "入力ディレクトリにファイルが見つかりません。")
                return
            
            # 匿名化プロファイルを取得
            anonymization_profile = self.get_modified_anonymization_profile()
            self.log_message("匿名化プロファイルを設定しました")
            
            # 入力ディレクトリ内のファイルを処理
            for i, file_path in enumerate(dicom_files):
                if file_path.is_file():
                    summary["処理ファイル数"] += 1
                    
                    # 進捗状況を更新
                    progress = (i + 1) / total_files * 100
                    if self.root:
                        self.progress_var.set(progress)
                        self.status_var.set(f"処理中... {i+1}/{total_files} ({progress:.1f}%)")
                    
                    self.log_message(f"処理中 ({i+1}/{total_files}): {file_path.name}")
                    
                    try:
                        # DICOMファイルかどうかを確認
                        try:
                            dcm = pydicom.dcmread(str(file_path), force=True)
                            
                            # ファイルの種類を特定
                            modality = "Unknown"
                            file_type = "Unknown"
                            if hasattr(dcm, 'Modality'):
                                modality = dcm.Modality
                                if modality == "RTPLAN":
                                    file_type = "放射線治療計画"
                                elif modality == "RTDOSE":
                                    file_type = "線量分布"
                                elif modality == "RTSTRUCT":
                                    file_type = "臓器輪郭"
                                elif modality == "CT" or modality == "RTIMAGE":
                                    file_type = "CT画像"
                            
                            self.log_message(f"ファイル種類: {file_type} (モダリティ: {modality})")
                            
                            # 出力ファイルパスを生成
                            if keep_structure:
                                # 元のディレクトリ構造を保持
                                rel_path = file_path.relative_to(input_dir)
                                output_path = output_dir / rel_path
                                output_path.parent.mkdir(parents=True, exist_ok=True)
                            else:
                                # フラットなディレクトリ構造
                                output_path = output_dir / file_path.name
                            
                            self.log_message(f"出力先: {output_path}")
                            
                            # 患者IDのマッピングを記録（存在する場合）
                            if hasattr(dcm, 'PatientID') and dcm.PatientID:
                                original_id = dcm.PatientID
                                if original_id not in self.patient_id_map:
                                    # 9で始まる7桁の数字を生成
                                    new_id = self.generate_anonymous_id(original_id)
                                    
                                    self.patient_id_map[original_id] = new_id
                                    summary["患者ID対応表"][original_id] = new_id
                                    
                                    # 患者IDの一部をマスク処理して表示
                                    if len(str(original_id)) > 4:
                                        masked_id = str(original_id)[:2] + "***" + str(original_id)[-2:]
                                    else:
                                        masked_id = "***"
                                    
                                    self.log_message(f"患者ID対応: {masked_id} → {new_id}")
                                
                                # 匿名化プロファイルに患者IDマッピングを反映
                                # 既に定義したgenerate_anonymous_idメソッドを使用するように変更
                                anonymization_profile["PatientID"] = lambda x: self.generate_anonymous_id(str(x))
                            
                            # ファイルを匿名化して保存
                            msg = f'処理中: {file_path.name} (タイプ: {file_type})'
                            self.log_message(msg)
                            
                            # DICOMファイルを匿名化
                            changes = self.anonymize_dicom(dcm, anonymization_profile, remove_private_tags)
                            
                            # 匿名化されたDICOMを保存
                            try:
                                dcm.save_as(str(output_path))
                                self.log_message(f"匿名化ファイル保存完了: {output_path.name}")
                            except Exception as save_error:
                                self.log_message(f"ファイル保存エラー: {str(save_error)}")
                                raise save_error
                            
                            summary["ファイル詳細"].append({
                                "ファイル名": file_path.name,
                                "タイプ": file_type,
                                "状態": "成功",
                                "変更フィールド": changes
                            })
                            summary["成功"] += 1
                            
                        except pydicom.errors.InvalidDicomError:
                            error_msg = f'DICOMファイルではないためスキップ: {file_path.name}'
                            self.log_message(error_msg)
                            summary["ファイル詳細"].append({
                                "ファイル名": file_path.name,
                                "タイプ": "非DICOM",
                                "状態": "スキップ"
                            })
                            summary["スキップ"] += 1
                            
                    except Exception as e:
                        error_msg = f'処理エラー {file_path.name}: {str(e)}'
                        self.log_message(error_msg)
                        self.logger.error(traceback.format_exc())
                        summary["ファイル詳細"].append({
                            "ファイル名": file_path.name,
                            "タイプ": "エラー",
                            "状態": "失敗",
                            "エラー詳細": str(e)
                        })
                        summary["エラー"] += 1
            
            # 処理終了時間を記録
            summary["処理終了時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # JSON形式のサマリーファイルを作成
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            msg = f"\n処理完了！"
            self.log_message(msg)
            msg = f"ログファイル: {log_path}"
            self.log_message(msg)
            msg = f"サマリーファイル: {summary_path}"
            self.log_message(msg)
            
            if self.root:
                self.status_var.set(f"処理完了: 成功 {summary['成功']}, スキップ {summary['スキップ']}, エラー {summary['エラー']}")
                messagebox.showinfo("処理完了", 
                               f"処理が完了しました。\n\n"
                               f"成功: {summary['成功']}\n"
                               f"スキップ: {summary['スキップ']}\n"
                               f"エラー: {summary['エラー']}\n\n"
                               f"ログファイル: {log_path}")
            
            # ファイルハンドラーを削除
            self.logger.removeHandler(file_handler)
            
        except Exception as e:
            error_msg = f"予期せぬエラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            if self.root:
                self.status_var.set("エラーが発生しました")
                messagebox.showerror("エラー", error_msg)

    def start_processing(self):
        """バックグラウンドで処理を開始"""
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
        
        # ログテキストをクリア
        self.log_text.delete(1.0, tk.END)
        
        # 処理開始
        self.status_var.set("処理を開始しています...")
        self.progress_var.set(0)
        self.log_message("処理スレッドを起動します...")
        
        # バックグラウンドで処理を実行
        self.process_thread = threading.Thread(target=self.process_directory)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # スレッドが起動したことを確認
        self.log_message(f"処理スレッド起動状態: {'実行中' if self.process_thread.is_alive() else '起動失敗'}")


def main():
    """メイン関数"""
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description='RT DICOM匿名化プログラム')
    parser.add_argument('--nogui', action='store_true', help='GUIを使用せずにコマンドラインで実行')
    parser.add_argument('--input', help='入力ディレクトリのパス')
    parser.add_argument('--output', help='出力ディレクトリのパス')
    parser.add_argument('--log', help='ログディレクトリのパス')
    args = parser.parse_args()
    
    if args.nogui:
        # コマンドラインモード
        print("コマンドラインモードで実行中...")
        anonymizer = RTDicomAnonymizer()
        
        # コマンドライン引数があれば設定
        if args.input:
            anonymizer.input_dir = Path(args.input)
        if args.output:
            anonymizer.output_dir = Path(args.output)
        if args.log:
            anonymizer.log_dir = Path(args.log)
            
        anonymizer.process_directory()
    else:
        # GUIモード
        print("GUIモードで実行中...")
        root = tk.Tk()
        app = RTDicomAnonymizer(root)
        root.mainloop()

if __name__ == '__main__':
    print("プログラムを開始します...")
    main()