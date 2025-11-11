# Sewmart Backend Services Installer

This project provides a **Python-based installer script** (`main.py`) to deploy and manage two critical Windows services for the **[SewMartPro](https://github.com/MohammedBoureafre/SewMartPro)** system:

- `SewmartPrinterAPI` – Receipt printing service  
- `SewmartBarcodePrinter` – Label printing service

The installer uses **NSSM (Non-Sucking Service Manager)** to register, start, and manage these services reliably on Windows. It supports both **interactive installation/removal** and **standalone EXE deployment**.

---

## Project Overview

| Feature | Description |
|-------|-----------|
| **Two Services** | `SewmartPrinterAPI` and `SewmartBarcodePrinter` |
| **Auto-Start** | Services start with Windows |
| **NSSM Integration** | Robust service management |
| **Admin Elevation** | Auto-requests UAC if needed |
| **Logging** | Full audit trail in `installer.log` |
| **EXE Support** | Distributable without Python |

---

## Source Code of Printer Services

The **source code** for the two backend services is hosted publicly:

| Service | Repository |
|-------|------------|
| **Receipt Printer API** | [https://github.com/MohammedBoure/ReceiptPrint](https://github.com/MohammedBoure/ReceiptPrint) |
| **Label Printer API** | [https://github.com/MohammedBoure/LabelPrint](https://github.com/MohammedBoure/LabelPrint) |

> These repositories contain the `.NET` or Python projects that generate the `app.exe` binaries used by this installer.

---

## Prerequisites

### Required Files & Folders

Place the following in the **same directory** as `main.py`:

```
project_folder/
├── main.py
├── nssm/
│   └── nssm.exe
├── printer_api/
│   └── app.exe         ← Built from ReceiptPrint
├── barcode_printer/
│   └── app.exe         ← Built from LabelPrint
```

> **Important**:  
> - `app.exe` must be **pre-built** from the respective GitHub repositories.  
> - `nssm.exe` must match your system architecture (x64 recommended).

---

### Software Requirements

| Tool | Purpose |
|------|-------|
| **Python 3.6+** | Run script directly |
| **PyInstaller** | Build `.exe` |
| **Windows 10/11** | Target OS |
| **Admin Rights** | Required for service installation |

---

## Setup Instructions

### 1. Prepare Files
- Clone or download:
  - [ReceiptPrint](https://github.com/MohammedBoure/ReceiptPrint) → Build → Place `app.exe` in `printer_api/`
  - [LabelPrint](https://github.com/MohammedBoure/LabelPrint) → Build → Place `app.exe` in `barcode_printer/`
- Download [NSSM](https://nssm.cc/download) → Extract `nssm.exe` → Place in `nssm/`

### 2. Run Installer (Python)
```bash
python main.py
```

> **Run as Administrator**

### 3. Choose Option
```
1) Install Services
2) Remove Services
```

---

## Convert to Standalone EXE

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build EXE
```bash
pyinstaller --onefile --name SewmartInstaller main.py
```

### Output
```
dist/SewmartInstaller.exe
```

### Step 3: Distribute
1. Copy `SewmartInstaller.exe`
2. Include:
   - `printer_api/` (with `app.exe`)
   - `barcode_printer/` (with `app.exe`)
   - `nssm/` (with `nssm.exe`)
3. Run `SewmartInstaller.exe` **as Administrator**

> No Python required on target machine!

---

## What Happens on Install?

| Action | Path |
|------|------|
| Copy folders | `C:\SewmartBackend\` |
| Register services | `SewmartPrinterAPI`, `SewmartBarcodePrinter` |
| Set working dir | `C:\SewmartBackend\printer_api`, etc. |
| Auto-start | Enabled |
| Start services | Immediately |

---

## Logs

- File: `installer.log` (same directory)
- Max size: 5 MB
- Backups: 3 rotated files

---

## Troubleshooting

| Issue | Solution |
|------|---------|
| **Service fails to start** | Check `installer.log`, verify `app.exe` works standalone |
| **Access denied** | Run as **Administrator** |
| **nssm.exe not found** | Ensure `nssm/` folder is present |
| **EXE can't find folders** | Keep `printer_api/`, `barcode_printer/`, `nssm/` in same dir as EXE |

---

## Relation to SewMartPro

This installer is a **companion deployment tool** for:

[SewMartPro – Main Application](https://github.com/MohammedBoure/SewMartPro)

It ensures the **printing backend services** are always running and ready for the frontend to call.

---

## License & Attribution

- **NSSM**: Licensed under [CC BY 4.0](https://nssm.cc/)
- **Service Code**: See respective repos:
  - [ReceiptPrint](https://github.com/MohammedBoure/ReceiptPrint)
  - [LabelPrint](https://github.com/MohammedBoure/LabelPrint)
- **Installer Script**: Provided as-is. Use responsibly.

---

**Deploy Sewmart backend services in seconds.**