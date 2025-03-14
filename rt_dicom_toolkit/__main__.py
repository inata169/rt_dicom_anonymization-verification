#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RT DICOM Toolkitのメインエントリーポイント
"""

import sys

def main():
    """メインエントリーポイント"""
    print("RT DICOM Toolkit")
    print("使用方法:")
    print("  python -m rt_dicom_toolkit.gui - GUIモジュールを実行")
    print("  python -m rt_dicom_toolkit.validator - 検証モジュールを実行")
    print("  python -m rt_dicom_toolkit.anonymizer - 匿名化モジュールを実行")

if __name__ == "__main__":
    main()
