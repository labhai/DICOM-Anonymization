#!/usr/bin/env python3
"""
FaceOff를 사용한 DICOM Defacing 자동화 스크립트

출력 구조:
    output/
    └── subject_id/
        ├── defaced.nii.gz          # Defaced NIfTI
        ├── defaced_mask.nii.gz     # Defacing mask
        └── defaced_dicom/          # Defaced DICOM 시리즈
            ├── slice_001.dcm
            ├── slice_002.dcm
            └── ...

사용법:
    python deface_dicom.py --input /path/to/root --output /path/to/output
    python deface_dicom.py --input /path/to/root --output /path/to/output --subjects sub001 sub002
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
from typing import List, Optional, Tuple

try:
    import nibabel as nib
    import pydicom
    import numpy as np
    from pydicom.uid import generate_uid
except ImportError as e:
    print(f"필수 패키지 설치 필요: {e}")
    print("설치: pip install nibabel pydicom numpy")
    sys.exit(1)


class DICOMDefacer:
    """DICOM defacing 파이프라인"""
    
    def __init__(self, threads: int = 4):
        self.threads = threads
        self._check_tools()
    
    def _check_tools(self):
        """필수 도구 확인"""
        for tool in ['dcm2niix', 'faceoff']:
            if not shutil.which(tool):
                raise RuntimeError(f"{tool}을 찾을 수 없습니다. conda activate faceoff를 실행했는지 확인하세요.")
    
    def find_subjects(self, root: Path, target_subjects: Optional[List[str]] = None) -> List[Tuple[str, Path]]:
        """
        루트 디렉토리에서 subject 이름과 해당 subject의 루트 경로를 찾습니다.
        
        Args:
            root: 검색 시작 디렉토리
            target_subjects: 특정 subject 이름 리스트 (None이면 모두 검색)
        
        Returns:
            (subject_name, subject_root_path) 튜플 리스트
        """
        print(f"\n[검색] {root} 에서 subject 검색 중...")
        
        subjects = {}
        
        # root 바로 아래의 디렉토리들을 subject로 간주
        for item in root.iterdir():
            if not item.is_dir():
                continue
            
            subject_name = item.name
            
            # target_subjects 필터링
            if target_subjects and subject_name not in target_subjects:
                continue
            
            # 해당 subject 디렉토리 아래에 DICOM 파일이 있는지 확인
            has_dicom = False
            dicom_count = 0
            
            for dirpath, _, filenames in os.walk(item):
                for filename in filenames:
                    if self._is_dicom_file(Path(dirpath) / filename):
                        has_dicom = True
                        dicom_count += 1
                        if dicom_count >= 5:  # 충분한 DICOM 파일이 있으면 중단
                            break
                if dicom_count >= 5:
                    break
            
            if has_dicom:
                subjects[subject_name] = item
                print(f"  ✓ {subject_name}: DICOM 파일 발견")
        
        return [(name, path) for name, path in sorted(subjects.items())]
    
    def _is_dicom_file(self, file_path: Path) -> bool:
        """파일이 DICOM인지 확인"""
        if not file_path.is_file():
            return False
        
        if file_path.suffix.lower() in ['.dcm', '.dicom']:
            return True
        
        try:
            with open(file_path, 'rb') as f:
                f.seek(128)
                return f.read(4) == b'DICM'
        except:
            return False
    
    def find_dicom_series(self, subject_dir: Path) -> List[Path]:
        """Subject 내의 모든 DICOM 시리즈 디렉토리 찾기"""
        series = []
        
        for dirpath, _, filenames in os.walk(subject_dir):
            current_dir = Path(dirpath)
            dicom_count = sum(1 for f in filenames if self._is_dicom_file(current_dir / f))
            
            if dicom_count >= 5:  # 최소 5개 이상의 DICOM 파일
                series.append(current_dir)
        
        return series
    
    def dcm2nii(self, dicom_dir: Path, output_dir: Path) -> Optional[Path]:
        """DICOM을 NIfTI로 변환"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'dcm2niix',
            '-z', 'y',  # gzip 압축
            '-f', 'temp',  # 임시 파일명
            '-o', str(output_dir),
            str(dicom_dir)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 생성된 NIfTI 파일 찾기
            nii_files = list(output_dir.glob('temp*.nii.gz'))
            if not nii_files:
                nii_files = list(output_dir.glob('temp*.nii'))
            
            return nii_files[0] if nii_files else None
            
        except subprocess.CalledProcessError:
            return None
    
    def deface(self, nifti_path: Path) -> Tuple[Optional[Path], Optional[Path]]:
        """
        FaceOff로 defacing 수행
        
        Returns:
            (defaced_nii, mask_nii) 튜플
        """
        # FaceOff 실행 파일의 디렉토리 찾기
        faceoff_bin = shutil.which('faceoff')
        if not faceoff_bin:
            print(f"  ✗ faceoff 실행 파일을 찾을 수 없습니다")
            return None, None
        
        # FaceOff 스크립트가 있는 디렉토리로 이동해야 함 (tempData 때문에)
        faceoff_dir = Path(faceoff_bin).parent.parent / 'FaceOff'
        
        # 만약 심볼릭 링크라면 실제 경로 확인
        if Path(faceoff_bin).is_symlink():
            real_path = Path(faceoff_bin).resolve()
            faceoff_dir = real_path.parent
        
        cmd = [
            'bash',
            str(faceoff_bin),
            '-i', str(nifti_path.absolute()),
            '-n', str(self.threads)
        ]
        
        # FaceOff 디렉토리에서 실행
        original_cwd = Path.cwd()
        
        try:
            os.chdir(faceoff_dir)
            
            result = subprocess.run(cmd, check=True, capture_output=True, 
                                  timeout=1200, text=True)
            
            # 원래 디렉토리로 복귀
            os.chdir(original_cwd)
            
            # FaceOff 출력 파일 찾기
            parent = nifti_path.parent
            stem = nifti_path.stem.replace('.nii', '')
            
            # 가능한 출력 파일명들
            defaced_candidates = [
                parent / f"{stem}_defaced.nii.gz",
                parent / f"{stem}_defaced.nii",
            ]
            
            mask_candidates = [
                parent / f"{stem}_defaceMask.nii.gz",
                parent / f"{stem}_defaceMask.nii",
                parent / f"{stem}_defaced_mask.nii.gz",
                parent / f"{stem}_mask.nii.gz",
            ]
            
            defaced = next((f for f in defaced_candidates if f.exists()), None)
            mask = next((f for f in mask_candidates if f.exists()), None)
            
            # 출력 파일을 찾지 못한 경우 모든 파일 확인
            if not defaced:
                all_files = list(parent.glob("*defaced*")) + list(parent.glob("*Mask*"))
                print(f"  ℹ 생성된 파일들: {[f.name for f in all_files]}")
            
            return defaced, mask
            
        except subprocess.CalledProcessError as e:
            os.chdir(original_cwd)
            print(f"  ✗ FaceOff 오류:")
            print(f"    명령어: {' '.join(cmd)}")
            if e.stdout:
                print(f"    출력: {e.stdout[:500]}")
            if e.stderr:
                print(f"    에러: {e.stderr[:500]}")
            return None, None
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            print(f"  ✗ 시간 초과 (1200초)")
            return None, None
        except Exception as e:
            os.chdir(original_cwd)
            print(f"  ✗ 예외 발생: {e}")
            return None, None
    
    def nii2dcm(self, defaced_nii: Path, original_dicom_dir: Path, 
                output_dir: Path) -> bool:
        """Defaced NIfTI를 DICOM으로 변환"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # NIfTI 로드
            nii_img = nib.load(defaced_nii)
            defaced_data = nii_img.get_fdata()
            
            # 원본 DICOM 파일들 찾기
            original_dicoms = sorted([
                f for f in original_dicom_dir.iterdir() 
                if self._is_dicom_file(f)
            ])
            
            if not original_dicoms:
                return False
            
            # 첫 번째 DICOM으로 기본 헤더 정보 확인
            ref_ds = pydicom.dcmread(original_dicoms[0])
            
            # Slice axis 결정
            if len(defaced_data.shape) != 3:
                return False
            
            slice_axis = np.argmax(defaced_data.shape)
            num_slices = defaced_data.shape[slice_axis]
            
            # Slice 수 맞추기
            if len(original_dicoms) != num_slices:
                print(f"  ⚠ Slice 수 불일치: DICOM={len(original_dicoms)}, NIfTI={num_slices}")
                # 작은 쪽에 맞춤
                num_slices = min(len(original_dicoms), num_slices)
                original_dicoms = original_dicoms[:num_slices]
            
            # 각 slice를 DICOM으로 저장
            new_series_uid = generate_uid()
            
            for i, original_dcm_path in enumerate(original_dicoms):
                # Slice 데이터 추출
                if slice_axis == 0:
                    slice_data = defaced_data[i, :, :]
                elif slice_axis == 1:
                    slice_data = defaced_data[:, i, :]
                else:
                    slice_data = defaced_data[:, :, i]
                
                # 원본 DICOM 로드
                ds = pydicom.dcmread(original_dcm_path)
                
                # Pixel data 변환
                original_dtype = ds.pixel_array.dtype
                original_min = np.min(ds.pixel_array)
                original_max = np.max(ds.pixel_array)
                
                # Normalize and scale
                if np.max(slice_data) > np.min(slice_data):
                    normalized = (slice_data - np.min(slice_data)) / (np.max(slice_data) - np.min(slice_data))
                    scaled = normalized * (original_max - original_min) + original_min
                else:
                    scaled = slice_data
                
                # Pixel data 업데이트
                ds.PixelData = scaled.astype(original_dtype).tobytes()
                
                # 메타데이터 업데이트
                ds.SeriesDescription = f"{getattr(ds, 'SeriesDescription', 'Unknown')}_Defaced"
                ds.SeriesInstanceUID = new_series_uid
                ds.ImageComments = "Defaced with FaceOff"
                
                # 저장
                output_path = output_dir / f"slice_{i+1:04d}.dcm"
                ds.save_as(output_path)
            
            print(f"  ✓ DICOM 변환 완료: {len(original_dicoms)}개 슬라이스")
            return True
            
        except Exception as e:
            print(f"  ✗ DICOM 변환 실패: {e}")
            return False
    
    def process_subject(self, subject_dir: Path, output_dir: Path, 
                       subject_name: str = None) -> bool:
        """
        Subject 전체 처리
        
        Args:
            subject_dir: Subject DICOM 디렉토리
            output_dir: 출력 디렉토리
            subject_name: Subject 이름 (None이면 디렉토리명 사용)
        """
        if subject_name is None:
            subject_name = subject_dir.name
        
        print(f"\n{'='*70}")
        print(f"Subject: {subject_name}")
        print(f"{'='*70}")
        
        # Subject 출력 디렉토리
        subject_out = output_dir / subject_name
        subject_out.mkdir(parents=True, exist_ok=True)
        
        # 임시 작업 디렉토리
        temp_dir = subject_out / '.temp'
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # DICOM 시리즈 찾기
            series_list = self.find_dicom_series(subject_dir)
            
            if not series_list:
                print(f"  ✗ DICOM 시리즈를 찾을 수 없습니다")
                return False
            
            print(f"  📁 {len(series_list)}개 시리즈 발견")
            
            # 모든 시리즈를 하나로 통합 또는 첫 번째 시리즈만 사용 (가장 큰 시리즈 선택)
            primary_series = max(series_list, key=lambda s: len(list(s.iterdir())))
            
            print(f"\n[1/4] DICOM → NIfTI 변환")
            nii_path = self.dcm2nii(primary_series, temp_dir)
            
            if not nii_path:
                print(f"  ✗ NIfTI 변환 실패")
                return False
            
            print(f"  ✓ 변환 완료: {nii_path.name}")
            
            # Defacing
            print(f"\n[2/4] FaceOff Defacing")
            print(f"  명령어: faceoff -i {nii_path} -n {self.threads}")
            defaced_nii, mask_nii = self.deface(nii_path)
            
            if not defaced_nii:
                print(f"  ✗ Defacing 실패")
                return False
            
            print(f"  ✓ Defacing 완료")
            
            # 결과 파일 이동
            print(f"\n[3/4] 결과 파일 저장")
            
            final_defaced = subject_out / 'defaced.nii.gz'
            shutil.move(str(defaced_nii), str(final_defaced))
            print(f"  ✓ {final_defaced.name}")
            
            if mask_nii and mask_nii.exists():
                final_mask = subject_out / 'defaced_mask.nii.gz'
                shutil.move(str(mask_nii), str(final_mask))
                print(f"  ✓ {final_mask.name}")
            
            # DICOM 변환
            print(f"\n[4/4] DICOM 변환")
            dicom_out_dir = subject_out / 'defaced_dicom'
            
            if self.nii2dcm(final_defaced, primary_series, dicom_out_dir):
                print(f"  ✓ {dicom_out_dir.name}/")
            else:
                print(f"  ⚠ DICOM 변환 실패 (NIfTI는 저장됨)")
            
            print(f"\n✅ Subject '{subject_name}' 처리 완료")
            return True
            
        except Exception as e:
            print(f"  ✗ 오류 발생: {e}")
            return False
            
        finally:
            # 임시 디렉토리 정리
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description='FaceOff를 사용한 DICOM Defacing 자동화',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s -i /data/subjects -o /data/defaced
  %(prog)s -i /data/subjects -o /data/defaced --subjects sub001 sub002
  %(prog)s -i /data/subjects -o /data/defaced --threads 8
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=Path,
        required=True,
        help='DICOM이 있는 루트 디렉토리'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        required=True,
        help='Defaced 결과를 저장할 출력 디렉토리'
    )
    
    parser.add_argument(
        '--subjects',
        nargs='+',
        help='처리할 특정 subject 이름들 (생략 시 모두 처리)'
    )
    
    parser.add_argument(
        '-n', '--threads',
        type=int,
        default=4,
        help='사용할 스레드 수 (기본: 4)'
    )
    
    args = parser.parse_args()
    
    # 입력 경로 확인
    if not args.input.exists():
        print(f"❌ 입력 경로가 존재하지 않습니다: {args.input}")
        return 1
    
    # 출력 디렉토리 생성
    args.output.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("FaceOff DICOM Defacing Pipeline")
    print("="*70)
    print(f"입력: {args.input}")
    print(f"출력: {args.output}")
    print(f"스레드: {args.threads}")
    if args.subjects:
        print(f"대상: {', '.join(args.subjects)}")
    
    # Defacer 초기화
    try:
        defacer = DICOMDefacer(threads=args.threads)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        return 1
    
    # Subject 검색
    subjects = defacer.find_subjects(args.input, args.subjects)
    
    if not subjects:
        print("\n❌ Subject를 찾을 수 없습니다")
        return 1
    
    print(f"\n📊 총 {len(subjects)}개 subject 발견\n")
    
    # 각 subject 처리
    success = 0
    failed = 0
    
    for i, (subject_name, subject_dir) in enumerate(subjects, 1):
        print(f"\n[{i}/{len(subjects)}] 처리 중...")
        
        if defacer.process_subject(subject_dir, args.output, subject_name):
            success += 1
        else:
            failed += 1
    
    # 최종 요약
    print("\n" + "="*70)
    print("처리 완료")
    print("="*70)
    print(f"총 subjects: {len(subjects)}")
    print(f"성공: {success}")
    print(f"실패: {failed}")
    print(f"출력 위치: {args.output}")
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())