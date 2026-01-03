# DICOM Anonymization (`dicom_anonymizer`)
This module provides tools for DICOM data anonymization, covering both header anonymization and facial information defacing.

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

**Usage**
  ```
  rsna-anonymizer
  ```

**Workflow**

1. rsna anonymizer 도구 실행 시 메인화면
  <img src="https://github.com/user-attachments/files/24415758/rsna-1.bmp" width="200" height="400"/>
   
3. Create Project  
   - File → New Project

4. Configure Project  
   - Project Name  
   - UID Root (affects generated DICOM UIDs)  
   - Storage Directory (output path)  
   - Modalities (CR, DX, CT, MR, etc.)
   - Select Script File  
     - Low-level anonymization (**dicom_header_anonymizer_low_level.script**)  
     - High-level anonymization (**dicom_header_anonymizer_high_level.script**)  


5. Import DICOM Files  
   - Import Files or Import Directory  

6. Run Anonymization  
   - Progress and logs shown in GUI
  
**Output**
- Anonymized DICOM files are written to the configured Storage Directory.
- The directory structure of the input data is preserved in the output.


### 2. Facial information anonymization 

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

**Output**  
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

