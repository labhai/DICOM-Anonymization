#!/bin/bash

# ============================================
# DICOM Deface Anonymizer (FaceOff 기반)
# Conda 환경 자동 생성 및 설정 스크립트
# ============================================

echo "DICOM Deface Anonymizer 환경 설정을 시작합니다..."

# 1. Conda 환경 생성 (Python 3.8 권장)
echo "[1/7] Conda 환경 생성 중..."
conda create -n dicom_deface_anonymizer python=3.8 -y

# 2. 환경 활성화
echo "[2/7] 환경 활성화..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate dicom_deface_anonymizer

# 3. ANTs 설치 (FaceOff의 핵심 의존성)
echo "[3/7] ANTs 설치 중 (시간이 걸릴 수 있습니다)..."
conda install -c conda-forge ants -y

# 4. Python 패키지 설치 (DICOM/NIfTI 처리용)
echo "[4/7] Python 패키지 설치 중..."
pip install nibabel pydicom numpy scipy

# 5. dcm2niix 설치 (DICOM to NIfTI 변환용)
echo "[5/7] dcm2niix 설치 중..."
conda install -c conda-forge dcm2niix -y

# 6. FaceOff 클론 및 실행 링크 설정
echo "[6/7] FaceOff 설치 중..."
cd ~
if [ -d "FaceOff" ]; then
    echo "FaceOff 디렉토리가 이미 존재합니다. 건너뜁니다."
else
    git clone https://github.com/srikash/FaceOff.git
fi

cd FaceOff
chmod +x FaceOff
ln -sf $(pwd)/FaceOff $CONDA_PREFIX/bin/faceoff

# 7. ANTs 환경변수 설정 (필수!)
echo "[7/7] ANTs 환경 변수 등록 중..."
export ANTSPATH="$CONDA_PREFIX/bin"
export PATH="$ANTSPATH:$PATH"

# conda 활성화 시 자동 설정되도록 hook 추가
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
mkdir -p $CONDA_PREFIX/etc/conda/deactivate.d

cat <<EOF > $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
#!/bin/bash
export ANTSPATH="\$CONDA_PREFIX/bin"
export PATH="\$ANTSPATH:\$PATH"
EOF

cat <<EOF > $CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh
#!/bin/bash
unset ANTSPATH
EOF

# 8. 설치 결과 요약
echo ""
echo "=========================================="
echo "*** DICOM Deface Anonymizer 환경 설정 완료"
echo "=========================================="
echo "설치된 도구 확인:"
echo "- Conda 환경: dicom_deface_anonymizer"
echo "- Python: $(python --version)"
echo "- ANTs: $(which antsRegistration)"
echo "- dcm2niix: $(which dcm2niix)"
echo "- FaceOff: $(which faceoff)"
echo ""
echo "=========================================="
echo "*** 사용 방법:"
echo "1. 환경 활성화: conda activate dicom_deface_anonymizer"
echo "2. 도움말 확인: faceoff -h"
echo ""
echo "*** 참고:"
echo "- FaceOff가 'antsRegistration can't be found' 오류를 낼 경우,"
echo "  아래 명령으로 ANTs 경로를 직접 등록하세요:"
echo "    export ANTSPATH=\$CONDA_PREFIX/bin"
echo "    export PATH=\$ANTSPATH:\$PATH"
echo "=========================================="
echo ""

# FaceOff 도움말 출력
faceoff -h 2>/dev/null
