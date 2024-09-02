#!/usr/bin/env python3
# rclone_backup_to_onedrive.py
# Version: 1.4
# Author: drhdev
# License: GPL v3
# Description: This script automates the backup process to Microsoft OneDrive using `rclone`. It creates compressed tarballs of specified directories and uploads them to OneDrive with daily, weekly, and monthly retention policies.

import os
import subprocess
import datetime
import tarfile
import logging
from logging.handlers import RotatingFileHandler
import sys
import time

# CONFIGURATION VARIABLES

# Define base directory as the directory where the script is run
BASE_DIR = os.path.dirname(os.path.realpath(__file__))  # The base directory is where the script is executed

# Set up logging to use the base directory
log_filename = os.path.join(BASE_DIR, 'rclone_backup_to_onedrive.log')
logger = logging.getLogger('rclone_backup_to_onedrive.py')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(log_filename, maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Check for verbose flag
verbose = '-v' in sys.argv
if verbose:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Backup Sources Configuration
# Add the local backup directory to the excluded paths to avoid recursive backups
LOCAL_BACKUP_DIR_NAME = "rclone_backup_to_onedrive_backups"
LOCAL_BACKUP_DIR = os.path.join(BASE_DIR, LOCAL_BACKUP_DIR_NAME)

BACKUP_PATHS = {
    "/etc": False,
    "/var/www": True,
    "/home": True,
    "/usr/local/bin": True,
    LOCAL_BACKUP_DIR: False,  # Exclude the local backup directory from the backup process
}

# Backup Destination Configuration
CHOSENNAME = os.uname()[1]  # Using hostname as identifier
DATE = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Set backup directories using the base directory
DAILY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/daily"
WEEKLY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/weekly"
MONTHLY_BACKUP_DIR = f"onedrive:/backups/{CHOSENNAME}/monthly"

# Retention Periods Configuration (in days)
DAILY_RETENTION = 1
WEEKLY_RETENTION = 30
MONTHLY_RETENTION = 180

# Backup File Name Configuration
BACKUP_FILENAME = f"{DATE}-{CHOSENNAME}.tar.gz"

# Local Backup Configuration
MAX_LOCAL_BACKUPS = 0

# SCRIPT LOGIC

# Create local backup directory if it does not exist
os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)

def check_rclone_config():
    """Check if rclone is configured correctly for OneDrive."""
    try:
        run_command("rclone version")
        result = subprocess.run("rclone listremotes", shell=True, text=True, capture_output=True, check=True)
        if "onedrive:" not in result.stdout:
            logger.error("Rclone is not configured for 'onedrive'. Please run 'rclone config' to set it up.")
            exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check rclone configuration: {e.stderr}")
        exit(1)

def run_command(command):
    """Run a system command and log the output."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{command}' failed with error: {e.stderr}")
        return False

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

def rclone_operation(operation, source, destination, retry=3, delay=5):
    """Perform an rclone operation and handle errors."""
    try:
        command = f"rclone {operation} {source} {destination}"
        logger.info(f"Executing rclone command: {command}")
        for attempt in range(retry):
            if run_command(command):
                time.sleep(2)
                return True
            logger.warning(f"Attempt {attempt + 1} for {operation} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        return False
    except Exception as e:
        logger.error(f"Failed to {operation} from {source} to {destination}: {e}")
        return False

def check_onedrive_access():
    """Check if the OneDrive remote is accessible, and reconnect if necessary."""
    try:
        if not run_command("rclone lsf onedrive:/"):
            logger.warning("Unable to access OneDrive. Attempting to refresh the token.")
            if not run_command("rclone config reconnect onedrive: --auto-confirm"):
                logger.error("Failed to reconnect to OneDrive. Ensure that rclone is set up correctly for non-interactive use.")
                exit(1)
        time.sleep(2)
    except Exception as e:
        logger.error(f"Failed to check OneDrive access: {e}")
        raise e

def keep_latest_daily_backup(remote_path):
    """Keep only the latest backup on OneDrive for each day."""
    try:
        result = subprocess.run(f"rclone lsf {remote_path}", shell=True, text=True, capture_output=True, check=True)
        backups = sorted(result.stdout.splitlines())
        latest_backup = None

        for backup in backups:
            backup_date = backup.split('-')[0]
            if latest_backup is None or backup_date != latest_backup.split('-')[0]:
                latest_backup = backup
            else:
                run_command(f"rclone deletefile {remote_path}/{backup}")
                logger.info(f"Deleted older backup of the same day: {backup}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clean up backups on OneDrive: {e.stderr}")

def write_final_status(backup_name, script_name, status):
    """Write the final status of the backup process to the log."""
    hostname = os.uname().nodename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_status_message = (
        f"FINAL_STATUS | {status.upper()} | Script: {script_name} | Host: {hostname} | "
        f"Backup: {backup_name} | Timestamp: {timestamp}"
    )
    logger.info(final_status_message)

# Start of the main script logic

check_rclone_config()
check_onedrive_access()

rclone_operation("mkdir", "", DAILY_BACKUP_DIR)
rclone_operation("mkdir", "", WEEKLY_BACKUP_DIR)
rclone_operation("mkdir", "", MONTHLY_BACKUP_DIR)

manage_local_backups(LOCAL_BACKUP_DIR, MAX_LOCAL_BACKUPS)

backup_filepath = os.path.join(LOCAL_BACKUP_DIR, BACKUP_FILENAME)
try:
    create_tarball(backup_filepath, BACKUP_PATHS, exclude_dir=LOCAL_BACKUP_DIR)
    backup_success = rclone_operation("copy", backup_filepath, DAILY_BACKUP_DIR)
    if backup_success:
        if os.path.exists(backup_filepath):
            os.remove(backup_filepath)
            logger.info(f"Backup transferred successfully, deleting local backup: {backup_filepath}")
            if MAX_LOCAL_BACKUPS == 0:
                manage_local_backups(LOCAL_BACKUP_DIR, MAX_LOCAL_BACKUPS)
        keep_latest_daily_backup(DAILY_BACKUP_DIR)
        status = "success"
    else:
        logger.error("Backup transfer to OneDrive failed. Keeping local backup.")
        status = "failure"
except Exception as e:
    logger.error(f"Failed to complete the backup process: {e}")
    status = "failure"

if datetime.datetime.now().weekday() == 6:
    rclone_operation("move", DAILY_BACKUP_DIR, WEEKLY_BACKUP_DIR)

if datetime.datetime.now().day == 1:
    rclone_operation("move", WEEKLY_BACKUP_DIR, MONTHLY_BACKUP_DIR)

rclone_operation("delete", f"--min-age {DAILY_RETENTION}d", DAILY_BACKUP_DIR)
rclone_operation("delete", f"--min-age {WEEKLY_RETENTION}d", WEEKLY_BACKUP_DIR)
rclone_operation("delete", f"--min-age {MONTHLY_RETENTION}d", MONTHLY_BACKUP_DIR)

write_final_status(BACKUP_FILENAME, os.path.basename(__file__), status)
logger.info("Backup script completed.")
