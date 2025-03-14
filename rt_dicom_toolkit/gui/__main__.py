#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUIモジュールのエントリーポイント
"""

from .validator_gui import run_validator_gui
from .anonymizer_gui import run_anonymizer_gui
import sys

def main():
    """GUIモジュールのメイン関数"""
    print("RT DICOM Toolkit GUI モジュール")
    print("使用方法:")
    print("  validator - 検証ツールGUIを起動")
    print("  anonymizer - 匿名化ツールGUIを起動")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validator":
            run_validator_gui()
        elif sys.argv[1] == "anonymizer":
            run_anonymizer_gui()
        else:
            print(f"不明なコマンド: {sys.argv[1]}")
    else:
        # デフォルトでvalidator_guiを起動
        run_validator_gui()

if __name__ == "__main__":
    main()
