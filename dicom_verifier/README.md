# DICOM Verification (`dicom_verifier`)
This module provides verification tools to validate the integrity of DICOM anonymization results, covering both header anonymization and facial defacing.
Verification results are exported as Excel reports for downstream review.

## 1. Header anonymization verification

**Environment**
- OS: Ubuntu 22.04
- Python >= 3.8

**Installation**  
Clone this repository and run the setup script to install the required Python dependencies:
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_verifier
  bash dicom_header_verifier.sh
  ```
If you encounter a permission error:
  ```
  chmod +x dicom_header_verifier.sh
  bash dicom_header_verifier.sh
  ```

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
- An Excel file summarizing anonymization compliance for each inspected DICOM file.
- The report includes tag-level verification results based on the selected anonymization level.


## 2. Facial defacing verification 

**Environment**
- OS: Ubuntu 22.04
- Conda required
- CUDA-enabled GPU recommended (for nnUNet-based verification)


**Installation**
Clone this repository and run the setup script.  
The script will automatically create a Conda environment and install the nnUNet model.
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_verifier
  bash dicom_deface_verifier.sh
  ```
At the final step, you may be prompted to remove downloaded archives to save disk space.  
After installation, activate the generated Conda environment:
  ```
  conda activate dicom_deface_verify
  ```

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
- An Excel file summarizing facial defacing verification results for each subject.
- The report evaluates the adequacy of facial anonymization by comparing raw and defaced DICOM data.
- Verification results are generated using a deep-learning-based segmentation model (nnUNet) to evaluate whether facial regions have been sufficiently anonymized.

**Reference**  
Nohel, Michal, et al. "Unified Framework for Foreground and Anonymization Area Segmentation in CT and MRI Data." BVM Workshop. Wiesbaden: Springer Fachmedien Wiesbaden, 2025.

