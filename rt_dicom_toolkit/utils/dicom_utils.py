"""
DICOM関連のユーティリティ関数を提供するモジュール
"""

import pydicom
import os
from pathlib import Path

def get_dicom_info(file_path):
    """
    DICOMファイルの基本情報を取得
    
    Args:
        file_path: DICOMファイルのパス
        
    Returns:
        基本情報を含む辞書、DICOMファイルでない場合はNone
    """
    try:
        dcm = pydicom.dcmread(str(file_path), force=True)
        
        # 基本情報を抽出
        info = {}
        for tag in ['Modality', 'PatientID', 'PatientName', 'StudyDate', 'SeriesDescription']:
            if hasattr(dcm, tag):
                info[tag] = getattr(dcm, tag)
            else:
                info[tag] = None
        
        # ファイルパス情報を追加
        info['FilePath'] = str(file_path)
        info['FileName'] = Path(file_path).name
        
        return info
    except Exception:
        return None

def is_dicom_file(file_path):
    """
    ファイルがDICOMファイルかどうかを判定
    
    Args:
        file_path: 判定するファイルのパス
        
    Returns:
        DICOMファイルの場合はTrue、そうでなければFalse
    """
    try:
        pydicom.dcmread(str(file_path), force=False, stop_before_pixels=True)
        return True
    except Exception:
        return False

def get_dicom_modality(file_path):
    """
    DICOMファイルのモダリティを取得
    
    Args:
        file_path: DICOMファイルのパス
        
    Returns:
        モダリティの文字列、取得できない場合は'Unknown'
    """
    try:
        dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
        if hasattr(dcm, 'Modality'):
            return dcm.Modality
        return 'Unknown'
    except Exception:
        return 'Unknown'

def get_dicom_description(file_path):
    """
    DICOMファイルの説明を取得（モダリティベースの一般的な説明）
    
    Args:
        file_path: DICOMファイルのパス
        
    Returns:
        ファイルタイプの説明文字列
    """
    modality = get_dicom_modality(file_path)
    
    if modality == 'RTPLAN':
        return '放射線治療計画'
    elif modality == 'RTDOSE':
        return '線量分布'
    elif modality == 'RTSTRUCT':
        return '臓器輪郭'
    elif modality == 'CT':
        return 'CT画像'
    elif modality == 'RTIMAGE':
        return '治療画像'
    elif modality == 'MR':
        return 'MR画像'
    else:
        return f'{modality}ファイル'