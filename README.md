# Sewmart Backend Services Installer

This project provides a Python script (`main.py`) to install and manage two Windows services, `SewmartPrinterAPI` and `SewmartBarcodePrinter`, as part of the [SewMartPro](https://github.com/MohammedBoure/SewMartPro) project. The script uses NSSM (Non-Sucking Service Manager) to configure and manage these services. Below are the requirements, setup instructions, and steps to convert the Python script into an executable (EXE) file.

## Project Overview
This installer is designed to:
- Deploy two services: `SewmartPrinterAPI` and `SewmartBarcodePrinter`.
- Copy necessary files to `C:\SewmartBackend`.
- Configure the services to run automatically using NSSM.
- Provide options to install or remove the services and their associated files.

The script is tailored for Windows and includes logic to ensure compatibility when packaged as an EXE using PyInstaller.

## Prerequisites

### Required Files and Folders
- **printer_api**: A folder containing the `app.exe` for the `SewmartPrinterAPI` service.
- **barcode_printer**: A folder containing the `app.exe` for the `SewmartBarcodePrinter` service.
- **nssm**: A folder containing the NSSM executable (`nssm.exe`) for managing Windows services.
- **main.py**: The provided Python script that handles service installation and removal.

Ensure these files and folders are placed in the same directory as the script before running it.

### Required Software
- **Python 3.6+**: Required to run the script if not using the EXE.
- **PyInstaller**: To convert the Python script to an EXE.
- **Windows Operating System**: The script is designed for Windows, as it uses Windows-specific commands and NSSM.
- **NSSM (Non-Sucking Service Manager)**: The `nssm.exe` binary must be included in the `nssm` folder. Download it from [NSSM's official site](https://nssm.cc/download) if not already present.

### Directory Structure
The directory structure should look like this:
```
project_folder/
├── main.py
├── nssm/
│   └── nssm.exe
├── printer_api/
│   └── app.exe
├── barcode_printer/
│   └── app.exe
```

## Setup Instructions
1. **Prepare the Environment**:
   - Ensure all required files and folders (`printer_api`, `barcode_printer`, `nssm`, and `main.py`) are in the same directory.
   - Install Python 3.6+ if you plan to run the script directly or convert it to an EXE.

2. **Run the Script**:
   - Open a command prompt with administrator privileges.
   - Navigate to the project folder: `cd path\to\project_folder`.
   - Run the script: `python main.py`.
   - Follow the prompts to either:
     - **Install** both services (option 1): Copies files to `C:\SewmartBackend`, sets up the services using NSSM, and starts them with auto-start enabled.
     - **Remove** both services (option 2): Stops and removes the services, then deletes the associated files.

3. **Logs**:
   - The script generates logs in `installer.log` in the same directory, with a maximum size of 5MB and up to 3 backup files.

## Converting the Python Script to EXE

To make the script portable and avoid requiring Python on the target machine, you can convert `main.py` to an EXE using PyInstaller. The script includes a `resource_path` function to handle file paths correctly when packaged as an EXE.

### Steps to Convert to EXE
1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Run PyInstaller**:
   - Navigate to the directory containing `main.py`.
   - Run the following command to create a single EXE file:
     ```bash
     pyinstaller --onefile --name SewmartInstaller main.py
     ```
   - **Options Explained**:
     - `--onefile`: Packages everything into a single executable.
     - `--name SewmartInstaller`: Names the output EXE as `SewmartInstaller.exe`.
   - The resulting EXE will be in the `dist` folder.

3. **Distribute the EXE**:
   - Copy `SewmartInstaller.exe` to the same directory as the `printer_api`, `barcode_printer`, and `nssm` folders.
   - Run `SewmartInstaller.exe` with administrator privileges to install or remove the services.

### Notes on EXE Conversion
- The `resource_path` function ensures that file paths (e.g., for `nssm.exe`, `printer_api`, and `barcode_printer`) are resolved correctly when running from the EXE.
- Ensure PyInstaller is compatible with your Python version.
- The EXE will include all dependencies (e.g., `os`, `shutil`, `subprocess`, `time`, `logging`, `sys`, and `ctypes`).
- If additional Python modules are added to the script, include them in the PyInstaller command using `--hidden-import module_name` if needed.
- Test the EXE on a clean Windows machine to ensure it works without requiring Python or additional dependencies.

## Usage
- **Install the Services**:
  - Select option 1 when prompted.
  - The script will copy the `printer_api` and `barcode_printer` folders to `C:\SewmartBackend`, install both services using NSSM, configure them to auto-start, and start them.
- **Remove the Services**:
  - Select option 2 when prompted.
  - The script will stop and remove both services, then delete the `C:\SewmartBackend` directory.

## Troubleshooting
- **Service Fails to Start**:
  - Check `installer.log` for detailed error messages.
  - Ensure `app.exe` in both `printer_api` and `barcode_printer` folders is functional and compatible with the target system.
  - Verify NSSM is correctly installed and accessible at `C:\SewmartBackend\nssm\nssm.exe`.
- **Permission Issues**:
  - Run the script or EXE as an administrator to avoid access-denied errors.
  - The script includes a retry mechanism for permission issues during file copying.
- **Missing Files**:
  - Ensure `printer_api`, `barcode_printer`, and `nssm` folders are correctly placed in the project directory.
  - Verify that `app.exe` exists in both `printer_api` and `barcode_printer` folders.
- **EXE Path Issues**:
  - If the EXE cannot find `nssm.exe` or other folders, ensure they are in the same directory as `SewmartInstaller.exe`.

## Relation to SewMartPro
This installer is designed to support the [SewMartPro](https://github.com/MohammedBoure/SewMartPro) project, which likely provides the backend services (`SewmartPrinterAPI` and `SewmartBarcodePrinter`). Ensure that the `app.exe` files in the `printer_api` and `barcode_printer` folders are built from the SewMartPro project or are compatible with its requirements.

## License
This project is provided as-is, with no warranty. Ensure you have the necessary permissions to use and distribute the `app.exe` files and `nssm.exe`. Refer to the [SewMartPro repository](https://github.com/MohammedBoure/SewMartPro) for specific licensing details related to the services.