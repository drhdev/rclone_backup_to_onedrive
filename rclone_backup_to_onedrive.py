#!/usr/bin/env python3
"""
Script Name: rclone_backup_to_onedrive.py
Version: 1.0
License: GPL v3

Description:
    This script automates the backup process to Microsoft OneDrive using `rclone`. It creates compressed tarballs
    of specified directories and uploads them to OneDrive with daily, weekly, and monthly retention policies.

Installation Instructions:
    1. Install or upgrade `rclone` to the latest stable version:
       - Open the terminal and run the following commands:
         ```
         curl https://rclone.org/install.sh | sudo bash
         ```
       - This will download and install the latest version of `rclone`.

    2. Configure `rclone` to connect to your OneDrive account:
       - Run the following command to set up `rclone`:
         ```
         rclone config
         ```
       - Follow the prompts to set up a new remote named `onedrive`.
       - Ensure that `rclone` is configured for non-interactive use with the correct permissions and scopes.

    3. Set up a Python virtual environment (venv) in the project directory:
       - Navigate to the project directory (default: `/home/user/python/rclone_backup_to_onedrive`):
         ```
         mkdir -p /home/user/python/rclone_backup_to_onedrive
         cd /home/user/python/rclone_backup_to_onedrive
         ```
       - Create and activate a virtual environment:
         ```
         python3 -m venv venv
         source venv/bin/activate
         ```

    4. Place this script in the project directory:
       - `/home/user/python/rclone_backup_to_onedrive`

    5. Set up a cron job to run this script automatically. For example, to run the backup daily at 2 am, add the following line to your crontab:
       ```
       0 2 * * * /home/user/python/rclone_backup_to_onedrive/venv/bin/python /home/user/python/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py
       ```

Requirements:
    - Python 3
    - rclone configured for OneDrive
"""

import os
import subprocess
import datetime
import tarfile
import logging
from logging.handlers import RotatingFileHandler
import time

############################
# CONFIGURATION VARIABLES  #
############################

# User-configurable settings
USER_HOME = os.path.expanduser("~")  # Dynamically get the current user's home directory
USER_PATH = os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin")  # User's PATH
RCLONE_CONFIG_PATH = os.path.join(USER_HOME, ".config/rclone/rclone.conf")  # Path to rclone config file

# Set environment variables for the script
os.environ["HOME"] = USER_HOME
os.environ["PATH"] = USER_PATH

# Set up logging
log_filename = 'logfile_rclone_backup_to_onedrive.log'
logger = logging.getLogger('rclone_backup_to_onedrive')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log environment variables for debugging
logger.info(f"Environment variables: {os.environ}")

# Backup Sources Configuration
BACKUP_PATHS = {
    "/etc": False,                  # Changed to False to avoid permission errors
    "/var/www": True,               # /var/www contains website files
    "/var/lib": False,              # Changed to False to avoid permission errors
    "/var/log": False,              # /var/log contains log files (usually not needed)
    "/var/spool": False,            # /var/spool contains print jobs, mail queues, etc.
    "/home": True,                  # /home contains user directories
    "/usr/local/bin": True,         # /usr/local/bin contains custom scripts
    "/var/backups/mysql": False,    # Changed to False if it doesn't exist
    "/var/python": False,           # Changed to False if it doesn't exist
    "/var/data": False,             # Changed to False if it doesn't exist
    "/var/shared": False            # Changed to False if it doesn't exist
}

# Backup Destination Configuration
CHOSENNAME = os.uname()[1]  # Using hostname as identifier
DATE = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))  # Directory where the script is executed
LOCAL_BACKUP_DIR = os.path.join(SCRIPT_DIR, "rclone_backup_to_onedrive_backups")
DAILY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/daily"
WEEKLY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/weekly"
MONTHLY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/monthly"

# Retention Periods Configuration (in days)
DAILY_RETENTION = 1    # Keep daily backups for 1 day
WEEKLY_RETENTION = 30  # Keep weekly backups for 30 days
MONTHLY_RETENTION = 180  # Keep monthly backups for 6 months (approximately 180 days)

