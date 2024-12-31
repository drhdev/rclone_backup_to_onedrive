#!/usr/bin/env python3
# rclone_backup_to_onedrive.py
# Version: 3.2
# Author: drhdev
# License: GPL v3
# Description: Enhanced backup script with YAML-based configurations, improved retention policies, per-configuration local backup retention, and cron compatibility.

import os
import subprocess
import datetime
import tarfile
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import shutil
import argparse
import yaml

# CONFIGURATION VARIABLES

# Define base directory as the directory where the script is run
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# Configurations directory
CONFIGS_DIR = os.path.join(BASE_DIR, 'configs')

# Set up logging to use the base directory
log_filename = os.path.join(BASE_DIR, 'rclone_backup_to_onedrive.log')
logger = logging.getLogger('rclone_backup_to_onedrive.py')
logger.setLevel(logging.DEBUG)

# Updated so the log file is rotated/overwritten at 1 MB total size, keeps only 1 backup
handler = RotatingFileHandler(log_filename, maxBytes=1 * 1024 * 1024, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_filename), exist_ok=True)

# Initialize verbose flag and console handler
verbose = False  # Will be set based on argparse
console_handler = None

# Function to parse command-line arguments
def parse_arguments():
    global verbose, console_handler
    parser = argparse.ArgumentParser(description='Backup script using rclone with YAML configurations.')
    parser.add_argument('configs', nargs='*', help='YAML configuration files to execute (located in configs/ directory).')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    args = parser.parse_args()
    
    if args.verbose:
        verbose = True
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return args.configs

# Function to find the rclone path
def find_rclone_path():
    """Find the path of the rclone executable, preferring apt installation."""
    apt_path = "/usr/bin/rclone"
    
    # Check for apt installation
    if os.path.exists(apt_path):
        logger.info(f"Using rclone from apt installation at {apt_path}")
        return apt_path
    else:
        logger.error("Rclone is not installed. Please install and configure rclone first.")
        print("\nRclone needs to be installed and configured. Use the following commands to install via apt:\n")
        print("sudo apt update")
        print("sudo apt install rclone")
        print("rclone config")
        exit(1)

# Set the path for rclone dynamically
RCLONE_PATH = find_rclone_path()

# Function to load and validate a YAML configuration
def load_yaml_config(yaml_path):
    """Load and validate a YAML configuration file."""
    try:
        with open(yaml_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Validate required fields
        required_fields = ['backup_paths', 'onedrive_remote', 'retention']
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field '{field}' in {os.path.basename(yaml_path)}.")
                return None
        
        # Validate onedrive_remote fields
        onedrive_required = ['daily', 'weekly', 'monthly']
        for subfield in onedrive_required:
            if subfield not in config['onedrive_remote']:
                logger.error(f"Missing required field 'onedrive_remote.{subfield}' in {os.path.basename(yaml_path)}.")
                return None
        
        # Validate retention fields
        retention_required = ['daily_retention', 'weekly_retention', 'monthly_retention']
        for subfield in retention_required:
            if subfield not in config['retention']:
                logger.error(f"Missing required field 'retention.{subfield}' in {os.path.basename(yaml_path)}.")
                return None
        
        # Set default for max_local_backups if not present
        if 'max_local_backups' not in config:
            config['max_local_backups'] = 0
        
        return config
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {os.path.basename(yaml_path)}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load {os.path.basename(yaml_path)}: {e}")
        return None

# Function to run a system command
def run_command(command):
    """Run a system command and log the output."""
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        if result.stdout.strip():
            logger.info(result.stdout.strip())
        if result.stderr.strip():
            logger.error(result.stderr.strip())
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{' '.join(command)}' failed with error: {e.stderr.strip()}")
        return False

# Function to check rclone configuration
def check_rclone_config():
    """Check if rclone is configured correctly for OneDrive."""
    try:
        if not run_command([RCLONE_PATH, "version"]):
            logger.error("Rclone version check failed.")
            return False
        result = subprocess.run([RCLONE_PATH, "listremotes"], text=True, capture_output=True, check=True)
        if "onedrive:" not in result.stdout:
            logger.error("Rclone is not configured for 'onedrive'. Please run 'rclone config' to set it up.")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check rclone configuration: {e.stderr.strip()}")
        return False

# Function to check OneDrive access
def check_onedrive_access():
    """Check if the OneDrive remote is accessible, and reconnect if necessary."""
    try:
        if not run_command([RCLONE_PATH, "lsf", "onedrive:/"]):
            logger.warning("Unable to access OneDrive. Attempting to refresh the token.")
            if not run_command([RCLONE_PATH, "config", "reconnect", "onedrive:", "--auto-confirm"]):
                logger.error("Failed to reconnect to OneDrive. Ensure that rclone is set up correctly for non-interactive use.")
                return False
        time.sleep(2)
        return True
    except Exception as e:
        logger.error(f"Failed to check OneDrive access: {e}")
        return False

# Function to create a tarball
def create_tarball(backup_filename, backup_paths, exclude_dir):
    """Create a tarball of the specified directories, excluding the local backups directory."""
    try:
        os.makedirs(exclude_dir, exist_ok=True)  # Ensure exclude_dir exists
        with tarfile.open(backup_filename, "w:gz") as tar:
            for path, should_backup in backup_paths.items():
                if should_backup:
                    if os.path.exists(path):
                        try:
                            tar.add(path, arcname=os.path.relpath(path, '/'))
                            logger.info(f"Added {path} to the backup.")
                        except PermissionError as pe:
                            logger.error(f"Permission denied while trying to add {path} to the backup: {pe}")
                    else:
                        logger.warning(f"Path {path} does not exist and will be skipped.")
        logger.info(f"Backup {backup_filename} created successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup {backup_filename}: {e}")
        return False

# Function to manage local backups
def manage_local_backups(backup_dir, max_backups):
    """Ensure no more than the maximum number of backups are kept locally."""
    try:
        os.makedirs(backup_dir, exist_ok=True)  # Ensure backup_dir exists
        if max_backups == 0:
            local_backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".tar.gz")])
            for backup in local_backups:
                os.remove(os.path.join(backup_dir, backup))
                logger.info(f"Deleted local backup as max_local_backups is 0: {backup}")
        elif max_backups > 0:
            local_backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".tar.gz")])
            if len(local_backups) > max_backups:
                logger.info("Too many local backups, removing oldest ones...")
                for backup in local_backups[:-max_backups]:
                    os.remove(os.path.join(backup_dir, backup))
                    logger.info(f"Deleted old local backup: {backup}")
    except Exception as e:
        logger.error(f"Failed to manage local backups: {e}")

