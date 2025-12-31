#!/bin/bash
echo "======================================================================="
echo "  DICOM 헤더 익명화 검증 도구 - 필수 패키지 설치"
echo "======================================================================="
echo ""

# 필수 Python 패키지 설치
echo "필수 Python 패키지 설치 중..."
echo ""

pip install "numpy>=1.20.0" "pandas>=1.3.0" "pydicom>=2.3.0" "xlsxwriter>=3.0.0"

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================="
    echo "  설치 완료"
    echo "======================================================================="
    echo ""
    echo "사용 방법:"
    echo "  python dicom_header_verifier.py --input /path/to/root --output result.xlsx --option <low|high>"
    echo ""
    echo "예시:"
    echo "  python dicom_header_verifier.py --input /path/to/dicom --output result.xlsx --option low"
    echo ""
else
    echo ""
    echo "❌ 패키지 설치 중 오류가 발생했습니다. 환경을 확인하세요."
    echo ""
fi
