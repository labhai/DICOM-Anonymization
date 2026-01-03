
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

#### 2. Facial information anonymization (dicom_deface_anonymizer)
- Automated 3D facial defacing for head-related DICOM images
- Conda-based environment

### Verification (`dicom_verifier`)

#### 1. Header anonymization verification (dicom_header_verifier)
- Low / High-level criteria support
- Excel-based verification reports

#### 2. Facial defacing verification (dicom_deface_verifier)
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

**Usage**
  ```
  rsna-anonymizer
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

**Usage**  
Run commands from the directory where dicom_deface_anonymizer.py exists.

- Basic anonymization:
  ```
  python dicom_deface_anonymizer.py \
    --input /path/to/root \
    --output /path/to/output
  ```

### Verification  
For DICOM anonymization verification (header verification and facial defacing verification), refer to the README file inside the dicom_verifier/ directory.  

#### 1. Header anonymization verification

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

#### 2. Facial defacing verification 

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


## Example & Test Dataset (Demo Data)

⚠️ No Test DICOM data is provided in this repository due to privacy and regulatory restrictions.

