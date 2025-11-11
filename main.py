import os
import shutil
import subprocess
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

# ---------------- Path Resolver (for PyInstaller) ----------------
def resource_path(relative_path):
    """
    Always resolve relative paths relative to the executable location,
    not the temporary _MEIPASS folder.
    """
    try:
        # When running as exe
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            # When running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"Path resolution error: {e}")
        return relative_path

# ---------------- Logging Setup ----------------
LOG_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer.log")
logger = logging.getLogger("installer")
logger.setLevel(logging.DEBUG)
# Set up a rotating file handler
fh = RotatingFileHandler(LOG_FILENAME, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)
# Set up a stream handler to output to console
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(ch)

# ---------------- Admin Elevation ----------------
def is_windows_admin():
    """Check if the script is running with administrator privileges."""
    if os.name != "nt": 
        return True # Not Windows, assume privileges are fine
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.debug(f"Admin check failed: {e}")
        return False

def relaunch_as_admin():
    """Relaunch the script with elevated privileges."""
    if os.name != "nt": 
        return False
    try:
        import ctypes
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        # Relaunch using "runas" verb to trigger UAC
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return True
    except Exception as e:
        logger.error(f"Could not elevate privileges: {e}")
        return False

# Relaunch as admin if not already
if __name__ == "__main__" and os.name == "nt" and not is_windows_admin():
    logger.info("Requesting administrator privileges...")
    if relaunch_as_admin():
        sys.exit(0) # Exit the non-admin process
    else:
        logger.error("Administrator privileges are required to run this installer.")
        input("Press Enter to exit...") # Keep console open
        sys.exit(1)

# ---------------- Config ----------------
BASE_DIR = r"C:\SewmartBackend"
NSSM_DIR = os.path.join(BASE_DIR, "nssm")

# Use resource_path to ensure correct access from .exe or source code
LOCAL_NSSM_PATH = resource_path(os.path.join("nssm", "nssm.exe"))

SERVICES = [
    {
        "name": "SewmartPrinterAPI",
        "src": resource_path("printer_api"), # Source folder in bundle
        "dst": os.path.join(BASE_DIR, "printer_api"), # Destination on C:
        "exe": os.path.join(BASE_DIR, "printer_api", "SewmartPrinterAPI.exe"), # Path to service exe
    },
    {
        "name": "SewmartBarcodePrinter",
        "src": resource_path("barcode_printer"),
        "dst": os.path.join(BASE_DIR, "barcode_printer"),
        "exe": os.path.join(BASE_DIR, "barcode_printer", "SewmartBarcodePrinter.exe"),
    }
]

