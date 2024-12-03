# rclone_backup_to_onedrive

![License](https://img.shields.io/github/license/drhdev/rclone_backup_to_onedrive)
![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![GitHub Stars](https://img.shields.io/github/stars/drhdev/rclone_backup_to_onedrive?style=social)

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Requirements](#requirements)
- [Installation Instructions](#installation-instructions)
  - [1. Install or Upgrade `rclone` via APT](#1-install-or-upgrade-rclone-via-apt)
  - [2. Configure `rclone` for OneDrive as Root](#2-configure-rclone-for-onedrive-as-root)
  - [3. Clone the Repository](#3-clone-the-repository)
  - [4. Set Up a Python Virtual Environment](#4-set-up-a-python-virtual-environment)
  - [5. Install Python Dependencies](#5-install-python-dependencies)
  - [6. Configure Environment Variables](#6-configure-environment-variables)
  - [7. Test the Scripts Manually](#7-test-the-scripts-manually)
  - [8. Set Up Cron Jobs for Automated Backups and Monitoring](#8-set-up-cron-jobs-for-automated-backups-and-monitoring)
- [Usage](#usage)
- [Restoration Guide](#restoration-guide)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Description

`rclone_backup_to_onedrive` is a robust solution for automating the backup of critical directories to Microsoft OneDrive. It leverages `rclone` for efficient data transfer and provides two Python scripts:

1. **`rclone_backup_to_onedrive.py`**: Automates the backup process based on configurations defined in YAML files. It handles the creation of compressed tarball backups, manages retention policies, and ensures backups are systematically rotated.

2. **`log2telegram.py`**: Monitors the backup logs for `FINAL_STATUS` entries and sends real-time notifications to a specified Telegram chat. This ensures you are immediately informed about the success or failure of your backup operations.

By integrating these scripts, you can achieve seamless, automated backups with proactive monitoring and notifications.

---

## Features

- **YAML-Based Configuration**:
  - Define multiple backup jobs with distinct settings in individual YAML files.
  - Pre-configured `configs` directory with example configurations (`config1.yaml` and `config2.yaml`).

- **Flexible Backup Management**:
  - Specify directories to include or exclude in backups.
  - Support for daily, weekly, and monthly backups with customizable retention counts.
  - Per-configuration control over the number of local backups to retain.

- **Automated Backup Rotation**:
  - Automatically rotates backups based on the defined schedule.
  - Manages retention policies by deleting older backups beyond the specified count.

- **Comprehensive Logging**:
  - Detailed logs for each step of every backup job.
  - `FINAL_STATUS` messages indicating `SUCCESS` or `FAILURE` for easy monitoring.

- **Real-Time Monitoring and Reporting**:
  - `log2telegram.py` script monitors backup logs and sends notifications via Telegram.
  - Immediate alerts on backup successes or failures for proactive management.

- **Cron Compatibility**:
  - Designed to work seamlessly with cron jobs for automated scheduling.
  - Avoids issues related to Snap installations when running via cron.

- **Error Handling**:
  - Validates configurations and handles errors gracefully without halting execution.
  - Logs errors for each backup job individually.

---

## Requirements

- **Operating System**: Linux (Tested on Ubuntu 22.04 and 24.04)
- **Python**: Python 3.x
- **Rclone**: Installed via APT (version 1.50 or higher)
- **Python Packages**: Listed in `requirements.txt`

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
  
   ```bash   
   sudo rclone selfupdate
   ```
   
   - **Expected Output:** `NOTICE: Successfully updated rclone from version vx.xx.x to version vx.xx.x`

### 2. Configure `rclone` for OneDrive as Root

Configuring `rclone` for OneDrive involves authorizing access to your OneDrive account. Since the backup scripts and cron jobs will run as `root`, it's essential to configure `rclone` for the `root` user to ensure seamless operation without permission issues.

#### Step-by-Step Guide:

1. **Run `rclone config` as Root:**

   Execute the configuration process with `root` privileges to ensure the configuration is stored for the `root` user.

   ```bash
   sudo rclone config
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

   - Return to your server terminal.
   - Paste the verification code when prompted.

10. **Finalize Configuration:**

    - Type `y` to confirm the configuration.
    - Type `q` to quit the configuration menu.

11. **Verify OneDrive Access:**

    ```bash
    sudo rclone lsf onedrive:/
    ```

    - This should list the contents of your OneDrive root directory.

**Note:** Configuring `rclone` as `root` ensures that any scripts or cron jobs running with `root` privileges can access the OneDrive remote without encountering permission issues.

### 3. Clone the Repository

#### Step-by-Step Guide:

1. **Navigate to Your Desired Directory:**

   Choose a directory where you want to place the backup scripts. For organizational purposes, it's recommended to use a directory like `/opt`.

   ```bash
   sudo mkdir -p /opt/rclone_backup_to_onedrive
   cd /opt/rclone_backup_to_onedrive
   ```

2. **Clone the Repository:**

   ```bash
   sudo git clone https://github.com/drhdev/rclone_backup_to_onedrive.git .
   ```

   - Cloning into the current directory (`.`) ensures that all repository contents are placed directly in `/opt/rclone_backup_to_onedrive`.

3. **Set Ownership (Optional):**

   If you prefer, you can assign ownership of the directory to `root` to maintain consistent permissions.

   ```bash
   sudo chown -R root:root /opt/rclone_backup_to_onedrive
   ```

### 4. Set Up a Python Virtual Environment

Using a virtual environment is recommended to manage dependencies without affecting system-wide packages.

#### Step-by-Step Guide:

1. **Create a Virtual Environment:**

   ```bash
   sudo python3 -m venv venv
   ```

   - This creates a virtual environment named `venv` in the project directory.

2. **Activate the Virtual Environment:**

   ```bash
   source venv/bin/activate
   ```

   - Your terminal prompt should now indicate that the virtual environment is active.

### 5. Install Python Dependencies

The scripts rely on certain Python packages listed in `requirements.txt`.

#### Step-by-Step Guide:

1. **Ensure You Are in the Virtual Environment:**

   - If not already activated, activate it:

     ```bash
     source venv/bin/activate
     ```

2. **Install Dependencies Using `pip` with `sudo`:**

   Since the virtual environment is located in a directory that requires root permissions, you need to install the packages with `sudo`.

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/pip install -r requirements.txt
   ```

   - **Explanation:**
     - **`sudo`**: Grants the necessary permissions to write to the `venv` directory.
     - **Absolute Path to `pip`**: Ensures that you're using the `pip` associated with your virtual environment.

   **Note:** Avoid using `sudo pip install` within a virtual environment unless necessary, as it can lead to permission issues. In this case, it's required because the `venv` directory is owned by `root`.

### 6. Configure Environment Variables

The scripts require Telegram credentials to send notifications. These are managed via environment variables.

#### Step-by-Step Guide:

1. **Create and Edit the `.env` File:**

   ```bash
   sudo nano /opt/rclone_backup_to_onedrive/.env
   ```

2. **Add Your Telegram Credentials:**

   Replace `your_telegram_bot_token` and `your_telegram_chat_id` with your actual Telegram Bot Token and Chat ID.

   ```plaintext
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

3. **Secure Your `.env` File:**

   The `.env` file contains sensitive information. Ensure it's secured and not exposed publicly.

   ```bash
   sudo chmod 600 /opt/rclone_backup_to_onedrive/.env
   ```

4. **Add `.env` to `.gitignore` to Prevent Accidental Commits:**

   ```bash
   echo ".env" | sudo tee -a /opt/rclone_backup_to_onedrive/.gitignore
   ```

### 7. Test the Scripts Manually

Before scheduling automated backups and monitoring, it's essential to verify that the scripts operate correctly.

#### Step-by-Step Guide:

1. **Ensure the Virtual Environment is Active:**

   ```bash
   source /opt/rclone_backup_to_onedrive/venv/bin/activate
   ```

2. **Run the Backup Script with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py -v
   ```

   - **Options:**
     - `-v` or `--verbose`: Enables verbose output, displaying detailed logs in the terminal.

3. **Monitor the Output:**

   - The script processes the configurations and outputs logs to the console and the log file `rclone_backup_to_onedrive.log`.

4. **Run the Monitoring Script with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v
   ```

   - **Options:**
     - `-v` or `--verbose`: Enables verbose output, displaying detailed logs in the terminal.
     - `-d` or `--delay`: (Optional) Delay in seconds between sending multiple Telegram messages (default: 10 seconds).

5. **Verify Backups on OneDrive:**

   - Log in to your OneDrive account and navigate to the specified backup directories to ensure backups have been uploaded.

6. **Verify Telegram Notifications:**

   - Check your Telegram chat for notifications sent by `log2telegram.py` regarding the backup status.

### 8. Set Up Cron Jobs for Automated Backups and Monitoring

Automate the backup and monitoring process by scheduling cron jobs to run the backup script and the monitoring script (`log2telegram.py`) at desired intervals.

#### Step-by-Step Guide:

1. **Determine the Absolute Paths of the Scripts:**

   Assuming your project is located at `/opt/rclone_backup_to_onedrive`.

   - **Backup Script Path:** `/opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py`
   - **Monitoring Script Path:** `/opt/rclone_backup_to_onedrive/log2telegram.py`
   - **Virtual Environment Python Path:** `/opt/rclone_backup_to_onedrive/venv/bin/python`

2. **Ensure Both Scripts are Executable:**

   ```bash
   sudo chmod +x /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py
   sudo chmod +x /opt/rclone_backup_to_onedrive/log2telegram.py
   ```

3. **Edit the Root’s Crontab:**

   Running the cron job as `root` ensures access to all directories that require elevated permissions.

   ```bash
   sudo crontab -e
   ```

4. **Add the Cron Job Entries:**

   Below are examples of how to set up cron jobs to run both scripts. Adjust the schedule as needed.

   - **Example 1: Run Both Scripts Daily at 4:00 AM with Multiple YAML Configurations**

     ```cron
     0 4 * * * /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py config1.yaml config2.yaml -v && /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v >> /var/log/rclone_backup_and_monitor_cron.log 2>&1
     ```

     - **Explanation:**
       - `0 4 * * *`: Runs daily at 4:00 AM.
       - Executes `rclone_backup_to_onedrive.py` with both `config1.yaml` and `config2.yaml` in verbose mode.
       - Upon successful completion, immediately runs `log2telegram.py` in verbose mode to send notifications.
       - Redirects both `stdout` and `stderr` to `/var/log/rclone_backup_and_monitor_cron.log` for monitoring.

   - **Example 2: Run Both Scripts Hourly with All YAML Configurations**

     ```cron
     0 * * * * /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py -v && /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v >> /var/log/rclone_backup_and_monitor_cron.log 2>&1
     ```

     - **Explanation:**
       - `0 * * * *`: Runs at the start of every hour.
       - Executes the backup script with all YAML configurations in verbose mode.
       - Immediately runs the monitoring script to send notifications.
       - Logs output to `/var/log/rclone_backup_and_monitor_cron.log`.

   - **Example 3: Run Both Scripts Multiple Times a Day with Different YAML Files**

     ```cron
     0 2,14 * * * /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py config1.yaml -v && /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v >> /var/log/rclone_backup_and_monitor_cron.log 2>&1
     30 6,18 * * * /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py config2.yaml -v && /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v >> /var/log/rclone_backup_and_monitor_cron.log 2>&1
     ```

     - **Explanation:**
       - **First Entry (`0 2,14 * * *`):** Runs daily at 2:00 AM and 2:00 PM.
         - Executes the backup script with `config1.yaml` in verbose mode.
         - Immediately runs the monitoring script to send notifications.
       - **Second Entry (`30 6,18 * * *`):** Runs daily at 6:30 AM and 6:30 PM.
         - Executes the backup script with `config2.yaml` in verbose mode.
         - Immediately runs the monitoring script to send notifications.
       - Both entries log output to `/var/log/rclone_backup_and_monitor_cron.log`.

5. **Save and Exit:**

   - After adding the cron job entries, save and exit the editor. The cron service will recognize and apply the new jobs automatically.

6. **Verify Cron Job Execution:**

   - After the scheduled times, check the cron log to ensure the scripts ran successfully.

     ```bash
     sudo cat /var/log/rclone_backup_and_monitor_cron.log
     ```

   - Look for `FINAL_STATUS` messages indicating `SUCCESS` or `FAILURE` for each backup job.

**Note on Using `sudo` with Cron Jobs:**

- **Installation and Configuration as `root`:**
  - Installing `rclone` via APT requires `sudo` privileges.
  - Configuring `rclone` for OneDrive as `root` ensures that cron jobs running as `root` can access the configuration without issues.

- **Running Scripts as `root`:**
  - Since cron jobs are scheduled in the `root`'s crontab, `rclone` is already configured for `root`, eliminating permission issues during execution.

By following these instructions, `rclone_backup_to_onedrive.py` and `log2telegram.py` will operate seamlessly together, providing automated backups and real-time monitoring through Telegram notifications without encountering permission-related problems.

---

## Usage

### Manual Execution of Backup and Monitoring Scripts

Before automating the process with cron jobs, you can manually execute the scripts to ensure everything is set up correctly.

#### Step-by-Step Guide:

1. **Activate the Virtual Environment:**

   ```bash
   source /opt/rclone_backup_to_onedrive/venv/bin/activate
   ```

2. **Run the Backup Script with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py -v
   ```

   - **Options:**
     - `-v` or `--verbose`: Enables verbose output, displaying detailed logs in the terminal.

3. **Monitor the Output:**

   - The script processes the configurations and outputs logs to the console and the log file `rclone_backup_to_onedrive.log`.

4. **Run the Monitoring Script with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/log2telegram.py -v
   ```

   - **Options:**
     - `-v` or `--verbose`: Enables verbose output, displaying detailed logs in the terminal.
     - `-d` or `--delay`: (Optional) Delay in seconds between sending multiple Telegram messages (default: 10 seconds).

5. **Verify Backups on OneDrive:**

   - Log in to your OneDrive account and navigate to the specified backup directories to ensure backups have been uploaded.

6. **Verify Telegram Notifications:**

   - Check your Telegram chat for notifications sent by `log2telegram.py` regarding the backup status.

### Command-Line Arguments for Backup Script

The backup script offers flexibility in how configurations are processed.

#### Specifying YAML Configuration Files

You can specify one or more YAML configuration files to execute. If no files are specified, the script processes all YAML files in the `configs` directory in alphabetical order.

##### Examples:

1. **Execute Specific Configurations with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py config1.yaml config2.yaml -v
   ```

   - **Behavior:**
     - Processes `config1.yaml` and `config2.yaml` in the order they are listed.
     - Outputs detailed logs to the terminal.

2. **Execute All Configurations with Default Logging:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py
   ```

   - **Behavior:**
     - Processes all YAML files in the `configs` directory in alphabetical order.
     - Logs details to `rclone_backup_to_onedrive.log` without displaying them in the terminal.

3. **Execute All Configurations with Verbose Output:**

   ```bash
   sudo /opt/rclone_backup_to_onedrive/venv/bin/python /opt/rclone_backup_to_onedrive/rclone_backup_to_onedrive.py -v
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
  - Test with `sudo rclone lsf onedrive:/` to verify connectivity.

- **Sufficient Permissions:**
  - You need read/write permissions to the directories where you will restore the data.
  - Running as `root` or using `sudo` is recommended.

- **`tar` Utility:**
  - Ensure `tar` is installed on your system for extracting backups.

### 2. Restoring Backup Files from OneDrive

#### Step 1: List Available Backups

Use `rclone` to list the available backups in your OneDrive. Replace `<backup_name>` and `<backup_directory>` with your specific backup configuration name and backup type (`daily`, `weekly`, or `monthly`).

```bash
sudo rclone lsf onedrive:/backups/<backup_name>/<backup_directory>/
```

**Example:**

```bash
sudo rclone lsf onedrive:/backups/hostname/daily/
```

#### Step 2: Download the Desired Backup

Choose the specific backup file you want to restore and download it to your local machine or server. Replace `<backup_name>`, `<backup_directory>`, and `<backup_file>` accordingly.

```bash
sudo rclone copy onedrive:/backups/<backup_name>/<backup_directory>/<backup_file> /local/restore/path
```

**Example:**

```bash
sudo rclone copy onedrive:/backups/hostname/daily/daily-backup-config1-20230903093000.tar.gz /home/user/restore/
```

### 3. Extracting the Backup

After downloading the backup file, extract its contents using the `tar` command. Ensure you specify the correct path where the backup should be restored.

```bash
sudo tar -xzf /local/restore/path/<backup_file> -C /target/restore/path
```

**Example:**

```bash
sudo tar -xzf /home/user/restore/daily-backup-config1-20230903093000.tar.gz -C /
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
- **`rclone` Configuration Issues:** Re-run `sudo rclone config reconnect onedrive:` if access to OneDrive is problematic.
- **File Not Found:** Double-check paths and file names, ensuring the correct case sensitivity.

---

## Troubleshooting

1. **Permission Denied Errors:**

   - **Cause:** Insufficient permissions to access or modify specified directories.
   - **Solution:** Run the script or commands as `root` or using `sudo`.

2. **Rclone Configuration Issues:**

   - **Cause:** Incorrect or incomplete `rclone` configuration for OneDrive.
   - **Solution:** Re-run `sudo rclone config` to ensure OneDrive is correctly set up. Verify connectivity with `sudo rclone lsf onedrive:/`.

3. **Cron Job Not Executing:**

   - **Cause:** Incorrect cron job entry or script permissions.
   - **Solution:**
     - Ensure the cron job path is absolute.
     - Verify that the scripts have executable permissions.
     - Check the cron log file (`/var/log/rclone_backup_and_monitor_cron.log`) for errors.

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
   - **Solution:** Ensure you are in the virtual environment and run `sudo /opt/rclone_backup_to_onedrive/venv/bin/pip install -r requirements.txt`.

8. **Script Execution Issues:**

   - **Cause:** Virtual environment not activated or incorrect Python interpreter.
   - **Solution:** Activate the virtual environment using `source /opt/rclone_backup_to_onedrive/venv/bin/activate` and ensure the cron job points to the correct Python interpreter within the virtual environment.

---

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

---

By following this comprehensive guide, eveyone should be able to set up and run the `rclone_backup_to_onedrive.py` and `log2telegram.py` scripts with confidence. Configuring `rclone` for `root` ensures that backups and monitoring operate seamlessly without encountering permission-related issues, especially when running via `root` cron jobs. The scripts' flexibility and detailed logging make them robust solutions for automated backups and real-time monitoring via Telegram.

For any issues, contributions, or feature requests, please visit the [GitHub repository](https://github.com/drhdev/rclone_backup_to_onedrive).

---

**Happy Backing Up and Monitoring!**

