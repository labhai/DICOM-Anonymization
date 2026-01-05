# DICOM Anonymization (`dicom_anonymizer`)
This module provides tools for DICOM data anonymization, covering both header anonymization and facial information defacing.

## DICOM Anonymization Overview

### Header anonymization overview
DICOM header anonymization is performed based on established privacy standards, including the HIPAA(Health Insurance Portability and Accountability Act) Safe Harbor method and DICOM PS3.15 Attribute Confidentiality Profiles, which define how identifying metadata should be removed, replaced, or generalized to reduce re-identification risk.  
Header fields are classified by re-identification risk, and different anonymization rules are applied depending on the selected anonymization level (low or high).  
- **Target Fields for Header Anonymization**  
  The following table summarizes representative header fields targeted for anonymization and how they are handled at each level.
  (This is a simplified overview; the full policy is defined in the script files.)  
  | Field Category | DICOM Tags (examples) | Low-level Policy | High-level Policy |
  | -------------- | ------------------ | ---------------- | ----------------- |
  | absolute identifiers     | Patient Name, Birth Date, Address | Removed            | Removed              |
  | Patient identifier       | Patient ID                        | Replaced with hash | Removed              |
  | Dates & times            | Study Date, Acquisition Date      | Replaced with hash | Removed              |
  | Institution & staff info | Institution Name, Physician Name  | Removed            | Removed              |
  | Quasi-identifiers        | Age, Weight, Body Part Thickness  | Preserved          | Generalized (binned) |
  | Low-risk attributes      | Sex                               | Preserved          | Preserved            |
- **Anonymization Levels**  
    - Low-level anonymization  
      Prioritizing privacy protection while preserving key metadata needed for analysis and longitudinal linkage.
    - High-level anonymization  
      Applying stricter removal or generalization rules to further reduce re-identification risk.  

### Facial information anonymization overview  
Facial information anonymization is applied to head(face)-related DICOM images (e.g., head CT, brain MRI), where facial contours may remain visible in pixel data even after complete header anonymization.  
To mitigate this risk, pixel-level facial defacing is performed to remove external facial features while preserving internal anatomical structures relevant for research and analysis.  
- **Target Regions for Facial Anonymization**  
  The anonymization process focuses on removing externally identifiable facial structures, while minimizing impact on clinically relevant regions.  
  | Category | Target Regions | Anonymization Strategy |
  | -------- | -------------- | ---------------------- |
  | Facial surface     | Eyes, nose, mouth, skin surface            | Defaced |
  | Facial soft tissue | Cheeks, lips, periorbital region           | Defaced |
  | Internal anatomy   | Brain, skull base, intracranial structures | Preserved |
- **Anonymization Levels**  
    - Low-level anonymization  
      Facial defacing is not applied at this level. This setting assumes a controlled internal research environment (e.g., within a single institution with restricted access), where DICOM header anonymization alone is sufficient to mitigate re-identification risk.  
      Omitting facial defacing at the low-level anonymization stage preserves anatomically surface information, thereby minimizing potential research loss in studies such as craniofacial morphology analysis or surface-based morphometry. For this reason, facial defacing is intentionally excluded from the default low-level policy and is applied only when explicitly required by the selected anonymization workflow.  
    - High-level anonymization  
      Facial defacing is applied for head(face)-related images intended for external sharing or multi-institutional use, where re-identification risk is higher.  

This anonymization policy design allows flexible adjustment of anonymization strength according to the data sharing scope and re-identification risk, while balancing privacy protection and data usability.


## Directory contains

- `dicom_header_anonymizer_high_level.script`  
  High-level RSNA DICOM Anonymizer script for aggressive header anonymization.

- `dicom_header_anonymizer_low_level.script`  
  Low-level RSNA DICOM Anonymizer script for conservative header anonymization.

- `dicom_deface_anonymizer.py`  
  Performs facial information anonymization (defacing) on head-related DICOM images.

- `dicom_deface_anonymizer.sh`  
  Sets up the Conda environment and installs dependencies for facial anonymization.

## What this script does

### 1. Header anonymization (RSNA DICOM Anonymizer)
- Script-based anonymization using RSNA DICOM Anonymizer
- Two anonymization levels:
  - Low-level: dicom_header_anonymizer_low_level.script
  - High-level: dicom_header_anonymizer_high_level.script
- GUI-based workflow (Windows)

### 2. Facial information anonymization (dicom_deface_anonymizer.py)
- Automated 3D facial defacing for head-related DICOM images
- Conda-based environment

## Usage

### 1. Header anonymization (RSNA DICOM Anonymizer) 

**Usage**
  ```
  rsna-anonymizer
  ```

**Workflow**

1. Launch the RSNA DICOM Anonymizer tool (Main screen)  
   <img src="https://github.com/user-attachments/files/24415758/rsna-1.bmp" width="300"/>
   
2. Create Project  
   <img src="https://github.com/user-attachments/files/24415809/rsna-2.bmp" width="150"/>
   - Select File → New Project from the top menu bar

3. Configure Project  
   <img src="https://github.com/user-attachments/files/24415815/rsna-3.bmp" width="250"/>
   - Project Name  
   - UID Root (affects generated DICOM UIDs)  
   - Storage Directory (output path)  
   - Modalities (CR, DX, CT, MR, etc.)
   - Select Script File  
     - Low-level anonymization (**dicom_header_anonymizer_low_level.script**)  
     - High-level anonymization (**dicom_header_anonymizer_high_level.script**)  

4. Import DICOM Files  
   <img src="https://github.com/user-attachments/assets/f685abd7-5321-4201-9deb-1cf98fb9c91c" width="150"/>
   - Select File → Import Files or Import Directory from the top menu bar

5. Run Anonymization  
   <img src="https://github.com/user-attachments/assets/0e9cf9fc-93b4-4d7d-b436-e192b54a8be8" width="400"/>
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
  
  
  
**References**  
NEMA. *DICOM Standard PS3.15 — Security and System Management Profiles.* DICOM Standards Committee, https://dicom.nema.org/medical/dicom/current/output/chtml/part15/PS3.15.html. Accessed 2025.

