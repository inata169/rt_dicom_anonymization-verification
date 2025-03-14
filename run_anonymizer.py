#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
匿名化処理を実行するスクリプト
"""

from pathlib import Path
import sys
import os

# rt_dicom_toolkitパッケージのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer
from rt_dicom_toolkit.config import DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_LOG_DIR

def main():
    """匿名化処理を実行"""
    print("匿名化処理を開始します...")
    
    # 匿名化ツールのインスタンスを作成
    anonymizer = RTDicomAnonymizer()
    
    # ディレクトリ設定を確認
    print(f"入力ディレクトリ: {anonymizer.input_dir}")
    print(f"出力ディレクトリ: {anonymizer.output_dir}")
    print(f"ログディレクトリ: {anonymizer.log_dir}")
    
    # 匿名化処理を実行
    anonymizer.process_directory()
    
    print("匿名化処理が完了しました。")

if __name__ == "__main__":
    main()
