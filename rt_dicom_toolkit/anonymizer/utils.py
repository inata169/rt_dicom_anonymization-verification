"""
匿名化に関連するユーティリティ関数
"""

import hashlib
import uuid
from pydicom.uid import generate_uid

def generate_uid_from_string(input_str):
    """
    文字列から一貫したUIDを生成する
    
    Args:
        input_str: 入力文字列
        
    Returns:
        DICOM形式のUID
    """
    # 入力文字列からハッシュを生成
    hash_obj = hashlib.md5(str(input_str).encode())
    hash_hex = hash_obj.hexdigest()
    
    # 2.25.でDICOM UIDを始める（Antropacユーザー領域）
    uid = "2.25." + str(int(hash_hex, 16) % 10**38)
    
    return uid[:64]  # UIDは最大64文字

def generate_anonymous_patient_id(original_id, prefix="ANO", method="hash"):
    """
    匿名化された患者IDを生成する
    
    Args:
        original_id: 元の患者ID
        prefix: 匿名化IDの接頭辞
        method: 'hash'または'uuid'
        
    Returns:
        匿名化された患者ID
    """
    if method == "hash":
        # MD5ハッシュを使用して短いIDを生成
        hash_obj = hashlib.md5(str(original_id).encode())
        hash_hex = hash_obj.hexdigest()
        return f"{prefix}{hash_hex[:8]}"
    elif method == "uuid":
        # UUIDの一部を使用
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        return f"{prefix}{short_uuid}"
    else:
        raise ValueError(f"不明な生成方法: {method}")