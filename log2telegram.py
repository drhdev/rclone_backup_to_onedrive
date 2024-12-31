#!/usr/bin/env python3
# log2telegram.py
# Version: 0.4.3
# Author: drhdev
# License: GPLv3
#
# Description:
# This script checks the 'rclone_backup_to_onedrive.log' file for any FINAL_STATUS entries
# and sends only the single most recently timestamped FINAL_STATUS entry as a Telegram message.
# It no longer tracks or remembers its last read position or inode; it simply reads the entire
# log file every time it is run, finds the newest FINAL_STATUS by timestamp, and sends it.

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
from datetime import datetime

# Load environment variables from .env if present
load_dotenv()

# Configuration
LOG_FILE_PATH = "rclone_backup_to_onedrive.log"  # Path to your log file
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

# Compile regex for FINAL_STATUS detection anywhere in the message
FINAL_STATUS_PATTERN = re.compile(r'FINAL_STATUS\s*\|', re.IGNORECASE)

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

def format_message(raw_message):
    """
    Formats the raw FINAL_STATUS log entry into a Markdown message for Telegram.
    Example Input:
        FINAL_STATUS | SUCCESS | Script: rclone_backup_to_onedrive.py | Host: pistar | Backup: daily-pistar-20241203184347.tar.gz | Timestamp: 2024-12-03 18:43:58
    Example Output:
        *FINAL_STATUS*
        *Status:* `SUCCESS`
        *Script:* `rclone_backup_to_onedrive.py`
        *Host:* `pistar`
        *Backup:* `daily-pistar-20241203184347.tar.gz`
        *Timestamp:* `2024-12-03 18:43:58`
    """
    parts = raw_message.split(" | ")
    if len(parts) != 6:
        logger.warning(f"Unexpected FINAL_STATUS format: {raw_message}")
        return raw_message  # Return as-is if format is unexpected

    # Unpack the parts
    _, status, script_info, host_info, backup_info, timestamp_info = parts

    # Extract values after the colon and space
    script_name = script_info.split(":", 1)[1].strip() if ":" in script_info else script_info
    host = host_info.split(":", 1)[1].strip() if ":" in host_info else host_info
    backup = backup_info.split(":", 1)[1].strip() if ":" in backup_info else backup_info
    timestamp = timestamp_info.split(":", 1)[1].strip() if ":" in timestamp_info else timestamp_info

    formatted_message = (
        f"*FINAL_STATUS*\n"
        f"*Status:* `{status}`\n"
        f"*Script:* `{script_name}`\n"
        f"*Host:* `{host}`\n"
        f"*Backup:* `{backup}`\n"
        f"*Timestamp:* `{timestamp}`"
    )
    return formatted_message

def process_log():
    """
    Reads the entire log file from start to finish, looking for FINAL_STATUS entries.
    Only the one with the most recent (largest) timestamp is sent to Telegram.
    """
    if not os.path.exists(LOG_FILE_PATH):
        logger.error(f"Log file '{LOG_FILE_PATH}' does not exist.")
        return

    try:
        with open(LOG_FILE_PATH, 'r') as f:
            lines = f.readlines()
            if not lines:
                logger.info("No lines found in the log file.")
                return

            logger.info(f"Read {len(lines)} line(s) from the log file.")

            latest_dt = None
            latest_message = None

            for line_number, line in enumerate(lines, start=1):
                original_line = line  # Keep the original line for debugging
                line = line.strip()

                # Split the log line into components: [timestamp, script, level, message]
                split_line = line.split(" - ", 3)
                if len(split_line) < 4:
                    logger.warning(f"Malformed log line (less than 4 parts): {original_line.strip()}")
                    continue

                message_part = split_line[3].strip()

                if FINAL_STATUS_PATTERN.search(message_part):
                    # Attempt to parse "Timestamp: YYYY-MM-DD HH:MM:SS"
                    match = re.search(r"Timestamp:\s*([\d\-:\s]+)", message_part)
                    if match:
                        timestamp_str = match.group(1).strip()
                        try:
                            dt_value = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if latest_dt is None or dt_value > latest_dt:
                                latest_dt = dt_value
                                latest_message = message_part
                            logger.debug(f"Line {line_number}: Found FINAL_STATUS with timestamp {timestamp_str}")
                        except ValueError:
                            logger.warning(f"Could not parse timestamp: {timestamp_str}")
                    else:
                        logger.debug(f"Line {line_number}: FINAL_STATUS found but no timestamp to compare.")
                else:
                    logger.debug(f"Line {line_number}: No FINAL_STATUS entry found.")
                    logger.debug(f"Processed Line {line_number}: {message_part}")

            if latest_message:
                logger.info("Sending only the single newest FINAL_STATUS entry.")
                send_telegram_message(latest_message)
            else:
                logger.info("No FINAL_STATUS entries found to send.")

    except Exception as e:
        logger.error(f"Error reading or processing log file: {e}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Reads 'rclone_backup_to_onedrive.log' for FINAL_STATUS entries, sending only the most recent one to Telegram."
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output to the console.')
    parser.add_argument('-d', '--delay', type=int, default=10,
                        help='Delay in seconds between sending multiple Telegram messages (if needed). Not crucial since only one message is sent.')
    args = parser.parse_args()

    # Set up console logging if verbose is enabled
    setup_console_logging(args.verbose)

    # Process the entire log file (always from the beginning)
    process_log()

if __name__ == "__main__":
    main()
