
# DICOM Anonymization

This repository provides a comprehensive DICOM anonymization and validation pipeline covering both DICOM header anonymization and facial information defacing, along with verification tools to ensure anonymization integrity.

## Features

### Anonymization (`dicom_anonymizer`)
#### 1. Header anonymization (RSNA DICOM Anonymizer)

- Script-based anonymization using RSNA DICOM Anonymizer
- Two anonymization levels:
  - Low-level: dicom_header_anonymizer_low_level.script
  - High-level: dicom_header_anonymizer_high_level.script
- GUI-based workflow (Windows)

#### 2. Facial information anonymization (dicom_deface_anonymizer.py)
- Automated 3D facial defacing for head-related DICOM images
- Conda-based environment

### Validation (`dicom_verifier`)

#### 1. Header anonymization verification (dicom_header_verifier.py)
- Low / High-level criteria support
- Excel-based verification reports

#### 2. Facial defacing verification (dicom_deface_verifier.py)
- Deep-learning-based verification (nnUNet)
- Conda-based environment
- Reference: Nohel, Michal, et al. "Unified Framework for Foreground and Anonymization Area Segmentation in CT and MRI Data." BVM Workshop. Wiesbaden: Springer Fachmedien Wiesbaden, 2025.


### Repository Structure
```
├── dicom_anonymizer
│   ├── dicom_header_anonymizer_high_level.script        # Header anonymization (high-level)
│   ├── dicom_header_anonymizer_low_level.script         # Header anonymization (low-level)
│   ├── dicom_deface_anonymizer.py          # Facial anonymization
│   └── dicom_deface_anonymizer.sh          # Facial anonymization environment setup
│
├── dicom_verifier
│   ├── dicom_header_verifier.py            # Header anonymization verifier
│   ├── dicom_header_verifier.sh            # Header verifier environment setup
│   ├── dicom_deface_verifier.py             # Facial anonymization verifier
│   └── dicom_deface_verifier.sh             # Facial verifier environment setup

```

## Installation and Usage

### Anonymization

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

**Usage**
  ```
  rsna-anonymizer
  ```

**Workflow**
1. Create Project  
   - File → New Project  

2. Configure Project  
   - Project Name  
   - UID Root (affects generated DICOM UIDs)  
   - Storage Directory (output path)  
   - Modalities (CR, DX, CT, MR, etc.)  

3. Select Script File  
   - Low-level anonymization (**dicom_header_anonymizer_low_level.script**)  
   - High-level anonymization (**dicom_header_anonymizer_high_level.script**)  

4. Import DICOM Files  
   - Import Files or Import Directory  

5. Run Anonymization  
   - Progress and logs shown in GUI  


#### 2. Facial information anonymization 

**Environment**
- OS: Ubuntu 22.04
- Conda required

**Installation**
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_anonymizer
  bash dicom_deface_anonymizer.sh
  ```
- Verify installation:
  ```
  faceoff -h 2>/dev/null
  ```

**Usage**
Basic anonymization:
  ```
  python dicom_deface_anonymizer.py \
    --input /path/to/root \
    --output /path/to/output
  ```

- Specific subjects only:
  ```
  python dicom_deface_anonymizer.py \
    --input /path/to/root \
    --output /path/to/output \
    --subjects sub001 sub002
  ```

### Validation

#### 1. Header anonymization verification

**Environment**
- OS: Ubuntu 22.04
- Python >= 3.8

**Installation**
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_verifier
  bash dicom_header_verifier.sh
  ```

**Usage**
- Basic verification:
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom
  ```

- Specify anonymization level (low/high)
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom \
    --option high
  ```

- change output filename (default: dicom_header_verification.xlsx)
  ```
  python dicom_header_verifier.py \
    --input /path/to/dicom \
    --option low \
    --output /path/to/results/results.xlsx
  ```

#### 2. Facial defacing verification 

**Environment**
- OS: Ubuntu 22.04
- Conda required


**Installation**
  ```
  git clone https://github.com/labhai/DICOM-Anonymization
  cd dicom_verifier
  bash dicom_deface_verifier.sh
  ```

**Usage**
- Basic verification:
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw
  ```

- Specify GPU (default: GPU 0):
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw \
    --gpu 2
  ```

- Specific subjects & change output filename (default: dicom_deface_verification.xlsx):
  ```
  python dicom_deface_verifier.py \
    --defaced /path/to/defaced \
    --raw /path/to/raw \
    --subjects sub001 sub002 \
    --output /path/to/results/results.xlsx
  ```

## Example & Test Dataset (Demo Data)

⚠️ No Test DICOM data is provided in this repository due to privacy and regulatory restrictions.

