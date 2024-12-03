# rclone_backup_to_onedrive

![Backup to OneDrive](https://img.shields.io/github/license/drhdev/rclone_backup_to_onedrive)
![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![GitHub stars](https://img.shields.io/github/stars/drhdev/rclone_backup_to_onedrive?style=social)

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Requirements](#requirements)
- [Installation Instructions](#installation-instructions)
  - [1. Install or Upgrade `rclone` via APT](#1-install-or-upgrade-rclone-via-apt)
  - [2. Configure `rclone` for OneDrive on a Headless Server](#2-configure-rclone-for-onedrive-on-a-headless-server)
  - [3. Clone the Repository](#3-clone-the-repository)
  - [4. Set Up a Python Virtual Environment](#4-set-up-a-python-virtual-environment)
  - [5. Install Python Dependencies](#5-install-python-dependencies)
  - [6. Test the Script Manually](#6-test-the-script-manually)
  - [7. Set Up the Cron Job for Automated Backups](#7-set-up-the-cron-job-for-automated-backups)
- [Configuration](#configuration)
  - [YAML Configuration Files](#yaml-configuration-files)
  - [Example YAML Configurations](#example-yaml-configurations)
- [Usage](#usage)
  - [Manual Execution](#manual-execution)
  - [Command-Line Arguments](#command-line-arguments)
- [Restoration Guide](#restoration-guide)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Description

`rclone_backup_to_onedrive.py` is a Python script that automates the backup process of specific directories to Microsoft OneDrive using `rclone`. It supports multiple backup configurations defined in YAML files, allowing for flexible and scalable backup solutions. The script creates compressed tarball backups, manages retention policies, and can be easily integrated with cron jobs for regular automated backups.

---

## Features

- **YAML-Based Configuration:**
  - Define multiple backup jobs with distinct settings in individual YAML files.
  - Pre-configured `configs` directory with demo YAML files (`config1.yaml` and `config2.yaml`).

- **Flexible Backup Management:**
  - Specify directories to include or exclude in backups.
  - Support for daily, weekly, and monthly backups with customizable retention counts.
  - Per-configuration control over the number of local backups to retain.

- **Automated Backup Rotation:**
  - Automatically rotates backups based on the defined schedule.
  - Manages retention policies by deleting older backups beyond the specified count.

- **Comprehensive Logging:**
  - Detailed logs for each step of every backup job.
  - `FINAL_STATUS` messages indicating `SUCCESS` or `FAILURE` for easy monitoring.

- **Cron Compatibility:**
  - Designed to work seamlessly with cron jobs for automated scheduling.
  - Avoids issues related to Snap installations when running via cron.

- **Error Handling:**
  - Validates configurations and handles errors gracefully without halting execution.
  - Logs errors for each backup job individually.

---

## Requirements

- **Operating System:** Linux (Tested on Ubuntu 22.04 and 24.04)
- **Python:** Python 3.x
- **Rclone:** Installed via APT (version 1.50 or higher)
- **Python Packages:** Listed in `requirements.txt`

---

## Installation Instructions

### 1. Install or Upgrade `rclone` via APT

**Why Use APT Instead of Snap?**

Installing `rclone` via Snap can cause compatibility issues with cron jobs due to Snap's confinement and cgroup management. Using APT ensures that `rclone` operates with the necessary permissions and paths required by cron, avoiding errors like `/system.slice/cron.service is not a snap cgroup`.

#### Step-by-Step Guide:

1. **Remove Snap Version of `rclone` (if installed):**

   If you have previously installed `rclone` using Snap, remove it to prevent conflicts.

   ```bash
   sudo snap remove rclone
   ```

2. **Update APT Package Index:**

   ```bash
   sudo apt update
   ```

3. **Install `rclone` via APT:**

   ```bash
   sudo apt install rclone
   ```

   - This installs `rclone` from the official APT repositories.
   - Even in newer Ubuntu versions (e.g., Ubuntu 24.04) where Snap is the default, APT can still be used for package management.

4. **Verify Installation:**

   ```bash
   which rclone
   ```

   - **Expected Output:** `/usr/bin/rclone`

   ```bash
   rclone version
   ```

   - Ensure `rclone` is installed and reports its version without errors.

### 2. Configure `rclone` for OneDrive on a Headless Server

Configuring `rclone` for OneDrive typically involves a browser for authorization. On a headless server (without a graphical interface), you'll need to perform a manual authorization process.

#### Step-by-Step Guide:

1. **Start `rclone` Configuration:**

   ```bash
   rclone config
   ```

2. **Create a New Remote:**

   - Type `n` to create a new remote.
   - **Name it:** `onedrive` (or any preferred name).

3. **Select the Storage Type:**

   - Choose the number corresponding to `Microsoft OneDrive`. As of recent versions, this is typically option `24`, but confirm in the prompt.

4. **Client ID and Secret:**

   - Press Enter to use the default client ID and secret.

5. **Edit Advanced Config:**

   - Type `n` for "Edit advanced config?"

6. **Use Auto Config:**

   - Type `n` for "Use auto config?"

7. **Generate Authorization URL:**

   - Since the server is headless, `rclone` will provide a URL that you need to open on a machine with a web browser.

   - **Example Output:**

     ```
     Please go to the following URL and authorize rclone:
     https://login.microsoftonline.com/... (truncated)
     ```

8. **Authorize `rclone`:**

   - Open the provided URL in a web browser on a different machine.
   - Sign in to your Microsoft account and grant `rclone` access to OneDrive.
   - After authorization, you'll receive a verification code.

9. **Enter the Verification Code:**

   - Return to your headless server terminal.
   - Paste the verification code when prompted.

10. **Finalize Configuration:**

    - Type `y` to confirm the configuration.
    - Type `q` to quit the configuration menu.

11. **Verify OneDrive Access:**

    ```bash
    rclone lsf onedrive:/
    ```

    - This should list the contents of your OneDrive root directory.

### 3. Clone the Repository

#### Step-by-Step Guide:

1. **Navigate to Your Desired Directory:**

   Choose a directory where you want to place the backup script.

   ```bash
   cd /home/user/
   ```

2. **Clone the Repository:**

   ```bash
   git clone https://github.com/drhdev/rclone_backup_to_onedrive.git
   ```

3. **Navigate to the Project Directory:**

   ```bash
   cd rclone_backup_to_onedrive
   ```

### 4. Set Up a Python Virtual Environment

Using a virtual environment is recommended to manage dependencies without affecting system-wide packages.

#### Step-by-Step Guide:

1. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   ```

   - This creates a virtual environment named `venv` in the project directory.

2. **Activate the Virtual Environment:**

   ```bash
   source venv/bin/activate
   ```

   - Your terminal prompt should now indicate that the virtual environment is active.

### 5. Install Python Dependencies

The script relies on certain Python packages listed in `requirements.txt`.

#### Step-by-Step Guide:

1. **Ensure You Are in the Virtual Environment:**

   - If not already activated, activate it:

     ```bash
     source venv/bin/activate
     ```

2. **Install Dependencies Using `pip`:**

   ```bash
   pip install -r requirements.txt
   ```

   - This installs all necessary packages in the virtual environment.

   **Note:** The repository includes a `requirements.txt` file for easy installation of dependencies.

### 6. Test the Script Manually

Before scheduling automated backups, it's essential to verify that the script operates correctly.

#### Step-by-Step Guide:

1. **Navigate to the Project Directory:**

   ```bash
   cd /home/user/rclone_backup_to_onedrive
   ```

2. **Run the Script with Verbose Output:**

   ```bash
   python rclone_backup_to_onedrive.py -v
   ```

   - **Notes:**
     - Running the script from within the project directory ensures correct path references.
     - The `-v` flag enables verbose output, displaying detailed logs in the terminal.

3. **Monitor the Output:**

   - The script will process the configurations and output logs to the console and the log file `rclone_backup_to_onedrive.log`.

4. **Verify Backups on OneDrive:**

   - Log in to your OneDrive account and navigate to the specified backup directories to ensure backups have been uploaded.

### 7. Set Up the Cron Job for Automated Backups

Automate the backup process by scheduling the script to run at desired intervals using cron.

#### Step-by-Step Guide:

1. **Determine the Absolute Path of the Script:**

   ```bash
   pwd
   # Output example: /home/user/rclone_backup_to_onedrive
   ```

   - **Script Path:** `/home/user/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py`

2. **Ensure the Script is Executable:**

   ```bash
   chmod +x rclone_backup_to_onedrive.py
   ```

3. **Edit the Root’s Crontab:**

   Running the cron job as `root` ensures access to all directories that require elevated permissions.

   ```bash
   sudo crontab -e
   ```

4. **Add the Cron Job Entry:**

   ```cron
   0 4 * * * /home/user/rclone_backup_to_onedrive/venv/bin/python /home/user/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py >> /var/log/rclone_backup_to_onedrive_cron.log 2>&1
   ```

   - **Explanation:**
     - `0 4 * * *`: Runs daily at 4:00 AM.
     - `/home/user/rclone_backup_to_onedrive/venv/bin/python`: Path to the Python interpreter within the virtual environment.
     - `/home/user/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py`: Path to the backup script.
     - `>> /var/log/rclone_backup_to_onedrive_cron.log 2>&1`: Redirects both `stdout` and `stderr` to a log file for monitoring.

5. **Save and Exit:**

   - The cron service will recognize and apply the new job automatically.

6. **Verify Cron Job Execution:**

   - After the scheduled time, check the cron log to ensure the script ran successfully.

     ```bash
     cat /var/log/rclone_backup_to_onedrive_cron.log
     ```

   - Look for `FINAL_STATUS` messages indicating `SUCCESS` or `FAILURE` for each backup job.

---

## Configuration

### YAML Configuration Files

Backup configurations are defined in YAML files located within the `configs` directory. Each YAML file represents a separate backup job with its own settings.

### Example YAML Configurations

The repository includes two demo YAML files:

1. **`configs/config1.yaml`**

   ```yaml
   backup_name: "config1"

   backup_paths:
     /etc: false
     /var/www: true
     /home: true
     /usr/local/bin: true
     /path/to/exclude: false

   onedrive_remote:
     daily: "onedrive:/backups/config1/daily"
     weekly: "onedrive:/backups/config1/weekly"
     monthly: "onedrive:/backups/config1/monthly"

   retention:
     daily_retention: 7
     weekly_retention: 4
     monthly_retention: 12

   max_local_backups: 0
   ```

2. **`configs/config2.yaml`**

   ```yaml
   backup_name: "config2"

   backup_paths:
     /etc: true
     /opt/data: true
     /var/log: false

   onedrive_remote:
     daily: "onedrive:/backups/config2/daily"
     weekly: "onedrive:/backups/config2/weekly"
     monthly: "onedrive:/backups/config2/monthly"

   retention:
     daily_retention: 5
     weekly_retention: 2
     monthly_retention: 6

   max_local_backups: 0
   ```

### Customizing the YAML Configuration

You can create additional YAML files in the `configs` directory to define more backup jobs. Below is the structure and explanations of each field.

#### YAML Configuration File Structure

```yaml
# Required: Unique name for the backup job (defaults to filename if omitted)
backup_name: "unique_backup_name"

# Required: Paths to include or exclude in the backup
backup_paths:
  /path/to/include1: true
  /path/to/include2: true
  /path/to/exclude: false

# Required: OneDrive remote paths for backups
onedrive_remote:
  daily: "onedrive:/backups/unique_backup_name/daily"
  weekly: "onedrive:/backups/unique_backup_name/weekly"
  monthly: "onedrive:/backups/unique_backup_name/monthly"

# Required: Retention settings for backups
retention:
  daily_retention: 7     # Keep last 7 daily backups
  weekly_retention: 4    # Keep last 4 weekly backups
  monthly_retention: 12  # Keep last 12 monthly backups

# Optional: Number of local backups to retain (defaults to 0)
max_local_backups: 3
```

#### Field Explanations

- **`backup_name`:**
  - *(Optional)* A unique identifier for the backup job.
  - If omitted, the script uses the YAML filename (without extension) as the backup name.

- **`backup_paths`:**
  - *(Required)* A dictionary specifying which directories to back up.
  - **Key:** Absolute path of the directory.
  - **Value:** `true` to include in the backup, `false` to exclude.

- **`onedrive_remote`:**
  - *(Required)* Specifies the OneDrive remote paths for storing backups.
  - **`daily`:** Path for daily backups.
  - **`weekly`:** Path for weekly backups.
  - **`monthly`:** Path for monthly backups.
  - Ensure that the remote name (`onedrive:`) matches your `rclone` configuration.

- **`retention`:**
  - *(Required)* Defines how many backups to retain for each frequency.
  - **`daily_retention`:** Number of daily backups to keep.
  - **`weekly_retention`:** Number of weekly backups to keep.
  - **`monthly_retention`:** Number of monthly backups to keep.

- **`max_local_backups`:**
  - *(Optional)* Specifies the maximum number of local backups to retain on the server.
  - Defaults to `0` if not specified, meaning no local backups are kept after transfer.
  - Set to a positive integer to retain that number of local backups.

### Creating Additional YAML Configurations

1. **Navigate to the `configs` Directory:**

   ```bash
   cd /home/user/rclone_backup_to_onedrive/configs
   ```

2. **Create a New YAML File:**

   ```bash
   nano my_backup.yaml
   ```

3. **Define Your Backup Configuration:**

   ```yaml
   backup_name: "my_custom_backup"

   backup_paths:
     /var/www: true
     /home/user/documents: true
     /etc: false
     /opt/data: true

   onedrive_remote:
     daily: "onedrive:/backups/my_custom_backup/daily"
     weekly: "onedrive:/backups/my_custom_backup/weekly"
     monthly: "onedrive:/backups/my_custom_backup/monthly"

   retention:
     daily_retention: 10
     weekly_retention: 5
     monthly_retention: 12

   max_local_backups: 2
   ```

4. **Save and Exit:**

   - Press `CTRL + O` to save.
   - Press `CTRL + X` to exit.

---

## Usage

### Manual Execution

Run the script manually to perform backups immediately or to test configurations.

#### Step-by-Step Guide:

1. **Activate the Virtual Environment (if not already active):**

   ```bash
   source /home/user/rclone_backup_to_onedrive/venv/bin/activate
   ```

2. **Navigate to the Project Directory:**

   ```bash
   cd /home/user/rclone_backup_to_onedrive
   ```

3. **Run the Script with Verbose Output:**

   ```bash
   python rclone_backup_to_onedrive.py -v
   ```

   - **Options:**
     - `-v` or `--verbose`: Enables verbose output, displaying detailed logs in the terminal.

4. **Monitor the Output:**

   - The script processes each YAML configuration, creates backups, and uploads them to OneDrive.
   - Detailed logs are written to `rclone_backup_to_onedrive.log` in the project directory.
   - If running with `-v`, logs are also displayed in the terminal.

5. **Verify Backups on OneDrive:**

   - Log in to your OneDrive account and navigate to the specified backup directories to ensure backups have been uploaded.

### Command-Line Arguments

The script offers flexibility in how configurations are processed.

#### Specifying YAML Configuration Files

You can specify one or more YAML configuration files to execute. If no files are specified, the script processes all YAML files in the `configs` directory in alphabetical order.

##### Examples:

1. **Execute Specific Configurations with Verbose Output:**

   ```bash
   python rclone_backup_to_onedrive.py config1.yaml config2.yaml -v
   ```

   - **Behavior:**
     - Processes `config1.yaml` and `config2.yaml` in the order they are listed.
     - Outputs detailed logs to the terminal.

2. **Execute All Configurations with Default Logging:**

   ```bash
   python rclone_backup_to_onedrive.py
   ```

   - **Behavior:**
     - Processes all YAML files in the `configs` directory in alphabetical order.
     - Logs details to `rclone_backup_to_onedrive.log` without displaying them in the terminal.

3. **Execute All Configurations with Verbose Output:**

   ```bash
   python rclone_backup_to_onedrive.py -v
   ```

   - **Behavior:**
     - Processes all YAML files in the `configs` directory in alphabetical order.
     - Outputs detailed logs to the terminal.

#### Running Without Specifying YAML Files

If you run the script without specifying any YAML files, it will automatically execute all YAML configurations found in the `configs` directory in alphabetical order, introducing a 5-second pause between each backup job to prevent resource contention.

---

## Restoration Guide

This guide provides step-by-step instructions to restore backups created by the `rclone_backup_to_onedrive.py` script. These steps will help you retrieve backups from OneDrive, extract the data, and ensure the correct permissions and ownership are restored on your server.

### 1. Prerequisites

Before starting the restoration process, ensure the following:

- **Installed and Configured `rclone`:**
  - Ensure `rclone` is installed and configured with access to your OneDrive account.
  - Test with `rclone lsf onedrive:/` to verify connectivity.

- **Sufficient Permissions:**
  - You need read/write permissions to the directories where you will restore the data.
  - Running as `root` or using `sudo` is recommended.

- **`tar` Utility:**
  - Ensure `tar` is installed on your system for extracting backups.

### 2. Restoring Backup Files from OneDrive

#### Step 1: List Available Backups

Use `rclone` to list the available backups in your OneDrive. Replace `<backup_name>` and `<backup_directory>` with your specific backup configuration name and backup type (`daily`, `weekly`, or `monthly`).

```bash
rclone lsf onedrive:/backups/<backup_name>/<backup_directory>/
```

**Example:**

```bash
rclone lsf onedrive:/backups/config1/daily/
```

#### Step 2: Download the Desired Backup

Choose the specific backup file you want to restore and download it to your local machine or server. Replace `<backup_name>`, `<backup_directory>`, and `<backup_file>` accordingly.

```bash
rclone copy onedrive:/backups/<backup_name>/<backup_directory>/<backup_file> /local/restore/path
```

**Example:**

```bash
rclone copy onedrive:/backups/config1/daily/daily-config1-20230903093000.tar.gz /home/user/restore/
```

### 3. Extracting the Backup

After downloading the backup file, extract its contents using the `tar` command. Ensure you specify the correct path where the backup should be restored.

```bash
sudo tar -xzf /local/restore/path/<backup_file> -C /target/restore/path
```

**Example:**

```bash
sudo tar -xzf /home/user/restore/daily-config1-20230903093000.tar.gz -C /
```

**Note:**

- Using `-C /` will extract the contents directly to the root filesystem, replicating the original paths. Ensure the target path does not overwrite important data unless intended.

### 4. Restoring File Permissions and Ownership

`tar` preserves file permissions and ownership by default. To ensure this explicitly, use:

```bash
sudo tar --preserve-permissions --preserve-order -xzf /local/restore/path/<backup_file> -C /target/restore/path
```

### 5. Verify Restored Files

It's crucial to verify the restored files to ensure the restoration was successful and data integrity is maintained.

- **Check File Integrity:** Manually check key files or use file checksums if available.
- **Check Permissions and Ownership:** Use `ls -l` to verify that files have the correct permissions.

**Example:**

```bash
ls -l /etc
```

### 6. Additional Considerations

- **Extended Attributes:** If your environment uses ACLs, SELinux contexts, or other extended attributes, ensure these attributes are correctly restored.
- **Testing:** Always test the restoration process in a safe environment before performing on a production server.
- **Automated Restore:** Consider scripting these steps if you frequently need to restore backups or plan to include restoration as part of a disaster recovery plan.

### 7. Troubleshooting Common Issues

- **Permission Denied Errors:** Ensure you are running the commands with the necessary privileges, e.g., as `root` or using `sudo`.
- **`rclone` Configuration Issues:** Re-run `rclone config reconnect onedrive:` if access to OneDrive is problematic.
- **File Not Found:** Double-check paths and file names, ensuring the correct case sensitivity.

---

## Troubleshooting

1. **Permission Denied Errors:**

   - **Cause:** Insufficient permissions to access or modify specified directories.
   - **Solution:** Run the script or commands as `root` or using `sudo`.

2. **Rclone Configuration Issues:**

   - **Cause:** Incorrect or incomplete `rclone` configuration for OneDrive.
   - **Solution:** Re-run `rclone config` to ensure OneDrive is correctly set up. Verify connectivity with `rclone lsf onedrive:/`.

3. **Cron Job Not Executing:**

   - **Cause:** Incorrect cron job entry or script permissions.
   - **Solution:**
     - Ensure the cron job path is absolute.
     - Verify that the script has executable permissions.
     - Check the cron log file (`/var/log/rclone_backup_to_onedrive_cron.log`) for errors.

4. **YAML Parsing Errors:**

   - **Cause:** Syntax errors or missing required fields in YAML configuration files.
   - **Solution:** Validate YAML files using a YAML validator or linter. Ensure all required fields are present.

5. **Snap-Related Errors:**

   - **Cause:** `rclone` installed via Snap causing confinement issues with cron jobs.
   - **Solution:** Ensure `rclone` is installed via APT as outlined in the installation instructions.

6. **Backup Not Found on OneDrive:**

   - **Cause:** Backup was not successfully uploaded.
   - **Solution:** Check the script log (`rclone_backup_to_onedrive.log`) for errors during the upload process. Ensure `rclone` has write permissions to the specified OneDrive directories.

7. **Missing Dependencies:**

   - **Cause:** Python packages not installed.
   - **Solution:** Ensure you are in the virtual environment and run `pip install -r requirements.txt`.

8. **Script Execution Issues:**

   - **Cause:** Virtual environment not activated or incorrect Python interpreter.
   - **Solution:** Activate the virtual environment using `source venv/bin/activate` and ensure the cron job points to the correct Python interpreter within the virtual environment.

---

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

---

By following this comprehensive guide, even novice users can set up and run the `rclone_backup_to_onedrive` script with confidence. The script's flexibility and detailed logging make it a robust solution for automated backups to OneDrive.

For any issues, contributions, or feature requests, please visit the [GitHub repository](https://github.com/drhdev/rclone_backup_to_onedrive).

---

**Happy Backing Up!**
