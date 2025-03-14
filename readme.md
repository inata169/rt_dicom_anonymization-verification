# 放射線治療DICOM匿名化・検証ツールキット

放射線治療（RT）用DICOMファイルの匿名化と検証を行うための包括的なツールキットです。本ツールは医学研究や多施設共同研究でのデータ共有において、患者のプライバシーを保護しつつ、放射線治療計画データを適切に扱うことを支援します。

## 特徴

### 匿名化ツール

- 完全または部分的な匿名化
- カスタマイズ可能な匿名化プロファイル
- 臨床的に重要な構造の保持（臓器名など）
- 一貫した患者ID対応づけ
- UID管理（一貫性維持または再生成）
- プライベートタグの処理（削除または保持）
- 詳細なログとレポート
- 元のディレクトリ構造保持オプション
- GUIとコマンドラインインターフェース

### 検証ツール

- 匿名化されたDICOMファイルの包括的な検証
- 元のファイルと匿名化されたファイルの比較
- 残留個人情報（PHI）の検出
- 構造保持の検証
- 匿名化品質に関する統計レポート
- 検証結果の視覚化
- 詳細なレポート
- GUIとコマンドラインインターフェース

## プロジェクト構造

```
rt_dicom_toolkit/
│
├── anonymizer/             # DICOM匿名化モジュール
│   ├── __init__.py
│   ├── __main__.py        # 匿名化モジュールのエントリーポイント
│   ├── core.py            # 匿名化コア機能
│   ├── profiles.py        # 匿名化プロファイル定義
│   └── utils.py           # 匿名化ユーティリティ
│
├── gui/                    # グラフィカルユーザーインターフェース
│   ├── __init__.py
│   ├── __main__.py        # GUIモジュールのエントリーポイント
│   ├── anonymizer_gui.py  # 匿名化ツールGUI
│   ├── common_widgets.py  # 共通ウィジェットコンポーネント
│   └── validator_gui.py   # 検証ツールGUI
│
├── utils/                  # 共通ユーティリティ
│   ├── __init__.py
│   ├── dicom_utils.py     # DICOM操作ユーティリティ
│   ├── file_utils.py      # ファイル操作ユーティリティ
│   ├── logging_utils.py   # ロギング機能
│   └── matplotlib_utils.py # Matplotlib設定ユーティリティ
│
├── validator/              # 匿名化検証モジュール
│   ├── __init__.py
│   ├── __main__.py        # 検証モジュールのエントリーポイント
│   ├── core.py            # 検証コア機能
│   ├── report.py          # レポート生成機能
│   └── rules.py           # 検証ルール定義
│
├── __init__.py             # パッケージ初期化
├── __main__.py            # メインエントリーポイント
├── cli.py                  # コマンドラインインターフェース
├── config.py               # 設定パラメータ
└── requirements.txt        # 依存パッケージリスト
```

## インストール

### 必要条件

- Python 3.6以上
- 依存パッケージ: pydicom, numpy, matplotlib, pandas

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/rt_dicom_toolkit.git
cd rt_dicom_toolkit

# 依存パッケージをインストール
pip install -r rt_dicom_toolkit/requirements.txt

# パッケージとしてインストール（オプション）
pip install -e .
```

## 使用方法

### 簡易実行方法

```bash
# 匿名化ツールの簡易実行
python run_anonymizer.py
```

### GUIモード

```bash
# 匿名化ツールGUI
python -m rt_dicom_toolkit.gui.anonymizer_gui
# または
python -m rt_dicom_toolkit.gui anonymizer

# 検証ツールGUI
python -m rt_dicom_toolkit.gui.validator_gui
# または
python -m rt_dicom_toolkit.gui validator

# デフォルトでは検証ツールGUIが起動
python -m rt_dicom_toolkit.gui
```

### コマンドラインモード

```bash
# 匿名化ツール
python -m rt_dicom_toolkit.cli anonymize --input /path/to/input --output /path/to/output

# 検証ツール
python -m rt_dicom_toolkit.cli validate --original /path/to/original --anonymized /path/to/anonymized

# モジュールとして直接実行
python -m rt_dicom_toolkit.anonymizer
python -m rt_dicom_toolkit.validator
```

### パッケージインストール後の実行方法

パッケージをインストールした場合（`pip install -e .`）、以下のコマンドが使用可能になります：

```bash
# コマンドラインツール
rt-anonymizer --input /path/to/input --output /path/to/output
rt-validator --original /path/to/original --anonymized /path/to/anonymized

# GUIツール
rt-anonymizer-gui
rt-validator-gui
```

### 注意事項

- 単にクラスをインポートするだけでは何も実行されません。例えば以下のコマンドはクラスをインポートするだけで、実際の処理は行いません：
  ```python
  python -c "from rt_dicom_toolkit.validator import RTDicomValidator"
  ```

- クラスを使用するには、インスタンス化して適切なメソッドを呼び出す必要があります：
  ```python
  python -c "from rt_dicom_toolkit.validator import RTDicomValidator; validator = RTDicomValidator(); print('検証ツールが初期化されました')"
  ```

## データディレクトリ

プロジェクトには以下のデータディレクトリが含まれています：

```
data/
├── anonymous_dicom/      # 匿名化されたDICOMファイルの出力先
├── input_dicom/          # 入力DICOMファイルの配置場所
├── logs/                 # ログファイルの保存先
└── validation_reports/   # 検証レポートの保存先
```

## 詳細ドキュメント

詳細なユーザーマニュアルと開発者ガイドは`docs`ディレクトリにあります：

- [ユーザーマニュアル](docs/user_manual.md)
- [開発者ガイド](docs/developer_guide.md)
- [API リファレンス](docs/api_reference.md)

## 貢献

バグ報告、機能リクエスト、プルリクエストなど、あらゆる形での貢献を歓迎します。
貢献する前に、プロジェクトの[貢献ガイドライン](CONTRIBUTING.md)をご確認ください。

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。
