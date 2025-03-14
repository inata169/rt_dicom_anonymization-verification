#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
検証モジュールのエントリーポイント
"""

from .core import RTDicomValidator
import sys

def main():
    """検証モジュールのメイン関数"""
    print("RT DICOM Validator モジュール")
    print("このモジュールはCLIまたはGUIから使用してください")
    print("GUIを起動するには:")
    print("  python -m rt_dicom_toolkit.gui validator")

if __name__ == "__main__":
    main()
