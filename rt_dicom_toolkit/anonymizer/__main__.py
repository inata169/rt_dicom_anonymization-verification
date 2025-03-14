#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
匿名化モジュールのエントリーポイント
"""

from .core import RTDicomAnonymizer
import sys

def main():
    """匿名化モジュールのメイン関数"""
    print("RT DICOM Anonymizer モジュール")
    print("このモジュールはCLIまたはGUIから使用してください")
    print("GUIを起動するには:")
    print("  python -m rt_dicom_toolkit.gui anonymizer")

if __name__ == "__main__":
    main()
