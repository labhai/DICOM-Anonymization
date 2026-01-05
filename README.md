
# DICOM Anonymization

This repository provides a comprehensive DICOM anonymization and validation pipeline covering both DICOM header anonymization and facial information defacing, along with verification tools to ensure anonymization integrity. It is designed for researchers, hospitals, and organizations that need to safely share medical imaging data while complying with privacy regulations.

### What Is DICOM?  
**DICOM (Digital Imaging and Communications in Medicine)** is the universal standard format used for medical images such as X-rays, CT, and MRI.  
A DICOM file contains not only the image itself but also extensive metadata in its header, including patient information (e.g., name, ID, date of birth, sex), examination details (e.g., acquisition date and time), as well as medical institution and imaging device information. Because image data and metadata are stored together in a single file, DICOM files are highly informative—but also potentially sensitive.  

### Why Anonymization Is Necessary
- **Header Anonymization**  
  DICOM headers contain patient identifiers and quasi-identifiers such as names, IDs, dates, and institution information. If not properly anonymized, these fields can enable re-identification, especially when data are shared across institutions or combined with external records. Therefore, anonymizing DICOM header metadata is essential before any data sharing or secondary use.  
  
- **Facial Information Anonymization**  
  Head CT and brain MRI images may include facial structures that can reveal a person’s identity, even when all header information has been removed. With advances in 3D reconstruction and facial recognition, such images pose a growing privacy risk. As a result, pixel-level facial defacing is required to ensure robust protection of patient privacy.

## Repository Structure

### `dicom_anonymizer`
#### 1. Header anonymization (RSNA DICOM Anonymizer)

- Script-based anonymization using RSNA DICOM Anonymizer
- Two anonymization levels:
  - Low-level: dicom_header_anonymizer_low_level.script
  - High-level: dicom_header_anonymizer_high_level.script
- GUI-based workflow (Windows only)
- Applicable to all DICOM modalities and imaging domains (e.g., CT, X-ray, MRI, brain, chest), with users selecting the appropriate anonymization script based on their use case.

#### 2. Facial information anonymization (dicom_deface_anonymizer)
- Automated 3D facial defacing for head-related DICOM images (e.g., head CT, brain MRI)
  - Not applied to non-head domains such as chest or abdominal imaging
- Conda-based environment

### `dicom_verifier`

#### 1. Header verification (dicom_header_verifier)
- Low / High-level criteria support
- Excel-based verification reports

#### 2. Facial information verification (dicom_deface_verifier)
- Deep-learning-based verification (nnUNet)
- Conda-based environment
- Reference: Nohel, Michal, et al. "Unified Framework for Foreground and Anonymization Area Segmentation in CT and MRI Data." BVM Workshop. Wiesbaden: Springer Fachmedien Wiesbaden, 2025.

## Requirements and Installation

### Anonymization  
For DICOM anonymization (header anonymization and facial defacing), refer to the README file inside the dicom_anonymizer/ directory.  

#### 1. Header anonymization (RSNA DICOM Anonymizer) 

**Environment**
- OS: Windows
- Python: 3.12 (recommended)
- GUI support required

- Verify Python installation:
  ```
  python --version
  python -m tkinter
  ```

**Installation**
  ```
  pip install rsna-anonymizer
  ```

#### 2. Facial information anonymization 

**Environment**
- OS: Ubuntu 22.04
- Conda required (used to install Python + ANTs dependencies)

**Installation**  
Clone this repository and run the setup script.  
The script will automatically create a Conda environment and install FaceOff (and required dependencies such as ANTs).
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_anonymizer
  bash dicom_deface_anonymizer.sh
  ```
After installation, verify that tool is available:
  ```
  faceoff -h 2>/dev/null
  ```
If the help message is printed correctly, FaceOff is ready to use.  
Then activate the generated Conda environment (example):
  ```
  conda activate dicom_deface_anonymizer
````

### Verification  
For DICOM anonymization verification (header verification and facial defacing verification), refer to the README file inside the dicom_verifier/ directory.  

#### 1. Header verification

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

#### 2. Facial information verification 

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

## Example (Quickstart)

### Header anonymization
```bash
rsna-anonymizer
```

### Header verification
```bash
python dicom_header_verifier.py \
  --input /path/to/dicom
```

### Facial information anonymization
```bash
python dicom_deface_anonymizer.py \
  --input /path/to/root \
  --output /path/to/output
```

### Facial information verification
```bash
python dicom_deface_verifier.py \
  --defaced /path/to/defaced \
  --raw /path/to/raw
```

## Test Dataset (Demo Data)

⚠️ No Test DICOM data is provided in this repository due to privacy and regulatory restrictions.

