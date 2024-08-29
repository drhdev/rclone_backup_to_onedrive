
# rclone_backup_to_onedrive

## Description

`rclone_backup_to_onedrive.py` is a Python script that automates the process of backing up specific directories to Microsoft OneDrive using `rclone`. It creates compressed tarball backups of specified directories and uploads them to OneDrive with daily, weekly, and monthly retention policies. The script is configurable and can be easily run as a cron job for scheduled backups.

## Features

- Backup specified directories to OneDrive with date-based versioning.
- Supports daily, weekly, and monthly retention policies for backups.
- Manages local backups and removes older backups based on user-defined settings.
- Handles permissions errors and skips paths that cannot be accessed.
- Configurable for any user environment and paths.
- Ensures that only the latest backup is kept on OneDrive for each day.

## Installation Instructions

1. **Install or Upgrade `rclone` to the Latest Stable Version:**

    Open the terminal and run the following commands to install or upgrade `rclone`:
    ```bash
    curl https://rclone.org/install.sh | sudo bash
    ```
   This will download and install the latest version of `rclone`.

2. **Configure `rclone` to Connect to Your OneDrive Account:**

    Run the following command to set up `rclone`:
    ```bash
    rclone config
    ```
    Follow the prompts to set up a new remote named `onedrive`. Ensure that `rclone` is configured for non-interactive use with the correct permissions and scopes.

3. **Set Up a Python Virtual Environment (`venv`) in the Project Directory:**

   Navigate to the project directory where you want to store the script (default: `/home/user/python/rclone_backup_to_onedrive`):
   ```bash
   mkdir -p /home/user/python/rclone_backup_to_onedrive
   cd /home/user/python/rclone_backup_to_onedrive
   ```
   Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Download and Place the Script in the Project Directory:**

   Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/drhdev/rclone_backup_to_onedrive.git
   cd rclone_backup_to_onedrive
   ```

5. **Set Up a Cron Job to Run This Script Automatically:**

   For example, to run the backup daily at 2 am, add the following line to your crontab:
   ```bash
   0 2 * * * /home/user/python/rclone_backup_to_onedrive/venv/bin/python /home/user/python/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py
   ```

## Configuration

The script can be configured to match your specific backup needs:

1. **Backup Sources Configuration:**
   Modify the `BACKUP_PATHS` dictionary in the script to specify which directories should be backed up. Set paths to `True` or `False` depending on whether they should be included.

2. **Local and Remote Backup Directories:**
   Configure the local and OneDrive backup directories by modifying the `LOCAL_BACKUP_DIR`, `DAILY_BACKUP_DIR`, `WEEKLY_BACKUP_DIR`, and `MONTHLY_BACKUP_DIR` variables.

3. **Retention Periods:**
   Adjust the retention periods for daily, weekly, and monthly backups by modifying the `DAILY_RETENTION`, `WEEKLY_RETENTION`, and `MONTHLY_RETENTION` variables.

4. **Maximum Local Backups:**
   Set `MAX_LOCAL_BACKUPS` to specify the maximum number of local backups to keep. Set to `0` to not keep any local backups after transfer.

## Requirements

- Python 3
- `rclone` configured for OneDrive
- Linux environment (tested on Ubuntu 22.04)

## Usage

Once configured, run the script manually using Python or set it up to run automatically using cron jobs as described above. The script will handle creating backups, managing retention, and transferring files to OneDrive as configured.

## License

This project is licensed under the GPL v3 License.
