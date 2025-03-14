"""
検証レポートの生成モジュール
"""

from datetime import datetime
from pathlib import Path

def generate_summary_report(summary, rules):
    """
    検証結果のサマリーレポートを生成
    
    Args:
        summary: 検証結果のサマリー情報
        rules: 検証ルールのインスタンス
        
    Returns:
        生成されたレポートテキスト
    """
    report = []
    
    report.append("=== 匿名化検証サマリーレポート ===")
    report.append(f"検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"総ファイル数: {summary['total_files']}")
    report.append(f"マッチングファイル数: {summary['matched_files']}")
    report.append("")
    
    # 全体の匿名化状況
    total_must_tags = len(rules.must_anonymize_tags) * summary['matched_files']
    total_anonymized = sum(summary['must_anonymize_stats'][tag]['anonymized'] for tag in rules.must_anonymize_tags)
    
    if total_must_tags > 0:
        anonymization_rate = total_anonymized / total_must_tags * 100
        report.append(f"必須タグ匿名化率: {anonymization_rate:.1f}%")
        
        if anonymization_rate >= 95:
            report.append("✅ 匿名化状況: 良好（95%以上のタグが正しく匿名化されています）")
        elif anonymization_rate >= 80:
            report.append("⚠️ 匿名化状況: 要確認（80-95%のタグが匿名化されています）")
        else:
            report.append("❌ 匿名化状況: 不十分（匿名化率が80%未満です）")
    
    report.append("")
    report.append("--- 必須匿名化タグの状況 ---")
    for tag in rules.must_anonymize_tags:
        anonymized = summary['must_anonymize_stats'][tag]['anonymized']
        not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
        total = anonymized + not_anonymized
        
        if total > 0:
            rate = anonymized / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {anonymized}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- UIDタグの変更状況 ---")
    for tag in rules.uid_tags:
        changed = summary['uid_stats'][tag]['changed']
        not_changed = summary['uid_stats'][tag]['not_changed']
        total = changed + not_changed
        
        if total > 0:
            rate = changed / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {changed}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- 構造タグの保持状況 ---")
    for tag in rules.structure_tags:
        preserved = summary['structure_stats'][tag]['preserved']
        not_preserved = summary['structure_stats'][tag]['not_preserved']
        total = preserved + not_preserved
        
        if total > 0:
            rate = preserved / total * 100
            status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
            report.append(f"{status} {tag}: {preserved}/{total} ({rate:.1f}%)")
    
    report.append("")
    report.append("--- プライベートタグの削除状況 ---")
    removed = summary['private_tags_stats']['removed']
    not_removed = summary['private_tags_stats']['not_removed']
    total = removed + not_removed
    
    if total > 0:
        rate = removed / total * 100
        status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
        report.append(f"{status} プライベートタグ削除: {removed}/{total} ({rate:.1f}%)")
    
    # モダリティ分布
    report.append("")
    report.append("--- モダリティ分布 ---")
    for modality, count in summary['modality_stats'].items():
        report.append(f"{modality}: {count}ファイル")
    
    # 患者ID対応表
    if summary['patient_id_map']:
        report.append("")
        report.append("--- 患者ID対応表 （最大10件表示） ---")
        count = 0
        for orig_id, anon_id in summary['patient_id_map'].items():
            # 患者IDの一部をマスク
            if len(orig_id) > 4:
                masked_id = orig_id[:2] + "***" + orig_id[-2:]
            else:
                masked_id = "***"
                
            report.append(f"{masked_id} → {anon_id}")
            count += 1
            if count >= 10:
                report.append(f"...他 {len(summary['patient_id_map']) - 10} 件")
                break
    
    return "\n".join(report)

def generate_validation_report_filename(prefix="validation_summary"):
    """
    レポートのファイル名を生成
    
    Args:
        prefix: ファイル名の接頭辞
        
    Returns:
        タイムスタンプを含むファイル名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.txt"

def save_report(report_text, report_dir, filename=None):
    """
    レポートをファイルに保存
    
    Args:
        report_text: レポートのテキスト
        report_dir: 保存先ディレクトリ
        filename: ファイル名（省略時は自動生成）
        
    Returns:
        保存したファイルのパス
    """
    if filename is None:
        filename = generate_validation_report_filename()
    
    report_path = Path(report_dir) / filename
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_path