# ---------------- Helpers ----------------
def run_cmd(cmd, description=None):
    """Runs a shell command and logs its output."""
    try:
        if description:
            logger.info(f"{description}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        if result.stdout.strip():
            logger.info(result.stdout.strip())
        if result.stderr.strip():
            logger.warning(result.stderr.strip())
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed ({description or ' '.join(cmd)}): {e.stderr or e}")
        return False

def service_exists(name):
    """Checks if a Windows service already exists."""
    try:
        # sc query returns error code 1060 if service doesn't exist
        result = subprocess.run(["sc", "query", name], capture_output=True, text=True, encoding='utf-8')
        return "1060" not in result.stdout
    except Exception as e:
        logger.error(f"Service check failed for '{name}': {e}")
        return False

def safe_copy(src, dst):
    """Safely copies a directory tree, removing the destination if it exists."""
    try:
        if os.path.exists(dst):
            logger.info(f"Removing existing directory: {dst}")
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        logger.info(f"Copied {src} → {dst}")
        return True
    except PermissionError:
        logger.warning(f"Access denied while copying {src}. Retrying in 3s...")
        time.sleep(3)
        try:
            shutil.rmtree(dst, ignore_errors=True) # Try again to remove
            shutil.copytree(src, dst)
            logger.info(f"Copied {src} → {dst}")
            return True
        except Exception as e:
            logger.error(f"Copy failed on retry: {e}")
            return False
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        return False

# ---------------- Install ----------------
def install_services():
    """Installs and starts all services defined in the SERVICES list."""
    logger.info("=== Installing Sewmart Backend Services ===")

    if not os.path.isfile(LOCAL_NSSM_PATH):
        logger.error(f"nssm.exe not found at expected path: {LOCAL_NSSM_PATH}")
        logger.error("Installation cannot continue without nssm.exe.")
        return

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(NSSM_DIR, exist_ok=True)
    shutil.copy2(LOCAL_NSSM_PATH, NSSM_DIR)
    nssm_path = os.path.join(NSSM_DIR, "nssm.exe")

    for s in SERVICES:
        logger.info(f"--- Installing service: {s['name']} ---")

        if not os.path.isdir(s["src"]):
            logger.error(f"Source folder not found: {s['src']}")
            logger.error(f"Skipping installation for {s['name']}.")
            continue

        # 1. Copy service files
        if not safe_copy(s["src"], s["dst"]):
            logger.error(f"Failed to copy files for {s['name']}. Skipping.")
            continue

        # 2. Remove old service if it exists (to ensure a clean install)
        if service_exists(s["name"]):
            logger.info(f"Service {s['name']} already exists. Removing it first for a clean installation.")
            # Pass nssm_path to the removal function
            remove_service(s["name"], s["dst"], nssm_path, keep_files=True)
            time.sleep(2) # Give Windows time to process removal

        # 3. Install via NSSM
        run_cmd([nssm_path, "install", s["name"], s["exe"]], f"Installing {s['name']}")
        run_cmd([nssm_path, "set", s["name"], "AppDirectory", s["dst"]], f"Setting AppDirectory for {s['name']}")
        run_cmd([nssm_path, "set", s["name"], "Start", "SERVICE_AUTO_START"], f"Setting auto-start for {s['name']}")
        
        # 4. Start the service
        run_cmd(["net", "start", s["name"]], f"Starting {s['name']}")

    logger.info("✅ Both Sewmart services installed and started successfully!")

# ---------------- Remove ----------------
def remove_service(name, path, nssm_path, keep_files=False):
    """Stops and removes a single service and its files."""
    logger.info(f"Removing {name}...")
    if service_exists(name):
        run_cmd(["net", "stop", name], f"Stopping {name}")
        run_cmd([nssm_path, "remove", name, "confirm"], f"Removing {name}")
    
    if not keep_files and os.path.isdir(path):
        try:
            shutil.rmtree(path)
            logger.info(f"Removed folder {path}")
        except Exception as e:
            logger.warning(f"Could not delete folder {path} (maybe in use?): {e}")
    elif keep_files:
        logger.info(f"Keeping files in {path} as requested.")

def remove_all():
    """Removes all services and the base directory."""
    logger.info("=== Removing all Sewmart Services ===")
    nssm_path = os.path.join(NSSM_DIR, "nssm.exe")
    
    if not os.path.isfile(nssm_path):
        logger.warning(f"nssm.exe not found at {nssm_path}. Will try to remove services but may fail.")
        # Create a dummy path if it doesn't exist so the loop doesn't fail
        nssm_path = "nssm.exe" 

    for s in SERVICES:
        remove_service(s["name"], s["dst"], nssm_path)

    time.sleep(2) # Give Windows time
    if os.path.isdir(BASE_DIR):
        try:
            shutil.rmtree(BASE_DIR)
            logger.info(f"Removed base directory {BASE_DIR}")
        except Exception as e:
            logger.error(f"Failed to remove base directory {BASE_DIR}. You may need to remove it manually. Error: {e}")

    logger.info("🗑️ All services and files removed successfully!")

# ---------------- Main ----------------
def main():
    """Main function to display the menu."""
    logger.info("=== Sewmart Backend Installer ===")
    print("1) Install both services")
    print("2) Remove both services completely")
    choice = input("Select (1 or 2): ").strip()

    if choice == "1":
        install_services()
    elif choice == "2":
        remove_all()
    else:
        logger.error("Invalid choice. Exiting.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()