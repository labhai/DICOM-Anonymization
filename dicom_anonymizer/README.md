# DICOM Anonymization (`dicom_anonymizer`)
## 1. Header anonymization (RSNA DICOM Anonymizer)

- Script-based anonymization using RSNA DICOM Anonymizer
- Two anonymization levels:
  - Low-level: dicom_header_anonymizer_low_level.script
  - High-level: dicom_header_anonymizer_high_level.script
- GUI-based workflow (Windows)

## 2. Facial information anonymization (dicom_deface_anonymizer.py)
- Automated 3D facial defacing for head-related DICOM images
- Conda-based environment

## Repository Structure
```
├── dicom_anonymizer
│   ├── dicom_header_anonymizer_high_level.script        # Header anonymization (high-level)
│   ├── dicom_header_anonymizer_low_level.script         # Header anonymization (low-level)
│   ├── dicom_deface_anonymizer.py          # Facial anonymization
│   └── dicom_deface_anonymizer.sh          # Facial anonymization environment setup
```

## Installation and Usage

### 1. Header anonymization (RSNA DICOM Anonymizer) 

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


### 2. Facial information anonymization 

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

- Specific subjects only:
  ```
  python dicom_deface_anonymizer.py \
    --input /path/to/root \
    --output /path/to/output \
    --subjects sub001 sub002
  ```

**Options**
- ```--input```: Path to the top-level input directory containing subjects folders (raw DICOM datasets).
- ```--output```: Path to the output directory where defaced results will be written.
- ```--subjects```: *(Optional)* List of subject IDs to process. (If omitted, the tool processes all subjects found under --input.)

**Output Structure**  
Each subject produces a dedicated output folder:
  ```
  output/
  └── subject_id/
      ├── defaced.nii.gz          # Defaced NIfTI
      ├── defaced_mask.nii.gz     # Defacing mask
      └── defaced_dicom/          # Defaced DICOM series
          ├── slice_001.dcm
          ├── slice_002.dcm
          └── ...
  ```

