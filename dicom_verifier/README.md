# DICOM Verification (`dicom_verifier`)
This module provides verification tools to validate the integrity of DICOM anonymization results, covering both header anonymization and facial defacing.
Verification results are exported as Excel reports for downstream review.

## Directory contains
```
├── dicom_verifier
│   ├── dicom_header_verifier.py            # Header anonymization verifier
│   ├── dicom_header_verifier.sh            # Header verifier environment setup
│   ├── dicom_deface_verifier.py             # Facial anonymization verifier
│   └── dicom_deface_verifier.sh             # Facial verifier environment setup
```

## What this script does

### 1. Header anonymization verification (dicom_header_verifier.py)
- Verification of DICOM header anonymization compliance
- Supports both low-level and high-level anonymization criteria
- Inspects DICOM tags and generates results in an Excel report

### 2. Facial defacing verification (dicom_deface_verifier.py)
- Verification of facial defacing adequacy in DICOM images
- Compares raw and defaced DICOM datasets at the subject level
- Uses a deep-learning-based segmentation model (nnUNet) for verification
- Generates verification results in an Excel report


## Usage  

### 1. Header anonymization verification

**Usage**
Run commands from the directory where dicom_header_verifier.py exists.  

- Basic verification (default: low-level criteria):
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom
  ```

- Specify anonymization level (low/high): 
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom \
    --option high
  ```

- Change output filename (default: dicom_header_verification.xlsx):
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom \
    --option low \
    --output /path/to/results/results.xlsx
  ```

**Options**
- ```--input```: Path to a DICOM file or a top-level directory containing DICOM files to be verified.
- ```--option```: *(Optional)* Verification level to apply.
  - ```low```(default): low-level header verification criteria
  - ```high```: high-level header verification criteria
- ```--output```: *(Optional)* Path and filename of the output Excel report.
  - Default: `dicom_header_verification.xlsx`

 
**Output**  
Verification results are saved as an Excel (.xlsx) file.  
The Excel report is composed of one summary sheet and multiple per-file detail sheets, enabling both dataset-level monitoring and file-level inspection.  

***1) Summary Sheet: Overall Verification Summary***  
The first sheet provides an integrated overview of all inspected DICOM files, allowing quick identification of files that pass or fail the anonymization policy.  
- The summary sheet includes, for each file:
    - Total number of inspected DICOM tags
    - Number of passed tags
    - Number of warning tags
    - Non-anonymization rate (%)
    - Verification result for absolute anonymization fields
    - Final decision (PASS / FAIL)  
This sheet enables rapid comparison across files and immediate identification of files requiring additional review.

- Definition of Summary Metrics

  | Metric | Description |  
  |------|-------------|  
  | `Total number of inspected DICOM tags` | The total count of DICOM header tags evaluated for anonymization compliance in a given file. |  
  | `Number of passed tags` | The number of tags that fully satisfy the anonymization policy (properly anonymized or allowed to remain unchanged). |  
  | `Number of warning tags` | The number of tags that do not strictly satisfy the anonymization policy but are classified as non-critical, resulting in a warning rather than an immediate failure. |  
  | `Non-anonymization rate (%)` | The proportion of tags that failed anonymization relative to the total number of inspected tags, expressed as a percentage. This value is used to assess overall anonymization adequacy at the file level. |  
  | `Verification result for absolute anonymization fields` | Indicates whether all *absolute anonymization fields* (i.e., tags that must always be anonymized under any policy) have been successfully anonymized. Any failure in these fields results in an automatic ***FAIL***. |  
  | `Final decision (PASS / FAIL)` | The overall verification outcome for the file. A file is marked ***PASS*** if it satisfies the absolute anonymization requirements and its non-anonymization rate is below the predefined threshold; otherwise, it is marked ***FAIL***. |  


***2) Per-file Sheets: Individual DICOM Verification Results***  
Each DICOM file has a dedicated sheet containing detailed verification results.  
- Top summary section
    - Number of passed and warning tags
    - Non-anonymization rate
    - Final decision (PASS / FAIL)
  
- Absolute anonymization field table
    - Lists all absolute anonymization tags
    - Indicates anonymization status (True / False) for each tag
    - Allows quick checking of failures caused by a single unprocessed critical tag
  
- Tag-level detailed verification table
    - DICOM tag
    - Original value
    - Verification status (PASS / WARNING)
    - Reason for warning (if applicable)
  
This structure enables fine-grained analysis of which specific tags failed and why, supporting policy refinement and corrective processing.


### 2. Facial defacing verification 

**Usage**
Run commands from the directory where dicom_deface_verifier.py exists.  

- Basic verification:
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw
  ```

- Specific subjects only:
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw \
    --subjects sub001 sub002
  ```
  
- Change output filename (default: dicom_deface_verification.xlsx):
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw \
    --output /path/to/results/results.xlsx
  ```
  
- Specify GPU (default: GPU 0):
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw \
    --gpu 2
  ```

**Options**
- ```--defaced```: Path to the top-level directory containing the defaced DICOM dataset (output of facial anonymization).
- ```--raw```: Path to the top-level directory containing the original (raw) DICOM dataset used as reference.
- ```--subjects```: *(Optional)* List of subject IDs to verify. (If omitted, all subjects under ```--defaced``` are processed.)
- ```--output```: *(Optional)* Path and filename of the output Excel verification report.
    - default: ```dicom_deface_verification.xlsx```
- ```--gpu```: *(Optional)* GPU device index to use for verification.
    - Default: GPU 0

**Output**
Facial defacing verification results are saved as an Excel (.xlsx) file, summarizing quantitative evaluation metrics for each subject.

***1) Summary Sheet: Facial Defacing Verification Results***
The main sheet presents subject-level verification results in tabular form.
- For each subject, the report includes:
    - DSC (Dice Similarity Coefficient)
    - HD95 (95th percentile Hausdorff Distance, mm)
    - SSIM (Structural Similarity Index)
    - PSNR (Peak Signal-to-Noise Ratio, dB)
    - Pass/Fail decision for each metric based on predefined thresholds
    - Final verification result (PASS / FAIL)  
  
At the top of the sheet, the applied threshold criteria are explicitly listed, e.g.:  
  - DSC ≥ 0.80
  - HD95 ≤ 30.0 mm
  - SSIM ≤ 0.80
  - PSNR ≤ 10.0 dB  

The following metrics are used to quantify both the spatial coverage of facial defacing and the degree of visual information destruction:
  - High DSC and low HD95 indicate that the defaced region sufficiently overlaps with the facial region detected by the verification model.
  - Low SSIM and PSNR values confirm that facial texture information has been effectively destroyed, reducing re-identification risk.
  - Subjects satisfying all metric thresholds are automatically marked as PASS, while any threshold violation results in FAIL.

This allows reviewers to immediately understand the evaluation standards used.


**Reference**  
Nohel, Michal, et al. "Unified Framework for Foreground and Anonymization Area Segmentation in CT and MRI Data." BVM Workshop. Wiesbaden: Springer Fachmedien Wiesbaden, 2025.

