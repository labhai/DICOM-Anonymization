"""
사용법:
    python dicom_deface_verifier.py --defaced /path/to/defaced --raw /path/to/raw

    # GPU 2 사용
    python dicom_deface_verifier.py --defaced /path/to/defaced --raw /path/to/raw --gpu 3

    # 특정 subjects만
    python dicom_deface_verifier.py --defaced /path/to/defaced --raw /path/to/raw --subjects sub001 sub002

    # 결과 저장 폴더 및 파일명 지정
    python dicom_deface_verifier.py --defaced /path/to/defaced --raw /path/to/raw --output /path/to/results/dicom_deface_verification.xlsx
"""

import os
import sys
import numpy as np
import nibabel as nib
import subprocess
import tempfile
import shutil
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, List

from scipy import ndimage
from skimage.metrics import structural_similarity as ssim
from nibabel.processing import resample_from_to
import xlsxwriter

import warnings
warnings.filterwarnings('ignore')


class DefacingVerifier:
    TARGETS = {
        'surface_dsc': 0.80,
        'hd95_mm': 30.00,
        'ssim_def': 0.80,
        'psnr_def_db': 10.00
    }

    SURFACE_TOL_MM = 5.0
    ROI_MARGIN_MM = 30.0
    
    def __init__(self, gpu_id: int = 0):
        self.gpu_id = gpu_id
        self.setup_environment()
        self.temp_dir = None
    
    def setup_environment(self):
        home_dir = os.path.expanduser("~")
        os.environ['nnUNet_raw'] = f"{home_dir}/nnUNet_raw"
        os.environ['nnUNet_preprocessed'] = f"{home_dir}/nnUNet_preprocessed"
        os.environ['nnUNet_results'] = f"{home_dir}/nnUNet"
        os.environ['nnUNet_n_proc_DA'] = "12"
        
        os.environ['CUDA_VISIBLE_DEVICES'] = str(self.gpu_id)
        print(f"GPU {self.gpu_id} 사용 설정 완료")
    
    @staticmethod
    def _is_dicom_file(file_path: Path) -> bool:
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
    
    def dcm2nii(self, dicom_dir: Path, output_dir: Path) -> Optional[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'dcm2niix',
            '-z', 'y',
            '-f', 'raw',
            '-o', str(output_dir),
            str(dicom_dir)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            nii_files = list(output_dir.glob('raw*.nii.gz'))
            if not nii_files:
                nii_files = list(output_dir.glob('raw*.nii'))
            
            return nii_files[0] if nii_files else None
            
        except subprocess.CalledProcessError:
            return None
    
    def find_raw_dicom_for_subject(self, subject_name: str, raw_root: Path) -> Optional[Path]:
        subject_dir = raw_root / subject_name
        
        if not subject_dir.exists():
            return None
        
        for dirpath, _, filenames in os.walk(subject_dir):
            current_dir = Path(dirpath)
            dicom_count = sum(1 for f in filenames if self._is_dicom_file(current_dir / f))
            
            if dicom_count >= 5:
                return current_dir
        
        return None
    
    def _prepare_single_input(self, img_path: Path, subdir_name: str) -> str:
        in_dir = Path(self.temp_dir) / subdir_name
        in_dir.mkdir(exist_ok=True)
        target = in_dir / "case001_0000.nii.gz"
        shutil.copy2(img_path, target)
        return str(in_dir)
    
    def _find_model_root(self, model_name: str) -> Path:
        base_path = Path(os.environ['nnUNet_results']) / model_name
        
        if not base_path.exists():
            raise FileNotFoundError(f"모델을 찾을 수 없습니다: {base_path}")
        
        candidate = base_path
        
        if not (candidate / "dataset.json").exists() or not (candidate / "plans.json").exists():
            default_trainer = candidate / "nnUNetTrainer__nnUNetPlans__3d_fullres"
            if (default_trainer / "dataset.json").exists() and (default_trainer / "plans.json").exists():
                candidate = default_trainer
            else:
                for p in candidate.glob("**/*"):
                    if p.is_dir() and (p / "dataset.json").exists() and (p / "plans.json").exists():
                        candidate = p
                        break
                else:
                    raise FileNotFoundError(f"모델 루트를 찾을 수 없습니다: {base_path}")
        
        return candidate
    
    def _run_nnunet_predict(self, input_dir: str, output_dir: str, model_name: str) -> str:
        model_root = self._find_model_root(model_name)
        out_dir = Path(self.temp_dir) / output_dir
        out_dir.mkdir(exist_ok=True)
        
        fold_all = model_root / "fold_all"
        
        if fold_all.exists():
            chosen_chk = "checkpoint_final.pth"
            if not (fold_all / chosen_chk).exists():
                chosen_chk = "checkpoint_best.pth"
            folds_arg = ["all"]
        else:
            fold_dirs = sorted([p for p in model_root.glob("fold_*") if p.is_dir()])
            if not fold_dirs:
                raise FileNotFoundError(f"fold_all 또는 fold_* 디렉토리가 없습니다: {model_root}")
            
            chosen_chk = "checkpoint_final.pth"
            fold_numbers = [fd.name.split("_")[-1] for fd in fold_dirs]
            folds_arg = fold_numbers
        
        cmd = [
            "nnUNetv2_predict_from_modelfolder",
            "-i", input_dir,
            "-o", str(out_dir),
            "-m", str(model_root),
            "-chk", chosen_chk,
            "-f", *folds_arg,
            "-step_size", "0.7"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            raise RuntimeError(f"nnUNet 예측 실패: {result.stderr}")
        
        preds = sorted(out_dir.glob("*.nii.gz"))
        if not preds:
            raise FileNotFoundError(f"예측 결과가 없습니다: {out_dir}")
        
        return str(preds[0])
    
    @staticmethod
    def load_nifti_data(path: Path) -> Tuple[np.ndarray, np.ndarray, any]:
        nii = nib.load(path)
        return nii.get_fdata(), nii.affine, nii.header
    
    def load_binary_mask_to_ref(self, mask_path: Path, ref_img_path: Path) -> np.ndarray:
        ref_nii = nib.load(ref_img_path)
        m_nii = nib.load(mask_path)
        
        if (m_nii.shape != ref_nii.shape) or (not np.allclose(m_nii.affine, ref_nii.affine, atol=1e-3)):
            m_nii = resample_from_to(m_nii, (ref_nii.shape, ref_nii.affine), order=0)
        
        m = m_nii.get_fdata()
        return (m > 0.5).astype(np.uint8)
    
    def get_foreground_mask(self, defaced_path: Path) -> np.ndarray:
        try:
            in_dir = self._prepare_single_input(defaced_path, "fg_input")
            pred_path = self._run_nnunet_predict(in_dir, "fg_pred", "Dataset803_anatomical_foreground_v2")
            fg, _, _ = self.load_nifti_data(Path(pred_path))
            fg = (fg > 0).astype(np.uint8)
            print("  ✓ 전경 마스크 생성 (Dataset803)")
            return fg
        except Exception as e:
            print(f"  ⚠ 전경 마스크 생성 실패: {e}")
            defaced_img, _, _ = self.load_nifti_data(defaced_path)
            thr = np.percentile(defaced_img, 5)
            m = defaced_img > thr
            lbl, n = ndimage.label(m)
            if n > 0:
                sizes = ndimage.sum(m, lbl, index=range(1, n+1))
                largest = 1 + int(np.argmax(sizes))
                m = (lbl == largest)
            m = ndimage.binary_fill_holes(m)
            print("  ✓ 전경 마스크 생성 (간이 방식)")
            return m.astype(np.uint8)
    
    @staticmethod
    def clip_to_roi(mask: np.ndarray, anchor_mask: np.ndarray, 
                    spacing: tuple, margin_mm: float = 30.0) -> np.ndarray:
        iters = tuple(max(1, int(np.ceil(margin_mm / s))) for s in spacing)
        s = ndimage.generate_binary_structure(3, 1)
        roi = ndimage.binary_dilation(anchor_mask.astype(bool), structure=s, 
                                     iterations=max(iters))
        return (mask.astype(bool) & roi).astype(np.uint8)
    
    @staticmethod
    def calculate_dsc(a: np.ndarray, b: np.ndarray) -> float:
        a = (a > 0).astype(np.float32)
        b = (b > 0).astype(np.float32)
        inter = np.sum(a * b)
        union = np.sum(a) + np.sum(b)
        if union == 0:
            return 1.0 if inter == 0 else 0.0
        return float(2.0 * inter / union)
    
    @staticmethod
    def surface_dsc(a: np.ndarray, b: np.ndarray, spacing: tuple, 
                   tol_mm: float = 5.0) -> float:
        s = ndimage.generate_binary_structure(3, 1)
        a = a.astype(bool)
        b = b.astype(bool)
        
        if not np.any(a) and not np.any(b):
            return 1.0
        if not np.any(a) or not np.any(b):
            return 0.0
        
        sa = a ^ ndimage.binary_erosion(a, s)
        sb = b ^ ndimage.binary_erosion(b, s)
        
        dt_a = ndimage.distance_transform_edt(~sa, sampling=spacing)
        dt_b = ndimage.distance_transform_edt(~sb, sampling=spacing)
        
        within_a = dt_b[sa] <= tol_mm
        within_b = dt_a[sb] <= tol_mm
        
        num = within_a.sum() + within_b.sum()
        den = sa.sum() + sb.sum()
        
        return float(num / max(den, 1))
    
    @staticmethod
    def hd95_dt(a: np.ndarray, b: np.ndarray, spacing: tuple) -> float:
        a = a.astype(bool)
        b = b.astype(bool)
        
        if not np.any(a) and not np.any(b):
            return 0.0
        if not np.any(a) or not np.any(b):
            return float('inf')
        
        s = ndimage.generate_binary_structure(3, 1)
        sa = a ^ ndimage.binary_erosion(a, s)
        sb = b ^ ndimage.binary_erosion(b, s)
        
        dt_a = ndimage.distance_transform_edt(~sa, sampling=spacing)
        dt_b = ndimage.distance_transform_edt(~sb, sampling=spacing)
        
        d_ab = dt_b[sa]
        d_ba = dt_a[sb]
        
        if d_ab.size == 0 or d_ba.size == 0:
            return float('inf')
        
        return float(np.percentile(np.hstack([d_ab, d_ba]), 95))
    
    def _global_rescale(self, raw_img: np.ndarray, defaced_img: np.ndarray, 
                       fg_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        fg = (fg_mask > 0)
        vals = raw_img[fg]
        
        if vals.size == 0:
            vals = raw_img.ravel()
        
        lo = np.percentile(vals, 1)
        hi = np.percentile(vals, 99)
        
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            lo, hi = float(np.min(vals)), float(np.max(vals))
            if hi <= lo:
                return raw_img.copy(), defaced_img.copy(), 1.0
        
        def scale(x):
            x = (x - lo) / (hi - lo)
            return np.clip(x, 0.0, 1.0)
        
        return scale(raw_img), scale(defaced_img), 1.0
    
    @staticmethod
    def calculate_ssim_masked(img1: np.ndarray, img2: np.ndarray, 
                             mask: np.ndarray) -> float:
        vals = []
        for z in range(img1.shape[2]):
            m = mask[:, :, z].astype(bool)
            if m.sum() < 25:
                continue
            
            yx = np.argwhere(m)
            (y0, x0), (y1, x1) = yx.min(0), yx.max(0)
            a = img1[y0:y1+1, x0:x1+1, z]
            b = img2[y0:y1+1, x0:x1+1, z]
            
            h, w = a.shape
            min_side = min(h, w)
            if min_side < 3:
                continue
            
            win = min(7, min_side)
            if win % 2 == 0:
                win -= 1
            win = max(3, win)
            
            if a.std() < 1e-8 or b.std() < 1e-8:
                continue
            
            vals.append(ssim(a, b, data_range=1.0, win_size=win))
        
        return float(np.mean(vals)) if vals else 1.0
    
    @staticmethod
    def calculate_psnr_masked(img1: np.ndarray, img2: np.ndarray, 
                             mask: np.ndarray, peak: float = 1.0) -> float:
        m = (mask > 0)
        if not np.any(m):
            return float('inf')
        
        diff = img1[m] - img2[m]
        mse = float(np.mean(diff * diff))
        
        if mse <= 0:
            return float('inf')
        
        return float(10.0 * np.log10((peak * peak) / mse))
    
    def verify_subject(self, subject_name: str, defaced_root: Path, 
                      raw_root: Path) -> Optional[Dict]:
        print(f"\n{'='*70}")
        print(f"Subject: {subject_name}")
        print(f"{'='*70}")
        
        subject_defaced_dir = defaced_root / subject_name
        defaced_nii = subject_defaced_dir / "defaced.nii.gz"
        defaced_mask = subject_defaced_dir / "defaced_mask.nii.gz"
        
        if not defaced_nii.exists():
            print(f"  ✗ Defaced NIfTI 파일 없음: {defaced_nii}")
            return None
        
        if not defaced_mask.exists():
            print(f"  ✗ Defaced mask 파일 없음: {defaced_mask}")
            return None
        
        print(f"  ✓ Defaced 파일 확인")
        
        raw_dicom_dir = self.find_raw_dicom_for_subject(subject_name, raw_root)
        
        if not raw_dicom_dir:
            print(f"  ✗ 원본 DICOM을 찾을 수 없습니다")
            return None
        
        print(f"  ✓ 원본 DICOM 발견: {raw_dicom_dir.relative_to(raw_root)}")
        
        self.temp_dir = tempfile.mkdtemp(prefix=f'verify_{subject_name}_')
        
        try:
            print(f"  [1/4] DICOM → NIfTI 변환")
            temp_nii_dir = Path(self.temp_dir) / "raw_nii"
            raw_nii = self.dcm2nii(raw_dicom_dir, temp_nii_dir)
            
            if not raw_nii:
                print(f"  ✗ NIfTI 변환 실패")
                return None
            
            print(f"  ✓ 변환 완료")
            
            print(f"  [2/4] 제거 영역 예측 (Dataset804)")
            def_in_dir = self._prepare_single_input(defaced_nii, "defaced_input")
            pred804_path = self._run_nnunet_predict(def_in_dir, "pred804", 
                                                    "Dataset804_SEG_defaced_areas_all_v2")
            pred_remove, _, _ = self.load_nifti_data(Path(pred804_path))
            PRED_REMOVE = (pred_remove > 0).astype(np.uint8)
            print(f"  ✓ 예측 완료")
            
            print(f"  [3/4] 전경 및 ROI 계산")
            defaced_img, _, def_hdr = self.load_nifti_data(defaced_nii)
            spacing = def_hdr.get_zooms()[:3]
            
            FG = self.get_foreground_mask(defaced_nii)
            KEEP = self.load_binary_mask_to_ref(defaced_mask, defaced_nii)
            
            TOOL_REMOVE = ((KEEP == 0) & (FG == 1)).astype(np.uint8)
            
            union_anchor = ((PRED_REMOVE == 1) | (TOOL_REMOVE == 1)).astype(np.uint8)
            ROI = self.clip_to_roi(np.ones_like(union_anchor), union_anchor, 
                                   spacing, margin_mm=self.ROI_MARGIN_MM)
            
            PRED_CLIP = ((PRED_REMOVE == 1) & (ROI == 1) & (FG == 1)).astype(np.uint8)
            TOOL_CLIP = ((TOOL_REMOVE == 1) & (ROI == 1) & (FG == 1)).astype(np.uint8)
            
            print(f"  ✓ ROI 계산 완료")
            
            print(f"  [4/4] 검증 지표 계산")
            raw_img, _, _ = self.load_nifti_data(raw_nii)
            raw_s, def_s, peak = self._global_rescale(raw_img, defaced_img, FG)
            
            dsc_surf = self.surface_dsc(PRED_CLIP, TOOL_CLIP, spacing, 
                                       tol_mm=self.SURFACE_TOL_MM)
            hd95 = self.hd95_dt(PRED_CLIP, TOOL_CLIP, spacing)
            
            def_region = TOOL_CLIP
            
            ssim_def = self.calculate_ssim_masked(raw_s, def_s, def_region)
            psnr_def = self.calculate_psnr_masked(raw_s, def_s, def_region, peak)
            
            passed = self._check_pass(dsc_surf, hd95, ssim_def, psnr_def)
            
            print(f"  ✓ 검증 지표 계산 완료")
            
            self._print_result(dsc_surf, hd95, ssim_def, psnr_def, passed)
            
            results = {
                'subject': subject_name,
                'surface_dsc': dsc_surf,
                'hd95_mm': hd95,
                'ssim_defaced': ssim_def,
                'psnr_defaced_db': psnr_def,
                'pred_voxels': int(PRED_CLIP.sum()),
                'tool_voxels': int(TOOL_CLIP.sum()),
                'passed': passed
            }
            
            return results
            
        except Exception as e:
            print(f"  ✗ 검증 실패: {e}")
            return None
            
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.temp_dir = None
    
    def _check_pass(self, dsc: float, hd95: float, ssim: float, psnr: float) -> bool:
        return (dsc >= self.TARGETS['surface_dsc'] and 
                hd95 <= self.TARGETS['hd95_mm'] and 
                ssim <= self.TARGETS['ssim_def'] and 
                psnr <= self.TARGETS['psnr_def_db'])
    
    def _print_result(self, dsc: float, hd95: float, ssim_def: float, 
                     psnr_def: float, passed: bool):
        print(f"\n  검증 지표:")
        print(f"    Surface DSC (@{self.SURFACE_TOL_MM}mm): {dsc:.4f}")
        print(f"    HD95 (mm):                   {hd95:.2f}")
        print(f"    SSIM (defaced):              {ssim_def:.4f}")
        print(f"    PSNR (defaced):              {psnr_def:.2f} dB")
        
        print(f"\n  품질 판정:")
        print(f"    Surface DSC {'✅' if dsc >= self.TARGETS['surface_dsc'] else '❌'} "
              f"(목표: ≥{self.TARGETS['surface_dsc']:.2f})")
        print(f"    HD95        {'✅' if hd95 <= self.TARGETS['hd95_mm'] else '❌'} "
              f"(목표: ≤{self.TARGETS['hd95_mm']:.2f} mm)")
        print(f"    SSIM(def)   {'✅' if ssim_def <= self.TARGETS['ssim_def'] else '❌'} "
              f"(목표: ≤{self.TARGETS['ssim_def']:.2f})")
        print(f"    PSNR(def)   {'✅' if psnr_def <= self.TARGETS['psnr_def_db'] else '❌'} "
              f"(목표: ≤{self.TARGETS['psnr_def_db']:.2f} dB)")
        
        print(f"\n  최종 결과: {'✅ PASS' if passed else '❌ FAIL'}")


def save_results_to_excel(results: List[Dict], output_path: Path):
    workbook = xlsxwriter.Workbook(str(output_path))
    
    bold_format = workbook.add_format({'bold': True})
    pass_format = workbook.add_format({'font_color': 'green'})
    fail_format = workbook.add_format({'font_color': 'red'})
    pass_bold_format = workbook.add_format({'bold': True, 'font_color': 'green'})
    fail_bold_format = workbook.add_format({'bold': True, 'font_color': 'red'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
    criteria_format = workbook.add_format({'bold': True})
    
    worksheet = workbook.add_worksheet('의료영상 얼굴 정보 익명화 검증 결과')
    
    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 12)
    worksheet.set_column('C:L', 15)
    
    row = 0
    worksheet.write(row, 0, '검증 기준', criteria_format)
    row += 1
    
    targets = DefacingVerifier.TARGETS
    
    worksheet.write(row, 0, f"DSC(mm)", bold_format)
    worksheet.write(row, 1, targets['surface_dsc'])
    row += 1
    
    worksheet.write(row, 0, f"HD95(mm)", bold_format)
    worksheet.write(row, 1, targets['hd95_mm'])
    row += 1
    
    worksheet.write(row, 0, f"SSIM", bold_format)
    worksheet.write(row, 1, targets['ssim_def'])
    row += 1
    
    worksheet.write(row, 0, f"PSNR(dB)", bold_format)
    worksheet.write(row, 1, targets['psnr_def_db'])
    row += 2
    
    headers = [
        'SUBJECT 명', '최종결과', 
        'DSC(mm)', 'DSC 만족 유무',
        'HD95(mm)', 'HD95 만족 유무',
        'SSIM', 'SSIM 만족 유무',
        'PSNR(dB)', 'PSNR 만족 유무'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(row, col, header, header_format)
    row += 1
    
    for result in results:
        col = 0
        
        worksheet.write(row, col, result['subject'])
        col += 1
        
        final_pass = result['passed']
        if final_pass:
            worksheet.write(row, col, 'PASS', pass_bold_format)
        else:
            worksheet.write(row, col, 'FAIL', fail_bold_format)
        col += 1
        
        dsc = result['surface_dsc']
        worksheet.write(row, col, round(dsc, 4))
        col += 1
        dsc_pass = dsc >= targets['surface_dsc']
        worksheet.write(row, col, 'PASS' if dsc_pass else 'FAIL',
                      pass_format if dsc_pass else fail_format)
        col += 1
        
        hd95 = result['hd95_mm']
        worksheet.write(row, col, round(hd95, 2))
        col += 1
        hd95_pass = hd95 <= targets['hd95_mm']
        worksheet.write(row, col, 'PASS' if hd95_pass else 'FAIL',
                      pass_format if hd95_pass else fail_format)
        col += 1
        
        ssim_val = result['ssim_defaced']
        worksheet.write(row, col, round(ssim_val, 4))
        col += 1
        ssim_pass = ssim_val <= targets['ssim_def']
        worksheet.write(row, col, 'PASS' if ssim_pass else 'FAIL',
                      pass_format if ssim_pass else fail_format)
        col += 1
        
        psnr = result['psnr_defaced_db']
        worksheet.write(row, col, round(psnr, 2))
        col += 1
        psnr_pass = psnr <= targets['psnr_def_db']
        worksheet.write(row, col, 'PASS' if psnr_pass else 'FAIL',
                      pass_format if psnr_pass else fail_format)
        
        row += 1
    
    workbook.close()
    print(f"\n✅ 검증 결과 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='FaceOff Defacing 검증',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--defaced', '-d',
        type=Path,
        required=True,
        help='Defaced 결과가 있는 루트 디렉토리'
    )
    
    parser.add_argument(
        '--raw', '-r',
        type=Path,
        required=True,
        help='원본 DICOM이 있는 루트 디렉토리'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='검증 결과를 저장할 디렉토리 (선택)'
    )
    
    parser.add_argument(
        '--subjects',
        nargs='+',
        help='검증할 특정 subject 이름들 (생략 시 모두 검증)'
    )
    
    parser.add_argument(
        '--gpu',
        type=int,
        default=0,
        help='사용할 GPU ID (기본: 0)'
    )
    
    args = parser.parse_args()
    
    if not args.defaced.exists():
        print(f"❌ Defaced 디렉토리가 없습니다: {args.defaced}")
        return 1
    
    if not args.raw.exists():
        print(f"❌ Raw 디렉토리가 없습니다: {args.raw}")
        return 1
    
    print("="*70)
    print("FaceOff Defacing 검증 파이프라인")
    print("="*70)
    print(f"Defaced: {args.defaced}")
    print(f"Raw:     {args.raw}")
    print(f"GPU:     {args.gpu}")
    
    subjects = []
    for item in args.defaced.iterdir():
        if item.is_dir():
            if args.subjects and item.name not in args.subjects:
                continue
            
            if (item / "defaced.nii.gz").exists():
                subjects.append(item.name)
    
    if not subjects:
        print("\n❌ 검증할 subject를 찾을 수 없습니다")
        return 1
    
    print(f"\n📊 총 {len(subjects)}개 subject 발견\n")
    
    verifier = DefacingVerifier(gpu_id=args.gpu)
    all_results = []
    success = 0
    failed = 0
    
    for i, subject_name in enumerate(subjects, 1):
        print(f"\n[{i}/{len(subjects)}] 검증 중...")
        
        result = verifier.verify_subject(subject_name, args.defaced, args.raw)
        
        if result:
            all_results.append(result)
            success += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print("검증 완료")
    print(f"{'='*70}")
    print(f"총 subjects: {len(subjects)}")
    print(f"성공: {success}")
    print(f"실패: {failed}")
    
    if all_results:
        pass_count = sum(1 for r in all_results if r['passed'])
        
        print(f"\n통과율: {pass_count}/{len(all_results)} "
              f"({pass_count/len(all_results)*100:.1f}%)")
        
        excel_path = Path("dicom_deface_verification.xlsx")
        save_results_to_excel(all_results, excel_path)
    
    print(f"{'='*70}\n")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
