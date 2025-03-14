"""
DICOM匿名化検証の中核機能を提供するモジュール
"""

import os
import json
from pathlib import Path
from datetime import datetime
import logging
import traceback
import threading

import pydicom
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ..config import (
    DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_REPORT_DIR
)
from .rules import ValidationRules
from .report import generate_summary_report
from ..utils.logging_utils import setup_logger
from ..utils.file_utils import find_dicom_files

class RTDicomValidator:
    """放射線治療用DICOMファイルの匿名化検証を行うクラス"""
    
    def __init__(self, root=None):
        """
        初期化
        
        Args:
            root: GUIのルートウィンドウ（TkinterのRoot）、CLIモードの場合はNone
        """
        self.root = root
        
        # ディレクトリ設定
        self.original_dir = DEFAULT_INPUT_DIR
        self.anonymized_dir = DEFAULT_ANONYMOUS_DIR
        self.report_dir = DEFAULT_REPORT_DIR
        
        # ディレクトリが存在しない場合は作成
        self.report_dir.mkdir(exist_ok=True)
        
        # ロガーの設定
        self.logger = setup_logger("RTDicomValidator")
        
        # 検証ルールの設定
        self.rules = ValidationRules()
        
        # GUI関連の属性を初期化
        if self.root:
            self.log_text = None
            self.summary_text = None
            self.tree = None
            self.figure = None
            self.ax = None
            self.canvas = None
            self.anonymization_level = None
            self.check_private_tags = None
            self.check_file_structure = None
            self.check_uid_changed = None
            self.detailed_report = None
            self.status_var = None
            
        self.log_message("匿名化検証ツール初期化完了")
        self.log_message(f"原本ディレクトリ初期設定: {self.original_dir}")
        self.log_message(f"匿名化ディレクトリ初期設定: {self.anonymized_dir}")
        self.log_message(f"レポートディレクトリ初期設定: {self.report_dir}")
    
    def log_message(self, message):
        """ログメッセージを表示とロガーに出力"""
        try:
            if self.root and hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.root.update_idletasks()
            
            # 常にコンソールにもログを出力
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"ログ出力エラー: {str(e)}")
    
    def update_summary(self, message):
        """サマリーテキストを更新"""
        try:
            if self.root and hasattr(self, 'summary_text') and self.summary_text:
                self.summary_text.insert("end", message + "\n")
                self.summary_text.see("end")
                self.root.update_idletasks()
        except Exception as e:
            print(f"サマリー更新エラー: {str(e)}")
    
    def compare_dicom_files(self, original_file, anonymized_file):
        """
        2つのDICOMファイルを比較して匿名化の状態を確認する
        
        Args:
            original_file: 原本DICOMファイルのパス
            anonymized_file: 匿名化されたDICOMファイルのパス
            
        Returns:
            検証結果を含む辞書
        """
        try:
            # ファイルを読み込む
            original_dcm = pydicom.dcmread(str(original_file), force=True)
            anonymized_dcm = pydicom.dcmread(str(anonymized_file), force=True)
            
            # 検証結果を初期化
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
            for tag in self.rules.must_anonymize_tags:
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
            for tag in self.rules.uid_tags:
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
            for tag in self.rules.structure_tags:
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
            # GUIが存在する場合はGUIの設定を使用、そうでなければデフォルト（full）
            anonymization_level = getattr(self, 'anonymization_level', None)
            if anonymization_level and hasattr(anonymization_level, 'get'):
                level = anonymization_level.get()
            else:
                level = "full"
                
            for tag in self.rules.optional_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # 匿名化設定に応じた確認
                if level == "full":
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
            for tag in self.rules.rt_specific_tags:
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
                    # TransferSyntaxUIDの確認
                    original_transfer_syntax = None
                    anonymized_transfer_syntax = None
                    
                    # FileMetaがあり、TransferSyntaxUIDが存在する場合のみ取得
                    if hasattr(original_dcm, 'file_meta') and hasattr(original_dcm.file_meta, 'TransferSyntaxUID'):
                        original_transfer_syntax = original_dcm.file_meta.TransferSyntaxUID
                    
                    if hasattr(anonymized_dcm, 'file_meta') and hasattr(anonymized_dcm.file_meta, 'TransferSyntaxUID'):
                        anonymized_transfer_syntax = anonymized_dcm.file_meta.TransferSyntaxUID
                    
                    # 転送構文が異なる場合は警告
                    if original_transfer_syntax != anonymized_transfer_syntax:
                        self.logger.warning(f"転送構文が異なります: 原本={original_transfer_syntax}, 匿名化={anonymized_transfer_syntax}")
                    
                    # ピクセルデータの比較
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
    
    def _generate_matching_key(self, dcm):
        """
        DICOMファイルからマッチングに使用するキーを生成
        
        Args:
            dcm: pydicomで読み込んだDICOMデータセット
            
        Returns:
            マッチングに使用するキー文字列、生成できない場合はNone
        """
        try:
            # マッチングに使用するタグのリスト
            # モダリティ、シリーズ番号、インスタンス番号などを使用
            key_parts = []
            
            # モダリティ
            if hasattr(dcm, 'Modality'):
                key_parts.append(f"MOD:{dcm.Modality}")
            
            # シリーズ番号
            if hasattr(dcm, 'SeriesNumber'):
                key_parts.append(f"SER:{dcm.SeriesNumber}")
            
            # インスタンス番号
            if hasattr(dcm, 'InstanceNumber'):
                key_parts.append(f"INS:{dcm.InstanceNumber}")
            
            # 画像の位置（スライス位置）
            if hasattr(dcm, 'ImagePositionPatient'):
                # 小数点以下を切り捨てて文字列化
                pos = [str(int(float(p))) for p in dcm.ImagePositionPatient]
                key_parts.append(f"POS:{','.join(pos)}")
            
            # SOPクラスUID（ファイルの種類を示す）
            if hasattr(dcm, 'SOPClassUID'):
                key_parts.append(f"SOP:{dcm.SOPClassUID}")
            
            # キーパーツが少なくとも2つ以上あれば有効なキーとみなす
            if len(key_parts) >= 2:
                return "|".join(key_parts)
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"マッチングキー生成エラー: {e}")
            return None

    def validate_files(self, original_dir, anonymized_dir):
        """
        ディレクトリ内のファイルを検証する
        
        Args:
            original_dir: 原本DICOMファイルのディレクトリパス
            anonymized_dir: 匿名化されたDICOMファイルのディレクトリパス
            
        Returns:
            検証結果のサマリーレポート
        """
        try:
            # 原本ディレクトリからDICOMファイルのリストを取得
            original_files = find_dicom_files(original_dir)
            
            # 匿名化ディレクトリからDICOMファイルのリストを取得
            anonymized_files = find_dicom_files(anonymized_dir)
            
            self.log_message(f"原本DICOMファイル数: {len(original_files)}")
            self.log_message(f"匿名化DICOMファイル数: {len(anonymized_files)}")
            
            # 分析用の集計データ
            summary = {
                "total_files": len(original_files),
                "matched_files": 0,
                "must_anonymize_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rules.must_anonymize_tags},
                "uid_stats": {tag: {"changed": 0, "not_changed": 0} for tag in self.rules.uid_tags},
                "structure_stats": {tag: {"preserved": 0, "not_preserved": 0} for tag in self.rules.structure_tags},
                "private_tags_stats": {"removed": 0, "not_removed": 0},
                "modality_stats": {},
                "rt_specific_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rules.rt_specific_tags},
                "patient_id_map": {},
            }
            
            # 詳細な結果保存用
            detailed_results = []
            
            # 匿名化前後のファイルをマッチングして検証
            progress_count = 0
            
            # マッチングの手法を選択
            # 1. まず相対パスでマッチングを試みる
            # 2. パスでマッチングできない場合は、DICOMタグの情報を使用してマッチング
            original_files_map = {}
            original_files_info = {}
            
            # 原本ファイルをマップに追加
            for file_path in original_files:
                # 相対パスでのマッチング用
                rel_path = file_path.relative_to(original_dir)
                original_files_map[str(rel_path)] = file_path
                
                # DICOMタグでのマッチング用
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                    key = self._generate_matching_key(dcm)
                    if key:
                        original_files_info[key] = file_path
                except Exception as e:
                    self.logger.warning(f"原本ファイル読み込みエラー: {file_path} - {e}")
            
            # マッチングして検証
            for anon_file in anonymized_files:
                progress_count += 1
                
                # 進捗状況を更新
                if self.root and hasattr(self, 'status_var') and self.status_var:
                    progress = progress_count / len(anonymized_files) * 100
                    self.status_var.set(f"検証中... {progress_count}/{len(anonymized_files)} ({progress:.1f}%)")
                
                try:
                    # 相対パスでマッチング
                    rel_path = anon_file.relative_to(anonymized_dir)
                    orig_file = None
                    
                    # 1. パスでマッチング
                    if str(rel_path) in original_files_map:
                        orig_file = original_files_map[str(rel_path)]
                        self.log_message(f"パスでマッチング成功: {rel_path}")
                    else:
                        # 2. DICOMタグでマッチング
                        try:
                            dcm = pydicom.dcmread(str(anon_file), force=True, stop_before_pixels=True)
                            key = self._generate_matching_key(dcm)
                            if key and key in original_files_info:
                                orig_file = original_files_info[key]
                                self.log_message(f"タグでマッチング成功: {anon_file.name} -> {orig_file.name}")
                        except Exception as e:
                            self.logger.warning(f"匿名化ファイル読み込みエラー: {anon_file} - {e}")
                    
                    # マッチするファイルが見つかった場合
                    if orig_file:
                        
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
                            detailed_report = True
                            if hasattr(self, 'detailed_report') and hasattr(self.detailed_report, 'get'):
                                detailed_report = self.detailed_report.get()
                                
                            if detailed_report:
                                detailed_results.append({
                                    "original_file": str(orig_file),
                                    "anonymized_file": str(anon_file),
                                    "results": results
                                })
                            
                            # GUIがある場合はツリービューを更新
                            if self.root and hasattr(self, 'update_treeview'):
                                # 最初のファイルのみclear=Trueで呼び出し、以降はclear=Falseで呼び出す
                                clear = (progress_count == 1)
                                self.update_treeview(results, clear=clear)
                    else:
                        self.log_message(f"マッチするファイルなし: {rel_path}")
                
                except Exception as e:
                    self.log_message(f"ファイル検証中にエラー: {str(e)}")
                    self.logger.error(traceback.format_exc())
            
            # サマリーレポートを生成
            report = generate_summary_report(summary, self.rules)
            
            # 詳細レポートを保存
            detailed_report = True
            if hasattr(self, 'detailed_report') and hasattr(self.detailed_report, 'get'):
                detailed_report = self.detailed_report.get()
                
            if detailed_report:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                detailed_report_path = Path(self.report_dir) / f"detailed_validation_report_{timestamp}.json"
                
                with open(detailed_report_path, 'w', encoding='utf-8') as f:
                    json.dump(detailed_results, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"詳細レポート保存完了: {detailed_report_path}")
            
            # GUIがある場合はグラフを描画
            if self.root and hasattr(self, 'draw_validation_graphs'):
                self.draw_validation_graphs(summary)
            
            return report
            
        except Exception as e:
            error_msg = f"検証処理中にエラーが発生しました: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            return None
