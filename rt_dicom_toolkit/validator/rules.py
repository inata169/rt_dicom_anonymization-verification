"""
DICOM匿名化検証のルールを定義するモジュール
"""

class ValidationRules:
    """匿名化検証ルールを定義するクラス"""
    
    def __init__(self):
        """検証ルールの初期化"""
        self.define_validation_rules()
    
    def define_validation_rules(self):
        """検証ルールを定義する"""
        # 必ず匿名化されるべきタグのリスト
        self.must_anonymize_tags = [
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientAddress",
            "PatientTelephoneNumbers",
            "ReferringPhysicianName",
            "PhysiciansOfRecord",
            "PerformingPhysicianName",
            "InstitutionName",
            "InstitutionAddress",
            "StationName",
            "OperatorsName"
        ]
        
        # UIDタグのリスト
        self.uid_tags = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID"
        ]
        
        # データの構造が保持されるべきタグのリスト
        self.structure_tags = [
            "Modality",
            "SOPClassUID",
            "ImageType",
            "SamplesPerPixel",
            "PhotometricInterpretation",
            "BitsAllocated",
            "BitsStored",
            "HighBit",
            "PixelRepresentation",
            "NumberOfFrames"
        ]
        
        # 匿名化されるかどうかオプションのタグ
        self.optional_anonymize_tags = [
            "StudyDate",
            "SeriesDate",
            "AcquisitionDate",
            "ContentDate",
            "StudyTime",
            "SeriesTime",
            "AcquisitionTime",
            "ContentTime",
            "AccessionNumber",
            "StudyID",
            "SeriesNumber",
            "AcquisitionNumber",
            "InstanceNumber",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "DeviceSerialNumber"
        ]
        
        # RT構造特有のタグ
        self.rt_specific_tags = [
            "StructureSetLabel",
            "StructureSetName",
            "ROIName",
            "DoseComment",
            "PlanLabel"
        ]