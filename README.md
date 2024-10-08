
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

    Open the terminal and check if `rclone` is already installed:
    ```bash
    which rclone
    ```
    Run the following commands to install or upgrade `rclone`:
    ```bash
    sudo snap install rclone
    ```
    This will download and install the latest version of `rclone` with snap.

    If you do not want to use snap or if it is not available on your system you can also install (an older version) of `rclone` with:
    ```bash
    sudo apt install rclone
    ```
    This will download and install the latest version of `rclone` available with apt and you need to adjust the path to rclone in the script.
   
3. **Configure `rclone` to Connect to Your OneDrive Account:**

   Run the following command to set up `rclone`:
   ```bash
   rclone config
   ```
   Follow the prompts to set up a new remote named `onedrive`. Ensure that `rclone` is configured for non-interactive use with the correct permissions and scopes.

   Test the connection to onedrive:
   ```bash
   rclone lsd onedrive:
   ```
4. **Download and Place the Script in the Project Directory:**

   Clone the repository and navigate to the project directory:
   ```bash
   cd /home/user/python/
   git clone https://github.com/drhdev/rclone_backup_to_onedrive.git
   cd rclone_backup_to_onedrive
   ```

5. **Set Up a Python Virtual Environment (`venv`) in the Project Directory:**

   Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
6. **Test the script manually:**

   Change the script according to your setup by editing:
   ```bash
   nano rclone_backup_to_onedrive.py
   ```
   Then run it with:
    ```bash
   python rclone_backup_to_onedrive.py -v
   ```

5. **Other Tests for rclone configuration:**

   Run any of the folloeing rclone commands to check if the configuration works:
   ```bash
   rclone lsd onedrive:
   rclone ls onedrive:
   rclone lsf onedrive: --recursive
   ```

   You can also try to copy a testfile to OneDrive via rclone:
   ```bash
   echo "Test File" > test.txt
   rclone copy test.txt onedrive:/test/
   ```

   Then use the following command to check if it worked:
   ```bash
   rclone lsf onedrive:/test/
   ```

   If the script cannot says that the rclone configuration for onedrive cannot be found, check the path of the rclone.config file and adjust accordingly (e.g. when using snap in Ubuntu 24.04 instead of manual configuration above):
   ```bash
   rclone config file
   ``` 

6. **Set Up a Cron Job to Run This Script Automatically:**

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

## **Restoration **

This guide provides step-by-step instructions to restore backups created by the `rclone_backup_to_onedrive.py` script. These steps will help you retrieve backups from OneDrive, extract the data, and ensure the correct permissions and ownership are restored on your server.

### **1. Prerequisites**

Before starting the restoration process, ensure the following:

- You have `rclone` installed and configured with access to OneDrive.
- You have permissions to write to the directories you intend to restore.
- You have `tar` installed on your system for extracting the backups.

### **2. Restoring Backup Files from OneDrive**

#### **Step 1: List Available Backups**

Use `rclone` to list the available backups in your OneDrive. Replace `<backup_directory>` with the path you used in the script (`daily`, `weekly`, or `monthly`):

```bash
rclone lsf onedrive:/backups/<hostname>/<backup_directory>/
```

Example:

```bash
rclone lsf onedrive:/backups/server1/daily/
```

#### **Step 2: Download the Desired Backup**

Choose the specific backup file you want to restore and download it to your local machine or server. Replace `<backup_name>` with the actual backup file name you listed in the previous step:

```bash
rclone copy onedrive:/backups/<hostname>/<backup_directory>/<backup_name> /local/restore/path
```

Example:

```bash
rclone copy onedrive:/backups/server1/daily/20230903093000-server1.tar.gz /home/user/restore/
```

### **3. Extract the Backup**

After downloading the backup file, extract its contents using the `tar` command. Ensure you specify the correct path where the backup should be restored:

```bash
tar -xzf /local/restore/path/<backup_name> -C /target/restore/path
```

Example:

```bash
tar -xzf /home/user/restore/20230903093000-server1.tar.gz -C /
```

**Note**: Using `-C /` will extract the contents directly to the root filesystem, replicating the original paths. Ensure the target path does not overwrite important data unless intended.

### **4. Restoring File Permissions and Ownership**

`tar` preserves file permissions, ownership, and symlinks by default, but if you want to ensure this explicitly, you can use:

```bash
tar --preserve-permissions --preserve-order -xzf /local/restore/path/<backup_name> -C /target/restore/path
```

### **5. Verify Restored Files**

It's crucial to verify the restored files to ensure the restoration was successful and data integrity is maintained:

- **Check File Integrity**: Manually check key files or use file checksums if available.
- **Check Permissions and Ownership**: Use `ls -l` to verify that files have the correct permissions.

Example:

```bash
ls -l /target/restore/path/etc
```

### **6. Additional Considerations**

- **Extended Attributes**: If your environment uses ACLs, SELinux contexts, or other extended attributes, ensure these attributes are correctly restored. 
- **Testing**: Always test the restoration process in a safe environment before performing on a production server.
- **Automated Restore**: Consider scripting these steps if you frequently need to restore backups or plan to include restoration as part of a disaster recovery plan.

### **7. Troubleshooting Common Issues**

- **Permission Denied Errors**: Ensure you are running the commands with the necessary privileges, e.g., as `root` or using `sudo`.
- **`rclone` Configuration Issues**: Re-run `rclone config reconnect onedrive:` if access to OneDrive is problematic.
- **File Not Found**: Double-check paths and file names, ensuring the correct case sensitivity.

## Requirements

- Python 3
- `rclone` configured for OneDrive
- Linux environment (tested on Ubuntu 22.04)

## Usage

Once configured, run the script manually using Python or set it up to run automatically using cron jobs as described above. The script will handle creating backups, managing retention, and transferring files to OneDrive as configured.

## License

This project is licensed under the GPL v3 License.
