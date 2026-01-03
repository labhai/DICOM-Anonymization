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

1. Launch the RSNA DICOM Anonymizer tool (Main screen)  
   <img src="https://github.com/user-attachments/files/24415758/rsna-1.bmp" width="300"/>
   
2. Create Project  
   - From the top menu bar, File → New Project  
   <img src="https://github.com/user-attachments/files/24415809/rsna-2.bmp" width="200"/>

3. Configure Project  
   - Project Name  
   - UID Root (affects generated DICOM UIDs)  
   - Storage Directory (output path)  
   - Modalities (CR, DX, CT, MR, etc.)
   - Select Script File  
     - Low-level anonymization (**dicom_header_anonymizer_low_level.script**)  
     - High-level anonymization (**dicom_header_anonymizer_high_level.script**)  
   <img src="https://github.com/user-attachments/files/24415815/rsna-3.bmp" width="300"/>

4. Import DICOM Files  
   - From the top menu bar, Import Files or Import Directory  

5. Run Anonymization  
   - Progress and logs shown in GUI  
   <img src="https://github.com/user-attachments/assets/0e9cf9fc-93b4-4d7d-b436-e192b54a8be8" width="400"/>
  
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

