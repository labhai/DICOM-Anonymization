#!/bin/bash

# ============================================
# Defacing 검증을 위한 Conda 환경 생성 및 설정
# nnUNetv2 기반 검증 환경
# ============================================

echo "Defacing 검증 환경 설정을 시작합니다..."

# 1. Conda 환경 생성 (Python 3.9)
echo "[1/7] Conda 환경 생성 중..."
conda create -n dicom_deface_verify python=3.9 -y

# 2. 환경 활성화
echo "[2/7] 환경 활성화..."
eval "$(conda shell.bash hook)"
conda activate dicom_deface_verify

# 3. PyTorch 설치 (CUDA 지원)
echo "[3/7] PyTorch 설치 중..."
echo "CUDA GPU를 사용하는 경우입니다."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU만 사용하는 경우 아래 주석을 해제하고 위 라인을 주석 처리하세요
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# PyTorch 설치 확인
echo ""
echo "PyTorch 설치 확인:"
python -c "import torch; print(f'PyTorch 버전: {torch.__version__}'); print(f'CUDA 사용 가능: {torch.cuda.is_available()}')"
echo ""

# 4. nnUNetv2 및 필수 패키지 설치
echo "[4/7] nnUNetv2 및 필수 패키지 설치 중..."
pip install nnunetv2
pip install blosc2
pip install xlsxwriter
pip install scipy scikit-image nibabel

# dcm2niix
echo ""
echo "dcm2niix 설치 중..."
conda install -c conda-forge dcm2niix -y

# nnUNetv2 설치 확인
echo ""
echo "nnUNetv2 설치 확인:"
nnUNetv2_predict -h > /dev/null 2>&1 && echo "✓ nnUNetv2 정상 설치됨" || echo "✗ nnUNetv2 설치 실패"
echo ""

# 5. 모델 다운로드 및 설치
echo "[5/7] 검증 모델 다운로드 및 설치 중..."

# 홈 디렉토리로 이동
cd ~

# 모델 파일이 이미 있는지 확인
if [ -f "BVM2025_Networks.zip" ]; then
    echo "모델 파일이 이미 존재합니다."
else
    echo "모델 다운로드 중..."
    wget https://zenodo.org/records/14509685/files/BVM2025_Networks.zip
fi

# 압축 해제
if [ -d "BVM2025_Networks" ]; then
    echo "이미 압축 해제된 모델이 존재합니다."
else
    echo "압축 해제 중..."
    unzip -q BVM2025_Networks.zip
    echo "✓ 압축 해제 완료"
fi

# 6. nnUNet_results 디렉토리 생성 및 모델 복사
echo "[6/7] 모델 설치 중..."

NNUNET_DIR="$HOME/nnUNet"

# 디렉토리 생성
mkdir -p "$NNUNET_DIR"

# 모델 복사
if [ -d "BVM2025_Networks" ]; then
    echo "모델 파일을 nnUNet_results로 복사 중..."
    cp -r BVM2025_Networks/* "$NNUNET_DIR/"
    echo "✓ 모델 복사 완료"
else
    echo "✗ BVM2025_Networks 디렉토리를 찾을 수 없습니다."
    exit 1
fi

# 7. 설치 확인
echo "[7/7] 설치 확인 중..."
echo ""
echo "=========================================="
echo "모델 폴더 확인:"
echo "=========================================="

ls -la "$NNUNET_DIR/" 2>/dev/null || echo "nnUNet 디렉토리 없음"

echo ""
echo "특정 모델 확인:"
if [ -d "$NNUNET_DIR/Dataset803_anatomical_foreground_v2" ]; then
    echo "✓ Dataset803_anatomical_foreground_v2 존재"
else
    echo "✗ Dataset803_anatomical_foreground_v2 없음"
fi

if [ -d "$NNUNET_DIR/Dataset804_SEG_defaced_areas_all_v2" ]; then
    echo "✓ Dataset804_SEG_defaced_areas_all_v2 존재"
else
    echo "✗ Dataset804_SEG_defaced_areas_all_v2 없음"
fi

# 최종 요약
echo ""
echo "=========================================="
echo "Defacing 검증 환경 설정 완료!"
echo "=========================================="
echo "환경 이름: dicom_deface_verify"
echo "Python: $(python --version)"
echo "PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo "nnUNet 모델 위치: $NNUNET_DIR"
echo ""
echo "=========================================="
echo "사용 방법:"
echo "1. 환경 활성화: conda activate dicom_deface_verify"
echo "2. 검증 스크립트 실행"
echo "=========================================="
echo ""

# 정리 옵션 (선택)
read -p "다운로드한 압축 파일을 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f ~/BVM2025_Networks.zip
    rm -rf ~/BVM2025_Networks
    echo "✓ 임시 파일 삭제 완료"
fi

echo ""
echo "설치가 완료되었습니다!"