# Function to perform rclone operations
def rclone_operation(operation, source, destination=None, retry=3, delay=5):
    """Perform an rclone operation and handle errors."""
    try:
        command = [RCLONE_PATH, operation]
        if operation in ["delete", "deletefile"]:
            if source:
                command.extend(source.split())
            else:
                logger.error(f"Operation '{operation}' requires a source path.")
                return False
        elif destination:
            command.extend([source, destination])
        else:
            # For operations like mkdir where destination is the path
            command.append(source)
        
        logger.info(f"Executing rclone command: {' '.join(command)}")
        
        for attempt in range(retry):
            if run_command(command):
                time.sleep(2)
                return True
            logger.warning(f"Attempt {attempt + 1} for {operation} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        logger.error(f"All {retry} attempts for {operation} failed.")
        return False
    except Exception as e:
        logger.error(f"Failed to {operation} from {source} to {destination}: {e}")
        return False

# Function to manage backups on OneDrive based on retention counts
def manage_backups_by_count(remote_path, backup_type, retention_count):
    """Ensure no more than the specified number of backups are kept on OneDrive."""
    try:
        result = subprocess.run(
            [RCLONE_PATH, "lsf", remote_path, "--files-only"],
            text=True,
            capture_output=True,
            check=True
        )
        backups = sorted(result.stdout.splitlines())
        if len(backups) > retention_count:
            backups_to_delete = backups[:-retention_count]
            for backup in backups_to_delete:
                run_command([RCLONE_PATH, "deletefile", f"{remote_path}/{backup}"])
                logger.info(f"Deleted old {backup_type} backup: {backup}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to manage {backup_type} backups on OneDrive: {e.stderr.strip()}")

# Function to generate backup filenames
def get_backup_filename(period, config_name):
    """Generate backup filename based on the backup period and config name."""
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    if period == 'daily':
        return f"daily-{config_name}-{timestamp}.tar.gz"
    elif period == 'weekly':
        week_number = now.strftime('%U')  # Week number of the year (Sunday as the first day)
        return f"weekly-{config_name}-W{week_number}-{timestamp}.tar.gz"
    elif period == 'monthly':
        return f"monthly-{config_name}-{now.strftime('%Y%m')}-{timestamp}.tar.gz"
    else:
        return f"{timestamp}-{config_name}.tar.gz"

# Function to write FINAL_STATUS messages
def write_final_status(backup_name, script_name, status):
    """Write the final status of the backup process to the log."""
    hostname = os.uname().nodename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_status_message = (
        f"FINAL_STATUS | {status.upper()} | Script: {script_name} | Host: {hostname} | "
        f"Backup: {backup_name} | Timestamp: {timestamp}"
    )
    logger.info(final_status_message)

# Function to process a single backup configuration
def process_backup_config(config, config_filename):
    """Process a single backup configuration."""
    backup_name = config.get('backup_name', config_filename)
    backup_paths = config['backup_paths']
    onedrive_remote = config['onedrive_remote']
    retention = config['retention']
    max_local_backups = config.get('max_local_backups', 0)  # Defaults to 0
    
    # Define remote backup directories
    DAILY_BACKUP_DIR = onedrive_remote['daily']
    WEEKLY_BACKUP_DIR = onedrive_remote['weekly']
    MONTHLY_BACKUP_DIR = onedrive_remote['monthly']
    
    # Create remote backup directories if they do not exist
    rclone_operation("mkdir", DAILY_BACKUP_DIR)
    rclone_operation("mkdir", WEEKLY_BACKUP_DIR)
    rclone_operation("mkdir", MONTHLY_BACKUP_DIR)
    
    # Manage local backups based on max_local_backups
    LOCAL_BACKUP_DIR = os.path.join(BASE_DIR, 'rclone_backup_to_onedrive_backups')
    manage_local_backups(LOCAL_BACKUP_DIR, max_backups=max_local_backups)
    
    # Create Daily Backup
    backup_filename = get_backup_filename('daily', backup_name)
    backup_filepath = os.path.join(LOCAL_BACKUP_DIR, backup_filename)
    status = "failure"  # Default status
    
    logger.info(f"Starting backup job '{backup_name}' with configuration '{config_filename}'")
    
    try:
        if create_tarball(backup_filepath, backup_paths, exclude_dir=LOCAL_BACKUP_DIR):
            backup_success = rclone_operation("copy", backup_filepath, DAILY_BACKUP_DIR)
            if backup_success:
                # If daily upload succeeded, manage daily retention
                manage_backups_by_count(DAILY_BACKUP_DIR, 'daily', retention.get('daily_retention', 7))
                status = "success"
            else:
                logger.error(f"Backup transfer to OneDrive for '{backup_name}' failed. Keeping local backup.")
    except Exception as e:
        logger.error(f"Failed to complete the backup process for '{backup_name}': {e}")
    
    # If daily was successfully uploaded, attempt weekly/monthly rotation
    if status == "success":
        current_weekday = datetime.datetime.now().weekday()
        current_day = datetime.datetime.now().day
        
        # Weekly Rotation (if Sunday == weekday 6)
        if current_weekday == 6:
            weekly_backup_filename = get_backup_filename('weekly', backup_name)
            weekly_backup_filepath = os.path.join(LOCAL_BACKUP_DIR, weekly_backup_filename)
            try:
                # Copy the local daily tarball to create a weekly tarball
                shutil.copy2(backup_filepath, weekly_backup_filepath)
                weekly_success = rclone_operation("copy", weekly_backup_filepath, WEEKLY_BACKUP_DIR)
                if weekly_success:
                    if os.path.exists(weekly_backup_filepath):
                        os.remove(weekly_backup_filepath)
                        logger.info(f"Weekly backup transferred successfully, deleting local backup: {weekly_backup_filepath}")
                    manage_backups_by_count(WEEKLY_BACKUP_DIR, 'weekly', retention.get('weekly_retention', 4))
            except Exception as e:
                logger.error(f"Failed to create weekly backup for '{backup_name}': {e}")
        
        # Monthly Rotation (if day==1)
        if current_day == 1:
            monthly_backup_filename = get_backup_filename('monthly', backup_name)
            monthly_backup_filepath = os.path.join(LOCAL_BACKUP_DIR, monthly_backup_filename)
            try:
                # Find the latest weekly backup
                result = subprocess.run(
                    [RCLONE_PATH, "lsf", WEEKLY_BACKUP_DIR, "--files-only"],
                    text=True,
                    capture_output=True,
                    check=True
                )
                weekly_backups = sorted(result.stdout.splitlines())
                if weekly_backups:
                    latest_weekly_backup = weekly_backups[-1]
                    latest_weekly_backup_path = f"{WEEKLY_BACKUP_DIR}/{latest_weekly_backup}"
                    # Copy the latest weekly backup from OneDrive to local for monthly rotation
                    # Or you could do direct remote->remote copy if desired, but we'll stick to the local approach
                    logger.info(f"Downloading latest weekly backup for monthly rotation: {latest_weekly_backup}")
                    rclone_operation("copy", latest_weekly_backup_path, LOCAL_BACKUP_DIR)
                    
                    # Now that it's local, rename/copy it to monthly name
                    downloaded_weekly_local = os.path.join(LOCAL_BACKUP_DIR, latest_weekly_backup)
                    if os.path.exists(downloaded_weekly_local):
                        shutil.copy2(downloaded_weekly_local, monthly_backup_filepath)
                        
                        monthly_success = rclone_operation("copy", monthly_backup_filepath, MONTHLY_BACKUP_DIR)
                        if monthly_success:
                            if os.path.exists(monthly_backup_filepath):
                                os.remove(monthly_backup_filepath)
                                logger.info(f"Monthly backup transferred successfully, deleting local backup: {monthly_backup_filepath}")
                            manage_backups_by_count(MONTHLY_BACKUP_DIR, 'monthly', retention.get('monthly_retention', 12))
                        # Clean up the downloaded weekly file
                        if os.path.exists(downloaded_weekly_local):
                            os.remove(downloaded_weekly_local)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to list weekly backups for monthly rotation in '{backup_name}': {e.stderr.strip()}")
            except Exception as e:
                logger.error(f"Failed to create monthly backup for '{backup_name}': {e}")
    
    # Now that weekly/monthly rotation logic is done, remove the local daily tarball if daily was a success
    if status == "success":
        if os.path.exists(backup_filepath):
            os.remove(backup_filepath)
            logger.info(f"Daily backup transferred successfully; removing local backup: {backup_filepath}")
    
    write_final_status(backup_filename, os.path.basename(__file__), status)
    logger.info(f"Backup job '{backup_name}' completed with status: {status.upper()}")

# Main execution function
def main():
    # Parse command-line arguments
    specified_configs = parse_arguments()
    
    # Validate and prepare the list of YAML files to process
    if specified_configs:
        # User specified YAML files; ensure they exist in configs directory
        yaml_files = []
        for cfg in specified_configs:
            cfg_path = os.path.join(CONFIGS_DIR, cfg)
            if os.path.isfile(cfg_path) and cfg.lower().endswith(('.yaml', '.yml')):
                yaml_files.append(cfg)
            else:
                logger.error(f"Specified configuration file '{cfg}' does not exist in 'configs/' or is not a YAML file.")
        if not yaml_files:
            logger.error("No valid YAML configuration files specified. Exiting.")
            exit(1)
    else:
        # No YAML files specified; process all YAML files in configs directory in alphabetical order
        try:
            yaml_files = sorted([f for f in os.listdir(CONFIGS_DIR) if f.lower().endswith(('.yaml', '.yml'))])
            if not yaml_files:
                logger.error("No YAML configuration files found in 'configs/' directory. Exiting.")
                exit(1)
        except FileNotFoundError:
            logger.error(f"'configs/' directory not found at expected location: {CONFIGS_DIR}")
            exit(1)
    
    # Process each YAML configuration file
    for idx, yaml_file in enumerate(yaml_files):
        yaml_path = os.path.join(CONFIGS_DIR, yaml_file)
        config = load_yaml_config(yaml_path)
        if config is None:
            logger.error(f"Skipping invalid configuration file: {yaml_file}")
            write_final_status(yaml_file, os.path.basename(__file__), "FAILURE")
            continue
        
        config_base_name = os.path.splitext(yaml_file)[0]
        process_backup_config(config, config_base_name)
        
        # If not the last configuration, wait for 5 seconds before next
        if idx < len(yaml_files) - 1:
            logger.info("Waiting for 5 seconds before processing the next configuration...")
            time.sleep(5)

if __name__ == "__main__":
    # Initial checks
    if not os.path.isdir(CONFIGS_DIR):
        logger.error(f"'configs/' directory does not exist at expected location: {CONFIGS_DIR}")
        print(f"Error: 'configs/' directory does not exist at expected location: {CONFIGS_DIR}")
        exit(1)
    
    # Check rclone configuration before proceeding
    if not check_rclone_config():
        logger.error("Rclone configuration check failed. Exiting.")
        exit(1)
    
    # Check OneDrive access before proceeding
    if not check_onedrive_access():
        logger.error("OneDrive access check failed. Exiting.")
        exit(1)
    
    # Execute main function
    main()