# Backup File Name Configuration
BACKUP_FILENAME = f"{DATE}-{CHOSENNAME}.tar.gz"  # Example: 20230601123000-servername.tar.gz

# Local Backup Configuration
MAX_LOCAL_BACKUPS = 0  # Default to 0 to keep no local backups after successful transfer

############################
# SCRIPT LOGIC             #
############################

# Create local backup directory if it does not exist
os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)

def check_rclone_config():
    """Check if rclone is configured correctly for OneDrive."""
    try:
        # Log rclone version for debugging
        run_command("rclone version")
        
        result = subprocess.run(f"rclone --config {RCLONE_CONFIG_PATH} listremotes", shell=True, text=True, capture_output=True, check=True)
        if "onedrive:" not in result.stdout:
            logger.error("Rclone is not configured for 'onedrive'. Please run 'rclone config' to set it up.")
            exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check rclone configuration: {e.stderr}")
        exit(1)

# Function to execute shell commands and log output
def run_command(command):
    """Run a system command and log the output."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        logger.info(result.stdout)
        logger.error(result.stderr) if result.stderr else None
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{command}' failed with error: {e.stderr}")
        return False

# Function to create a tarball of specified paths
def create_tarball(backup_filename, backup_paths, exclude_dir):
    """Create a tarball of the specified directories, excluding the local backups directory."""
    try:
        with tarfile.open(backup_filename, "w:gz") as tar:
            for path, should_backup in backup_paths.items():
                if should_backup:
                    if os.path.exists(path) and path != exclude_dir:
                        try:
                            tar.add(path)
                            logger.info(f"Added {path} to the backup.")
                        except PermissionError as pe:
                            logger.error(f"Permission denied while trying to add {path} to the backup: {pe}")
                    elif path == exclude_dir:
                        logger.info(f"Excluding {exclude_dir} from the backup.")
                    else:
                        logger.warning(f"Path {path} does not exist and will be skipped.")
        logger.info(f"Backup {backup_filename} created successfully.")
    except Exception as e:
        logger.error(f"Failed to create backup {backup_filename}: {e}")
        raise e

# Function to manage local backups
def manage_local_backups(backup_dir, max_backups):
    """Ensure no more than the maximum number of backups are kept locally."""
    try:
        local_backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".tar.gz")])
        if max_backups == 0:
            for backup in local_backups:
                os.remove(os.path.join(backup_dir, backup))
                logger.info(f"Deleted local backup as MAX_LOCAL_BACKUPS is 0: {backup}")
        elif len(local_backups) > max_backups:
            logger.info("Too many backups, removing oldest ones...")
            for backup in local_backups[:-max_backups]:
                os.remove(os.path.join(backup_dir, backup))
                logger.info(f"Deleted old backup: {backup}")
    except Exception as e:
        logger.error(f"Failed to manage local backups: {e}")
        raise e

# Function to perform rclone operations
def rclone_operation(operation, source, destination, retry=3, delay=5):
    """Perform an rclone operation and handle errors."""
    try:
        command = f"rclone --config {RCLONE_CONFIG_PATH} {operation} {source} {destination}"
        logger.info(f"Executing rclone command: {command}")
        for attempt in range(retry):
            if run_command(command):
                time.sleep(2)  # Add a small delay to ensure the operation completes
                return True
            logger.warning(f"Attempt {attempt + 1} for {operation} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        return False
    except Exception as e:
        logger.error(f"Failed to {operation} from {source} to {destination}: {e}")
        return False

# Function to check if the OneDrive remote is accessible
def check_onedrive_access():
    """Check if the OneDrive remote is accessible, and reconnect if necessary."""
    try:
        # Try listing files in OneDrive root to check access
        if not run_command(f"rclone --config {RCLONE_CONFIG_PATH} lsf onedrive:/"):
            logger.warning("Unable to access OneDrive. Attempting to refresh the token.")
            # Reconnect to refresh the token non-interactively (optional if token is permanent)
            if not run_command(f"rclone --config {RCLONE_CONFIG_PATH} config reconnect onedrive: --auto-confirm"):
                logger.error("Failed to reconnect to OneDrive. Ensure that rclone is set up correctly for non-interactive use.")
                exit(1)
        time.sleep(2)  # Add a delay to ensure OneDrive access is stable
    except Exception as e:
        logger.error(f"Failed to check OneDrive access: {e}")
        raise e

# Function to delete all but the latest backup of the same day on OneDrive
def keep_latest_daily_backup(remote_path):
    """Keep only the latest backup on OneDrive for each day."""
    try:
        result = subprocess.run(f"rclone --config {RCLONE_CONFIG_PATH} lsf {remote_path}", shell=True, text=True, capture_output=True, check=True)
        backups = sorted(result.stdout.splitlines())
        latest_backup = None

        for backup in backups:
            backup_date = backup.split('-')[0]
            if latest_backup is None or backup_date != latest_backup.split('-')[0]:
                latest_backup = backup
            else:
                run_command(f"rclone --config {RCLONE_CONFIG_PATH} deletefile {remote_path}/{backup}")
                logger.info(f"Deleted older backup of the same day: {backup}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clean up backups on OneDrive: {e.stderr}")

# Check if rclone is configured properly
check_rclone_config()

# Check if OneDrive remote is accessible; reconnect if needed
check_onedrive_access()

# Create OneDrive directories if they don't exist
rclone_operation("mkdir", "", DAILY_BACKUP_DIR)
rclone_operation("mkdir", "", WEEKLY_BACKUP_DIR)
rclone_operation("mkdir", "", MONTHLY_BACKUP_DIR)

# Manage local backups before creating a new one
manage_local_backups(LOCAL_BACKUP_DIR, MAX_LOCAL_BACKUPS)

# Create tarball of the backup sources, excluding the local backups directory
backup_filepath = os.path.join(LOCAL_BACKUP_DIR, BACKUP_FILENAME)
create_tarball(backup_filepath, BACKUP_PATHS, exclude_dir=LOCAL_BACKUP_DIR)

# Sync local backups to OneDrive with date-based versioning
if rclone_operation("copy", backup_filepath, DAILY_BACKUP_DIR):
    # Delete local backup after successful transfer
    if os.path.exists(backup_filepath):
        try:
            os.remove(backup_filepath)
            logger.info(f"Backup transferred successfully, deleting local backup: {backup_filepath}")
            # If MAX_LOCAL_BACKUPS is 0, remove all remaining local backups
            if MAX_LOCAL_BACKUPS == 0:
                manage_local_backups(LOCAL_BACKUP_DIR, MAX_LOCAL_BACKUPS)
        except Exception as e:
            logger.error(f"Failed to delete local backup: {e}")
    # Keep only the latest backup for the same day on OneDrive
    keep_latest_daily_backup(DAILY_BACKUP_DIR)
else:
    logger.error("Backup transfer to OneDrive failed. Keeping local backup.")

# Move daily backups to weekly and monthly if needed
if datetime.datetime.now().weekday() == 6:  # Sunday is the 6th day
    rclone_operation("move", DAILY_BACKUP_DIR, WEEKLY_BACKUP_DIR)

if datetime.datetime.now().day == 1:  # First day of the month
    rclone_operation("move", WEEKLY_BACKUP_DIR, MONTHLY_BACKUP_DIR)

# Cleanup remote backups older than retention periods
rclone_operation("delete", f"--min-age {DAILY_RETENTION}d", DAILY_BACKUP_DIR)
rclone_operation("delete", f"--min-age {WEEKLY_RETENTION}d", WEEKLY_BACKUP_DIR)
rclone_operation("delete", f"--min-age {MONTHLY_RETENTION}d", MONTHLY_BACKUP_DIR)

logger.info("Backup script completed.")
