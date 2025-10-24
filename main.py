import os
import shutil
import subprocess
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

# ---------------- Path Resolver (for PyInstaller) ----------------
def resource_path(relative_path):
    """تعيد المسار الصحيح سواء أثناء التطوير أو التشغيل من الملف التنفيذي."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # عند التشغيل من ملف exe
    else:
        base_path = os.path.abspath(".")  # عند التشغيل من الكود الأصلي
    return os.path.join(base_path, relative_path)

# ---------------- Logging Setup ----------------
LOG_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer.log")
logger = logging.getLogger("installer")
logger.setLevel(logging.DEBUG)
fh = RotatingFileHandler(LOG_FILENAME, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(ch)

# ---------------- Admin Elevation ----------------
def is_windows_admin():
    if os.name != "nt": 
        return True
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.debug(f"Admin check failed: {e}")
        return False

def relaunch_as_admin():
    if os.name != "nt": 
        return False
    try:
        import ctypes
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return True
    except Exception as e:
        logger.error(f"Could not elevate privileges: {e}")
        return False

if __name__ == "__main__" and os.name == "nt" and not is_windows_admin():
    logger.info("Requesting administrator privileges...")
    if relaunch_as_admin():
        sys.exit(0)
    else:
        logger.error("Administrator privileges are required.")
        sys.exit(1)

# ---------------- Config ----------------
BASE_DIR = r"C:\SewmartBackend"
NSSM_DIR = os.path.join(BASE_DIR, "nssm")

# استخدم resource_path لضمان الوصول الصحيح سواء من exe أو من الكود
LOCAL_NSSM_PATH = resource_path(os.path.join("nssm", "nssm.exe"))

SERVICES = [
    {
        "name": "SewmartPrinterAPI",
        "src": resource_path("printer_api"),
        "dst": os.path.join(BASE_DIR, "printer_api"),
        "exe": os.path.join(BASE_DIR, "printer_api", "app.exe"),
    },
    {
        "name": "SewmartBarcodePrinter",
        "src": resource_path("barcode_printer"),
        "dst": os.path.join(BASE_DIR, "barcode_printer"),
        "exe": os.path.join(BASE_DIR, "barcode_printer", "app.exe"),
    }
]

# ---------------- Helpers ----------------
def run_cmd(cmd, description=None):
    try:
        if description:
            logger.info(f"{description}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            logger.info(result.stdout.strip())
        if result.stderr.strip():
            logger.warning(result.stderr.strip())
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed ({description}): {e.stderr or e}")
        return False

def service_exists(name):
    try:
        result = subprocess.run(["sc", "query", name], capture_output=True, text=True)
        return "1060" not in result.stdout
    except Exception as e:
        logger.error(f"Service check failed: {e}")
        return False

def safe_copy(src, dst):
    try:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        logger.info(f"Copied {src} → {dst}")
        return True
    except PermissionError:
        logger.warning(f"Access denied while copying {src}. Retrying...")
        time.sleep(3)
        try:
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
            logger.info(f"Copied {src} → {dst}")
            return True
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        return False

# ---------------- Install ----------------
def install_services():
    logger.info("=== Installing Sewmart Backend Services ===")

    if not os.path.isfile(LOCAL_NSSM_PATH):
        logger.error("nssm.exe not found in local 'nssm' folder.")
        return

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(NSSM_DIR, exist_ok=True)
    shutil.copy2(LOCAL_NSSM_PATH, NSSM_DIR)
    nssm_path = os.path.join(NSSM_DIR, "nssm.exe")

    for s in SERVICES:
        logger.info(f"--- Installing service: {s['name']} ---")

        if not os.path.isdir(s["src"]):
            logger.error(f"Source folder not found: {s['src']}")
            continue

        # Copy folders
        if not safe_copy(s["src"], s["dst"]):
            continue

        # Remove old service if exists
        if service_exists(s["name"]):
            logger.info(f"Service {s['name']} already exists. Removing it first.")
            remove_service(s["name"], s["dst"], nssm_path)
            time.sleep(2)

        # Install via NSSM
        run_cmd([nssm_path, "install", s["name"], s["exe"]], f"Installing {s['name']}")
        run_cmd([nssm_path, "set", s["name"], "AppDirectory", s["dst"]], f"Setting AppDirectory for {s['name']}")
        run_cmd([nssm_path, "set", s["name"], "Start", "SERVICE_AUTO_START"], f"Setting auto-start for {s['name']}")
        run_cmd(["net", "start", s["name"]], f"Starting {s['name']}")

    logger.info("✅ Both Sewmart services installed and started successfully!")

# ---------------- Remove ----------------
def remove_service(name, path, nssm_path):
    logger.info(f"Removing {name}...")
    if service_exists(name):
        run_cmd(["net", "stop", name], f"Stopping {name}")
        run_cmd([nssm_path, "remove", name, "confirm"], f"Removing {name}")
    if os.path.isdir(path):
        try:
            shutil.rmtree(path)
            logger.info(f"Removed folder {path}")
        except Exception as e:
            logger.warning(f"Could not delete folder {path}: {e}")

def remove_all():
    logger.info("=== Removing all Sewmart Services ===")
    nssm_path = os.path.join(NSSM_DIR, "nssm.exe")

    for s in SERVICES:
        remove_service(s["name"], s["dst"], nssm_path)

    time.sleep(2)
    if os.path.isdir(BASE_DIR):
        try:
            shutil.rmtree(BASE_DIR)
            logger.info(f"Removed {BASE_DIR}")
        except Exception as e:
            logger.error(f"Failed to remove {BASE_DIR}: {e}")

    logger.info("🗑️ All services and files removed successfully!")

# ---------------- Main ----------------
def main():
    logger.info("=== Sewmart Backend Installer ===")
    print("1) Install both services")
    print("2) Remove both services completely")
    choice = input("Select (1 or 2): ").strip()

    if choice == "1":
        install_services()
    elif choice == "2":
        remove_all()
    else:
        logger.error("Invalid choice.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
