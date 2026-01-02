#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DICOM 헤더 익명화 점검 - 단순화 버전 (Excel 리포트 생성)
- 단일 파일 또는 폴더 단위로 익명화율 계산
- 비익명화율 임계값 기준으로 PASS/FAIL 판정
- 저수준/고수준 익명화 방식 지원
- Excel 리포트 자동 생성
"""

import os
import re
import argparse
import warnings
from typing import Any, Tuple

import pandas as pd
import pydicom

warnings.filterwarnings('ignore')


# =========================
# 설정
# =========================
FAIL_WARNING_RATE = 0.15      # 비익명화율 임계값 (15%)


# =========================
# 익명화 필드 정의
# =========================

# 절대 익명화 (1-5)
ABSOLUTE_ANON_TAGS = {
    "PatientName",          
    "PatientBirthDate",      
    "PatientAddress",       
    "PersonName",          
    "PatientID",            
}

# 식별 및 HIPAA 필드 (6-35)
IDENTIFYING_HIPAA_TAGS = {
    "SOPInstanceUID",                         
    "UID",                                 
    "StudyDate",                             
    "StudyTime",                          
    "AccessionNumber",                         
    "AcquisitionDate",               
    "AcquisitionTime",                         
    "ContentDate",                            
    "ContentTime",                          
    "InstitutionAddress",                  
    "ReferringPhysicianName",             
    "PerformingPhysicianName",            
    "PrivateCreator",                      
    "PrivateTagData",                      
    "StudyInstanceUID",                       
    "SeriesInstanceUID",                      
    "FillerOrderNumberImagingServiceRequest",
    "PlacerOrderNumberImagingServiceRequest",
    "AcquisitionDateTime",
    "AdmittingDate",
    "ContentCreatorName",
    "ImageActualDate",
    "LastMenstrualDate",
    "StorageMediaFileSetUID",
    "VerifyingObserverName",
    "AcquisitionContextSequence",
    "ClinicalTrialSiteName",
    "ClinicalTrialSubjectID",
    "ClinicalTrialSubjectReadingID",
    "PatientComments",
}

# 준식별 필드 (36-64)
QUASI_IDENTIFIER_TAGS = {
    "ReferringPhysicianAddress",               
    "ReferringPhysicianTelephoneNumbers",   
    "PatientSex",                         
    "PatientAge",                   
    "PatientWeight",                
    "Occupation",                     
    "PerformedProcedureStepStartDate", 
    "PerformedProcedureStepStartTime",      
    "ScheduledProcedureStepStartDate",    
    "ScheduledProcedureStepEndDate",    
    "InstitutionalDepartmentName",       
    "DerivationDescription",           
    "ImageComments",
    "ContrastBolusAgent",
    "CurveDate",
    "OverlayDate",
    "PulseSequenceDate",
    "HeartRate",
    "LesionNumber",
    "StageName",
    "TriggerTime",
    "ViewName",
    "BodyPartThickness",
    "ClinicalTrialProtocolID",
    "ClinicalTrialSiteID",
    "ClinicalTrialSponsorName",
    "OrganExposed",
    "PatientState",
    "PatientSize",
}

# 전체 PHI 태그 통합
PHI_TAGS = sorted(list(ABSOLUTE_ANON_TAGS | IDENTIFYING_HIPAA_TAGS | QUASI_IDENTIFIER_TAGS))

# 추가 설명 필드
ADDITIONAL_PHI_TEXTY = {
    "ProtocolName", "RequestedProcedureDescription", "PerformedProcedureStepDescription",
    "StudyComments", "SeriesComments", "StudyDescription", "SeriesDescription"
}


# =========================
# 익명화 규칙 정의 (항목별)
# =========================

# 저수준: Hash값 대체 허용
LOW_HASH_ALLOWED = {
    "PatientID",  # 5
    "SOPInstanceUID",  # 6
    "UID",  # 7
    "StudyDate",  # 8
    "AccessionNumber",  # 10
    "AcquisitionDate",  # 11
    "ContentDate",  # 13
    "StudyInstanceUID",  # 20
    "SeriesInstanceUID",  # 21
    "FillerOrderNumberImagingServiceRequest",  # 22
    "PlacerOrderNumberImagingServiceRequest",  # 23
    "AcquisitionDateTime",  # 24
    "AdmittingDate",  # 25
    "ImageActualDate",  # 27
    "LastMenstrualDate",  # 28
    "StorageMediaFileSetUID",  # 29
    "ClinicalTrialSubjectID",  # 33
    "ClinicalTrialSubjectReadingID",  # 34
    "PerformedProcedureStepStartDate",  # 42
    "PerformedProcedureStepStartTime",  # 43
    "ScheduledProcedureStepStartDate",  # 44
    "ScheduledProcedureStepEndDate",  # 45
    "CurveDate",  # 50
    "OverlayDate",  # 51
    "PulseSequenceDate",  # 52
    "ClinicalTrialProtocolID",  # 59
    "ClinicalTrialSiteID",  # 60
}

# 저수준: 유지 허용
LOW_RETAIN_ALLOWED = {
    "PatientSex",  # 38
    "PatientAge",  # 39
    "PatientWeight",  # 40
    "HeartRate",  # 53
    "TriggerTime",  # 56
    "ViewName",  # 57
    "BodyPartThickness",  # 58
    "PatientSize",  # 64
}

# 고수준: 5단위 구간 반올림 필요
HIGH_RANGE_REQUIRED = {
    "PatientAge",  # 39
    "PatientWeight",  # 40
    "HeartRate",  # 53
    "TriggerTime",  # 56
    "BodyPartThickness",  # 58
    "PatientSize",  # 64
}

# 고수준: 유지 허용 (구간 반올림 불필요)
HIGH_RETAIN_ALLOWED = {
    "PatientSex",  # 38
}


# =========================
# 유틸리티 함수
# =========================
def _value_to_str(v: Any) -> str:
    """값을 문자열로 변환"""
    try:
        if v is None: 
            return ""
        return re.sub(r"\s+", " ", str(v)).strip()
    except Exception:
        return ""


# 플레이스홀더 패턴
PLACEHOLDER_PATTERNS = [
    r"^\s*$", r"^ANON(YMOUS)?$", r"^REDACTED$", r"^REMOVED$", r"^DE-?IDENTIFIED$",
    r"^UNKNOWN$", r"^N/?A$", r"^X+$", r"^\*+$", r"^0+$"
]
PLACEHOLDER_REGEX = re.compile("|".join(PLACEHOLDER_PATTERNS), flags=re.IGNORECASE)

def _is_placeholder(s: str) -> bool:
    """플레이스홀더 여부 확인"""
    return bool(PLACEHOLDER_REGEX.search(s)) or s == "Unknown"


# 날짜/시간 제로값
ZEROISH_DATES = {"", "00000000", "19000101", "19000100", "00010101"}
ZEROISH_TIMES = {"", "000000", "000000.000000", "000000.000"}


def _is_hash_value(s: str) -> bool:
    """Hash값인지 확인"""
    if not s or len(s) < 10:
        return False
    # UUID 형식
    if re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", s):
        return True
    # 16진수 문자열 (10자 이상)
    if re.match(r"^[0-9a-fA-F]{10,}$", s):
        return True
    # 영숫자 혼합 긴 문자열 (12자 이상)
    if re.match(r"^[0-9A-Za-z\-\_]{12,}$", s):
        return True
    return False


def _is_range_value(s: str, tag: str) -> bool:
    """5단위 구간 반올림인지 확인"""
    if not s:
        return False
    
    # 나이: "65-69", "70-74" 형식
    if tag == "PatientAge":
        # "065Y" 형식 제거 후 체크
        age_str = re.sub(r'[YMDymd]', '', s).strip()
        # 범위 형식: "65-69"
        if re.match(r"^\d{2,3}-\d{2,3}$", age_str):
            parts = age_str.split("-")
            try:
                low, high = int(parts[0]), int(parts[1])
                if high - low == 4 and low % 5 == 0:
                    return True
            except ValueError:
                pass
        return False
    
    # 숫자 범위: "70-74", "165-169" 등
    if re.match(r"^\d+-\d+$", s):
        parts = s.split("-")
        if len(parts) == 2:
            try:
                low, high = int(parts[0]), int(parts[1])
                # 5단위 구간인지 확인 (차이가 4이고, 시작값이 5의 배수)
                if high - low == 4 and low % 5 == 0:
                    return True
            except ValueError:
                pass
    
    return False


# PHI 의심 패턴
DESCRIPTOR_PHI_REGEXES = [
    r"\b(name|mrn|ssn|dob|phone|tel|id|acc(ession)?|acct|pat(i?ent)?|chart)\b",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\+?\d[\d .\-]{7,}\d",
    r"\b\d{7,}\b",
    r"^[A-Z]{2,}(\^[A-Z]{2,})+$",
    r"\bfor\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
    r"\b[A-Z][a-z]+,?\s+[A-Z][a-z]+\b"
]
DESCRIPTOR_PHI_COMPILED = [re.compile(p, re.IGNORECASE) for p in DESCRIPTOR_PHI_REGEXES]

def _descriptor_has_phi(s: str) -> bool:
    """설명 필드에 PHI 의심 패턴이 있는지 확인"""
    if not s:
        return False
    for rgx in DESCRIPTOR_PHI_COMPILED:
        if rgx.search(s):
            return True
    return False


# =========================
# 익명화 검증 로직
# =========================
def check_anonymization(tag: str, value: str, option: str = "low") -> Tuple[bool, str]:
    """
    태그와 값을 받아서 익명화 여부 판정
    option: "low" (저수준) 또는 "high" (고수준)
    반환: (익명화됨=True/안됨=False, 판정사유)
    """
    
    # 빈값 또는 플레이스홀더면 항상 통과
    if not value or _is_placeholder(value):
        return True, f"[{option.upper()}] 빈값/플레이스홀더"
    
    # === 저수준 (LOW) 검증 ===
    if option == "low":
        # 1-4번: 무조건 삭제 (PatientID 제외)
        if tag in {"PatientName", "PatientBirthDate", "PatientAddress", "PersonName"}:
            return False, "[LOW] 삭제 필요"
        
        # 5번 PatientID: Hash값 대체 허용
        if tag == "PatientID":
            if _is_hash_value(value):
                return True, "[LOW] Hash값 대체 허용"
            return False, "[LOW] 삭제 또는 Hash값 대체 필요"
        
        # Hash값 대체 허용 태그들
        if tag in LOW_HASH_ALLOWED:
            if _is_hash_value(value):
                return True, "[LOW] Hash값 대체 허용"
            return False, "[LOW] 삭제 또는 Hash값 대체 필요"
        
        # 유지 허용 태그들 (38, 39, 40, 53, 56, 57, 58, 64)
        if tag in LOW_RETAIN_ALLOWED:
            return True, "[LOW] 유지 허용"
        
        # 나머지는 무조건 삭제
        return False, "[LOW] 삭제 필요"
    
    # === 고수준 (HIGH) 검증 ===
    elif option == "high":
        # 1-5번: 무조건 삭제
        if tag in ABSOLUTE_ANON_TAGS:
            return False, "[HIGH] 삭제 필요"
        
        # 6-35번 중 Hash값 대체 허용 태그들 → 고수준에서는 무조건 삭제
        if tag in LOW_HASH_ALLOWED:
            return False, "[HIGH] 삭제 필요"
        
        # 38번 PatientSex: 유지 허용
        if tag in HIGH_RETAIN_ALLOWED:
            return True, "[HIGH] 유지 허용"
        
        # 39, 40, 53, 56, 58, 64번: 5단위 구간 반올림 필요
        if tag in HIGH_RANGE_REQUIRED:
            if _is_range_value(value, tag):
                return True, "[HIGH] 5단위 구간 반올림 적용"
            return False, "[HIGH] 5단위 구간 반올림 필요"
        
        # 57번 ViewName: 고수준에서는 삭제
        if tag == "ViewName":
            return False, "[HIGH] 삭제 필요"
        
        # 나머지는 무조건 삭제
        return False, "[HIGH] 삭제 필요"
    
    # 기본값 (도달하지 않음)
    return False, f"[{option.upper()}] 알 수 없는 검증 방식"


# =========================
# 단일 파일 분석
# =========================
def analyze_single_dcm(dcm_path: str, option: str = "low"):
    """단일 DICOM 파일 분석 후 DataFrame + 요약정보 반환"""
    ds = pydicom.dcmread(dcm_path, stop_before_pixels=True, force=True)
    
    rows = []
    for tag in PHI_TAGS:
        # 값 추출
        try:
            elem = ds.data_element(tag)
            if elem is not None:
                vr = elem.VR
                val = _value_to_str(elem.value)
                
                # VR=SH(Short String)인 경우 16자 초과시 잘라냄
                if vr == "SH" and isinstance(val, str) and len(val) > 16:
                    val = val[:16]
            else:
                val = ""
                vr = None
        except Exception:
            val = ""
            vr = None
        
        # 익명화 검증
        is_anon, reason = check_anonymization(tag, val, option)
        rows.append([tag, val, is_anon, reason])
    
    # DataFrame 생성
    df = pd.DataFrame(rows, columns=["태그", "값", "익명화여부", "판정사유"])
    
    # 요약 계산
    total = len(df)
    ok_cnt = int(df["익명화여부"].sum())
    warn_cnt = total - ok_cnt
    warn_rate = warn_cnt / total if total > 0 else 0.0
    overall = "FAIL" if warn_rate >= FAIL_WARNING_RATE else "PASS"
    
    # 절대 익명화 필드 검증
    abs_df = df[df["태그"].isin(ABSOLUTE_ANON_TAGS)].copy()
    abs_pass = abs_df["익명화여부"].all() if not abs_df.empty else True
    
    # 최종 결과
    final_result = "PASS" if (overall == "PASS" and abs_pass) else "FAIL"
    
    summary = {
        "파일명": os.path.basename(dcm_path),
        "검증 방식": option.upper(),
        "통과": ok_cnt,
        "경고": warn_cnt,
        "익명화율": f"{(1 - warn_rate):.2%}",
        "비익명화율 임계값(15%)": "PASS" if warn_rate < FAIL_WARNING_RATE else "FAIL",
        "절대익명화 필드 검증": "PASS" if abs_pass else "FAIL",
        "최종 결과": final_result,
    }
    
    return df, abs_df, summary


# =========================
# Excel 작성 유틸리티
# =========================
def write_summary(ws, summary, df, workbook):
    """상단 요약정보 작성 후 다음 시작 행 반환"""
    bold_fmt = workbook.add_format({'bold': True})
    red_fmt = workbook.add_format({'font_color': 'red', 'bold': True})
    green_fmt = workbook.add_format({'font_color': 'green', 'bold': True})
    
    summary_items = [
        ("검증 방식", summary['검증 방식']),
        ("검사 태그수", len(df)),
        ("통과", summary['통과']),
        ("경고", summary['경고']),
        ("익명화율", summary['익명화율']),
        ("비익명화율 임계값", summary['비익명화율 임계값(15%)']),
        ("절대 익명화 필드 검증", summary['절대익명화 필드 검증']),
        ("최종 결과", summary['최종 결과']),
    ]
    
    for i, (key, val) in enumerate(summary_items):
        ws.write(i, 0, f"{key}:", bold_fmt)
        # PASS / FAIL 강조
        if key == "최종 결과":
            if str(val).upper() == "FAIL":
                ws.write(i, 1, val, red_fmt)
            elif str(val).upper() == "PASS":
                ws.write(i, 1, val, green_fmt)
            else:
                ws.write(i, 1, val)
        else:
            ws.write(i, 1, val)
    return len(summary_items) + 2


def write_section(ws, start_row, title, df, workbook):
    """제목 + DataFrame 한 블록을 시트에 작성하고 다음 시작 행 반환"""
    title_fmt = workbook.add_format({
        'bold': True,
        'bg_color': '#D9D9D9',
        'align': 'left',
        'valign': 'vcenter',
        'font_size': 11
    })
    header_fmt = workbook.add_format({
        'bold': True,
        'bg_color': '#D9D9D9',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    red_false_fmt = workbook.add_format({'font_color': 'red', 'bold': True, 'valign': 'top'})
    
    # 제목
    ws.write(start_row, 0, title, title_fmt)
    row = start_row + 2
    
    headers = ["태그", "값", "익명화여부", "판정사유"]
    for j, h in enumerate(headers):
        ws.write(row, j, h, header_fmt)
    row += 1
    
    # 데이터 작성
    if df is not None and not df.empty:
        for _, r in df.iterrows():
            for j, h in enumerate(headers):
                val = str(r[h])
                if h == "익명화여부" and str(r["익명화여부"]).lower() == "false":
                    ws.write(row, j, "False", red_false_fmt)
                else:
                    ws.write(row, j, val, text_fmt)
            row += 1
    else:
        ws.write(row, 0, "없음 (모두 익명화 통과)", text_fmt)
        row += 1
    
    row += 4
    return row


# =========================
# 폴더 분석 및 Excel 생성
# =========================
def run_folder_to_xlsx(input_path: str, output_path: str, option: str = "low"):
    """DICOM 폴더 또는 파일 검사 후 Excel 리포트 생성"""
    
    # 입력 경로 확인
    if not os.path.exists(input_path):
        print(f"[오류] 입력 경로를 찾을 수 없습니다: {input_path}")
        return
    
    # 파일 목록 수집
    dcm_files = []
    if os.path.isfile(input_path):
        if input_path.lower().endswith((".dcm", ".dicom")):
            dcm_files.append(input_path)
    else:
        for root, _, files in os.walk(input_path):
            for fn in files:
                if fn.lower().endswith((".dcm", ".dicom")):
                    dcm_files.append(os.path.join(root, fn))
    
    if not dcm_files:
        print(f"[알림] DICOM 파일을 찾을 수 없습니다: {input_path}")
        return
    
    print(f"검사 시작: {len(dcm_files)}개 파일")
    
    all_summaries = []
    processed_count = 0
    
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        
        for fpath in dcm_files:
            try:
                df, abs_df, summary = analyze_single_dcm(fpath, option)
                flagged_df = df[~df["익명화여부"]].copy()
                all_summaries.append(summary)
                
                # 시트 이름 생성 (31자 제한)
                sheet_name = os.path.splitext(os.path.basename(fpath))[0][:31]
                
                # DataFrame 인덱스 리셋
                df = df.reset_index(drop=True)
                abs_df = abs_df.reset_index(drop=True)
                flagged_df = flagged_df.reset_index(drop=True)
                
                # 임시로 데이터 쓰기 (나중에 덮어씀)
                df.to_excel(writer, sheet_name=sheet_name, startrow=10000)
                ws = writer.sheets[sheet_name]
                
                # 열 너비 설정
                ws.set_column(0, 0, 28)
                ws.set_column(1, 1, 45)
                ws.set_column(2, 2, 10)
                ws.set_column(3, 3, 35)
                
                # 요약 및 섹션 작성
                row = write_summary(ws, summary, df, workbook)
                row = write_section(ws, row, "- 절대 익명화 필드 검증 결과 -", abs_df, workbook)
                row = write_section(ws, row, "- 경고 (점검 필요) -", flagged_df, workbook)
                row = write_section(ws, row, "- 전체 결과 -", df, workbook)
                
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"  - {processed_count}/{len(dcm_files)} 파일 완료")
                
            except Exception as e:
                print(f"[오류] {os.path.basename(fpath)}: {e}")
        
        # 전체 요약 시트 생성
        if all_summaries:
            summary_df = pd.DataFrame(all_summaries)
            summary_df.to_excel(writer, sheet_name="전체 파일 검증 통합 결과", index=False)
            
            ws = writer.sheets["전체 파일 검증 통합 결과"]
            
            # 포맷 정의
            red_bold = workbook.add_format({'font_color': 'red', 'bold': True})
            green_bold = workbook.add_format({'font_color': 'green', 'bold': True})
            red_plain = workbook.add_format({'font_color': 'red'})
            normal_fmt = workbook.add_format({})
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
            
            # 열 너비 조정
            ws.set_column(0, 0, 15)
            ws.set_column(1, 1, 12)
            ws.set_column(2, len(summary_df.columns) - 1, 20)
            
            # 헤더 작성
            for col, header in enumerate(summary_df.columns):
                ws.write(0, col, header, header_fmt)
            
            # PASS/FAIL 색상 지정
            for row_idx, result in enumerate(summary_df["최종 결과"], start=1):
                file_name = summary_df.at[row_idx - 1, "파일명"]
                ws.write(row_idx, 0, file_name, normal_fmt)
                for col_idx, col_name in enumerate(summary_df.columns[1:], start=1):
                    val = summary_df.at[row_idx - 1, col_name]
                    
                    # PASS/FAIL 강조 (최종 결과만)
                    if col_name == "최종 결과":
                        if str(val).upper() == "FAIL":
                            ws.write(row_idx, col_idx, val, red_bold)
                            ws.write(row_idx, 0, file_name, red_plain)
                        elif str(val).upper() == "PASS":
                            ws.write(row_idx, col_idx, val, green_bold)
                        else:
                            ws.write(row_idx, col_idx, val, normal_fmt)
                    else:
                        ws.write(row_idx, col_idx, val, normal_fmt)
        
        # 전체 요약 시트를 맨 앞으로 이동
        summary_sheet = writer.sheets.get("전체 파일 검증 통합 결과")
        if summary_sheet is not None:
            workbook.worksheets_objs.remove(summary_sheet)
            workbook.worksheets_objs.insert(0, summary_sheet)
    
    print(f"  - {processed_count}/{len(dcm_files)} 파일 완료")
    print(f"\n✅ 검사 완료! 결과 저장: {output_path}")


# =========================
# 메인 실행
# =========================
def main():
    parser = argparse.ArgumentParser(
        description="DICOM 헤더 익명화 검증 및 Excel 리포트 생성"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="검사할 DICOM 파일 또는 폴더 경로"
    )
    parser.add_argument(
        "--output",
        default="dicom_header_verification.xlsx",
        help="출력 Excel 파일 경로 (기본값: dicom_header_verification.xlsx)"
    )
    parser.add_argument(
        "--option",
        choices=["low", "high"],
        default="low",
        help="익명화 검증 방식: low(저수준, 기본값) 또는 high(고수준)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("DICOM 헤더 익명화 검증")
    print("="*60)
    print(f"입력: {args.input}")
    print(f"출력: {args.output}")
    print(f"검증 방식: {args.option.upper()}")
    print(f"비익명화율 임계값: {FAIL_WARNING_RATE:.1%}")
    print("="*60)
    print()
    
    run_folder_to_xlsx(args.input, args.output, args.option)


if __name__ == "__main__":
    main()
