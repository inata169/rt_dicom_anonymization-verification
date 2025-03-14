"""
DICOM匿名化のプロファイルを定義するモジュール
"""

import hashlib
from pydicom.uid import generate_uid

def get_anonymization_profile(anonymizer):
    """
    匿名化プロファイルを取得する
    
    Args:
        anonymizer: RTDicomAnonymizerインスタンス
        
    Returns:
        匿名化プロファイル（タグ名とその置換方法を含む辞書）
    """
    # キーは属性のタグ、値は変換方法（値または関数）
    return {
        # 基本的な患者情報
        "PatientName": "ANONYMOUS",
        "PatientID": lambda x: anonymizer.generate_anonymous_id(x),
        "PatientBirthDate": "19000101",
        "PatientSex": "O",  # Other
        "PatientAge": "000Y",
        "PatientWeight": "",
        "PatientAddress": "",
        "PatientTelephoneNumbers": "",
        
        # 研究・施設情報
        "StudyID": lambda x: hashlib.md5(str(x).encode()).hexdigest()[:8],
        "AccessionNumber": "",
        "InstitutionName": "ANONYMOUS_INSTITUTION",
        "InstitutionAddress": "",
        "ReferringPhysicianName": "ANONYMOUS_PHYSICIAN",
        "PhysiciansOfRecord": "",
        "PerformingPhysicianName": "",
        "OperatorsName": "",
        
        # 識別子
        "StudyInstanceUID": lambda x: generate_uid(),
        "SeriesInstanceUID": lambda x: generate_uid(),
        "SOPInstanceUID": lambda x: generate_uid(),
        "FrameOfReferenceUID": lambda x: generate_uid(),
        
        # 日付と時刻（日付の年を2000年に設定、月日はそのまま）
        "StudyDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
        "SeriesDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
        "AcquisitionDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
        "ContentDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
        "StudyTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
        "SeriesTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
        "AcquisitionTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
        "ContentTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
        
        # その他の識別情報
        "DeviceSerialNumber": "",
        "StationName": "ANONYMOUS_STATION",
        "ManufacturerModelName": "",  # メーカー情報はそのまま残してもよい
        
        # RT特有の属性
        "StructureSetLabel": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
        "StructureSetName": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
        "ROIName": lambda x: f"ROI_{str(x)[-10:]}" if not any(organ in str(x).lower() for organ in ["lung", "heart", "liver", "kidney", "spinal", "brain"]) else str(x),
        "DoseComment": "ANONYMIZED",
        "PlanLabel": lambda x: f"ANONYMOUS_PLAN_{str(x)[-5:]}",
    }