#!/usr/bin/env python3
# log2telegram.py
# Version: 1.0.0
# Author: drhdev
# License: GPLv3
#
# Description:
# This script monitors the 'rclone_backup_to_onedrive.log' file for new FINAL_STATUS entries,
# sends them as formatted messages via Telegram, and then exits. It ensures
# that only new entries are sent by tracking the last read position and inode.
# Additionally, it introduces a configurable delay between sending multiple
# Telegram messages to avoid overwhelming the Telegram API.

import os
import sys
import json
import logging
import requests
import argparse
import re
import time
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables from .env if present
load_dotenv()

# Configuration
LOG_FILE_PATH = "rclone_backup_to_onedrive.log"  # Path to your log file
STATE_FILE_PATH = "log_notifier_state.json"      # Path to store the state
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Validate Telegram credentials
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set as environment variables.")
    sys.exit(1)

# Set up logging
log_filename = 'log2telegram.log'
logger = logging.getLogger('log2telegram.py')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def setup_console_logging(verbose: bool):
    """
    Sets up console logging if verbose is True.
    """
    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        logger.debug("Console logging enabled.")

class LogState:
    """
    Manages the state of the log file to track the last read position and inode.
    """
    def __init__(self, state_file):
        self.state_file = state_file
        self.inode = None
        self.position = 0
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.inode = data.get("inode")
                    self.position = data.get("position", 0)
                logger.debug(f"Loaded state: inode={self.inode}, position={self.position}")
            except Exception as e:
                logger.error(f"Failed to load state file: {e}")
        else:
            logger.debug("No existing state file found. Starting fresh.")

    def save_state(self, inode, position):
        try:
            with open(self.state_file, 'w') as f:
                json.dump({"inode": inode, "position": position}, f)
            logger.debug(f"Saved state: inode={inode}, position={position}")
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

# Compile regex for FINAL_STATUS detection (adjusted to new format)
# New FINAL_STATUS format:
# FINAL_STATUS | SUCCESS | Script: rclone_backup_to_onedrive.py | Host: hostname | Backup: config1.yaml | Timestamp: 2024-12-03 14:00:00
FINAL_STATUS_PATTERN = re.compile(r'^FINAL_STATUS\s*\|\s*(\w+)\s*\|\s*Script:\s*(.+?)\s*\|\s*Host:\s*(.+?)\s*\|\s*Backup:\s*(.+?)\s*\|\s*Timestamp:\s*(.+)$', re.IGNORECASE)

def send_telegram_message(message, retries=3, delay_between_retries=5):
    """
    Sends the given message to Telegram with a retry mechanism.
    """
    formatted_message = format_message(message)
    logger.debug(f"Formatted message to send: {formatted_message}")
    for attempt in range(1, retries + 1):
        try:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": formatted_message,
                "parse_mode": "Markdown"  # Using Markdown for better formatting
            }
            response = requests.post(TELEGRAM_API_URL, data=payload, timeout=10)
            logger.debug(f"Telegram API response: {response.status_code} - {response.text}")
            if response.status_code == 200:
                logger.info(f"Sent Telegram message: {formatted_message}")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Exception occurred while sending Telegram message: {e}")
        if attempt < retries:
            logger.info(f"Retrying in {delay_between_retries} seconds... (Attempt {attempt}/{retries})")
            time.sleep(delay_between_retries)
    logger.error(f"Failed to send Telegram message after {retries} attempts.")
    return False

def format_message(match):
    """
    Formats the raw FINAL_STATUS log entry into a Markdown message for Telegram.
    Example Input:
        FINAL_STATUS | SUCCESS | Script: rclone_backup_to_onedrive.py | Host: hostname | Backup: config1.yaml | Timestamp: 2024-12-03 14:00:00
    Example Output:
        *FINAL_STATUS*
        *Status:* `SUCCESS`
        *Script:* `rclone_backup_to_onedrive.py`
        *Host:* `hostname`
        *Backup:* `config1.yaml`
        *Timestamp:* `2024-12-03 14:00:00`
    """
    status, script_name, host, backup, timestamp = match.groups()
    formatted_message = (
        f"*FINAL_STATUS*\n"
        f"*Status:* `{status}`\n"
        f"*Script:* `{script_name}`\n"
        f"*Host:* `{host}`\n"
        f"*Backup:* `{backup}`\n"
        f"*Timestamp:* `{timestamp}`"
    )
    return formatted_message

def process_log(state: LogState, delay_between_messages: int):
    """
    Processes the log file for new FINAL_STATUS entries and sends them via Telegram.
    Introduces a delay between sending multiple messages to avoid overwhelming Telegram.
    """
    if not os.path.exists(LOG_FILE_PATH):
        logger.error(f"Log file '{LOG_FILE_PATH}' does not exist.")
        return

    try:
        with open(LOG_FILE_PATH, 'r') as f:
            st = os.fstat(f.fileno())
            current_inode = st.st_ino
            if state.inode != current_inode:
                # Log file has been rotated or is new
                logger.info("Detected new log file or rotation. Resetting position.")
                state.position = 0
                state.inode = current_inode

            f.seek(state.position)
            lines = f.readlines()
            if not lines:
                logger.info("No new lines to process.")
                return

            logger.info(f"Processing {len(lines)} new line(s).")
            final_status_entries = []
            for line_number, line in enumerate(lines, start=1):
                original_line = line  # Keep the original line for debugging
                line = line.strip()

                # Check if the line matches the FINAL_STATUS pattern
                match = FINAL_STATUS_PATTERN.match(line)
                if match:
                    final_status_entries.append((line_number, match))
                else:
                    logger.debug(f"Line {line_number}: No FINAL_STATUS entry found.")
                    logger.debug(f"Processed Line {line_number}: {line}")  # Log the actual message content

            if final_status_entries:
                logger.info(f"Detected {len(final_status_entries)} FINAL_STATUS entry(ies) to send.")
                for idx, (line_number, match) in enumerate(final_status_entries, start=1):
                    logger.debug(f"Line {line_number}: Detected FINAL_STATUS entry.")
                    success = send_telegram_message(match)
                    if not success:
                        logger.error(f"Failed to send Telegram message for line {line_number}: {line}")
                    if idx < len(final_status_entries):
                        logger.debug(f"Waiting for {delay_between_messages} seconds before sending the next message.")
                        time.sleep(delay_between_messages)
            else:
                logger.info("No FINAL_STATUS entries detected to send.")

            logger.info(f"Processed {len(final_status_entries)} FINAL_STATUS entry(ies).")

            # Update the state with the current file position
            state.position = f.tell()
            state.inode = current_inode
            state.save_state(state.inode, state.position)

    except Exception as e:
        logger.error(f"Error processing log file: {e}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Monitor 'rclone_backup_to_onedrive.log' for FINAL_STATUS entries and send them to Telegram.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output to the console.')
    parser.add_argument('-d', '--delay', type=int, default=10, help='Delay in seconds between sending multiple Telegram messages (default: 10 seconds).')
    args = parser.parse_args()

    # Set up console logging if verbose is enabled
    setup_console_logging(args.verbose)

    # Initialize log state
    state = LogState(STATE_FILE_PATH)

    # Process the log file with the specified delay
    process_log(state, delay_between_messages=args.delay)

if __name__ == "__main__":
    main()
