# Maya Arnold RenderManager
An easy-to-use script that streamlines Arnold batch rendering and sequence validation in production pipelines. 

# Process
- PySide2-based Maya tool with two core functions: Render Sequence and Validate Sequence. 

  ### Render Sequence
  - Custom camera selection, frame range, and resolution controls 
  - Multi-AOV setup: Beauty, Diffuse, Specular, SSS, Transmission, AO, Emission, Z 
  - Frame-by-frame rendering with real-time progress tracking bar 
  - Automatic scene save before rendering starts 
  - Auto-sets validation path after render completes 

  ### ValidateSequence
  - Scans output directory against expected frame range 
  - Detects missing frames by comparing found files vs expected range 
  - Identifies corrupt EXR files by checking magic number (first 4 bytes) and file size thresholds 
  - Generates detailed Validation Report window showing pass/fail status, missing frame list, and corrupt file details with byte sizes 

<img width="1682" height="1127" alt="image" src="https://github.com/user-attachments/assets/6023de3f-2049-46d2-b080-9dffac78fa74" />

