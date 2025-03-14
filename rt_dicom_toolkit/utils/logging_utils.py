"""
ロギング機能に関連するユーティリティ関数を提供するモジュール
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name, level=logging.INFO, log_file=None):
    """
    ロガーをセットアップする
    
    Args:
        name: ロガーの名前
        level: ログレベル
        log_file: ログファイルのパス（省略可）
        
    Returns:
        設定されたロガーのインスタンス
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 古いハンドラを削除（重複防止）
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（指定されている場合）
    if log_file:
        # ディレクトリを確保
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_filename(prefix, extension='log'):
    """
    タイムスタンプ付きのログファイル名を生成
    
    Args:
        prefix: ファイル名の接頭辞
        extension: ファイル拡張子
        
    Returns:
        タイムスタンプ付きのファイル名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def add_file_handler(logger, log_file, level=logging.INFO):
    """
    既存のロガーにファイルハンドラーを追加
    
    Args:
        logger: ロガーインスタンス
        log_file: ログファイルのパス
        level: ログレベル
        
    Returns:
        追加されたファイルハンドラー
    """
    # ディレクトリを確保
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return file_handler