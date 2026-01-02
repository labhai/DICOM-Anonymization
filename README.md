
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
This repository is organized into two main components: dicom_anonymizer and dicom_verifier.  
Each component provides its own detailed installation and usage instructions.  

For DICOM anonymization (header anonymization and facial defacing), refer to the README file inside the dicom_anonymizer/ directory.  

For DICOM anonymization verification (header verification and facial defacing verification), refer to the README file inside the dicom_verifier/ directory.  

Each submodule README includes:
- Required environment
- installation instructions
- Detailed command-line usage examples
- Option descriptions and output formats


## Example & Test Dataset (Demo Data)

⚠️ No Test DICOM data is provided in this repository due to privacy and regulatory restrictions.

