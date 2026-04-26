#!/usr/bin/env python
"""WebServerWatcher monitors web server logs for successful 200 codes."""

# webserverwatcher.py
# WebServerWatcher v2026.04.26

# Copyright (C) 2026 Michael McMahon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# "Who will watch the watchmen?"

# WebServerWatcher monitors active web server logs for successful 200 codes. If
# a successfuly 200 code is not found within a reasonable time, the web server
# service will be restarted.

# The goal of this project is to be more responsive than systemd and more
# accurate than a random pause.

# Note: This currently only works with a standard apache2/nginx combined log
# file format at this time.

# In order to run, this script requires permission to restart services and view
# log files. Run with this command:
#   python3 webservicewatcher.py

# This only uses standard python libraries so in hopes of living off the land.
# Import libraries
from datetime import datetime
import re
import subprocess
import syslog
import time
import configparser

# Configuration
config = configparser.ConfigParser()
config.read("config/webserverwatcher.ini")

# Access values
# Enable/disable verbose debugging
debug = config.getint("general", "debug")
# The log file will be monitored for activity
logfile = config.get("log", "logfile")
# Seconds since a 200 code to restart the web service.
WINDOW_SECONDS = config.getfloat("time", "WINDOW_SECONDS")
# Seconds to wait after service restart.
WAIT_SECONDS = config.getfloat("time", "WAIT_SECONDS")
# Service that needs to be restarted
webservice = config.get("systemd", "webservice")
# Path for systemctl
systemctl_path = config.get("systemd", "systemctl_path")

# TODO Add more config options for different log file configurations.

if debug == 1:
    print("Variables:")
    print(f"logfile: {logfile}")
    print(f"Time: {WINDOW_SECONDS}:{WAIT_SECONDS}")
    print(f"Service: {webservice}")
    print(f"systemctl: {systemctl_path}")


def read_last_matching_line(filepath):
    try:
        # Read file line by line to handle line breaks correctly
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Read lines from the bottom up.
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()

            # Regular expression looks for a 200 surrounded by spaces with
            # anything before or after that.
            if re.search(r"^.* 200 .*$", line):
                return line.strip()

        # If no match is found, return None.
        return None

    except FileNotFoundError:
        syslog.syslog(syslog.LOG_ERR, f"Log file not found: {filepath}")
        print(f"Error: File not found at {filepath}")


def process_log_time(line):
    """
    Parse a single line from the log file, parse the timestamp, and return the
    time in seconds since epoch.
    """
    # Example NGINX/Apache2 log line:
    # 127.0.0.1 - - [03/Apr/2026:16:44:19 -0400] "GET / HTTP/1.1" 200 9575 "-"
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
    # (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

    # Remove the first parts (IP address and dashes) to isolate the timestamp.
    # TODO This is brittle as some logs have different formatting. Suggest
    # improvements please.
    parts = line.split(" ")
    # print(parts)
    if len(parts) > 1:
        timestamp_str = parts[3].split()[0].strip("[]")
        if debug == 1:
            print(timestamp_str)
        # Parse the timestamp string in seconds since epoch.
        # Format: DD/Mon/YY:HH:MM:SS
        #         03/Apr/2026:16:44:19
        try:
            dt = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S")
            if debug == 1:
                print(dt)
            ts_sec = dt.timestamp()
            if debug == 1:
                print(ts_sec)
        except ValueError:
            syslog.syslog(
                syslog.LOG_ERR,
                "Parsing timestamp failed. Fix datetime parsing.",
            )
            print("Error: Parsing timestamp failed. Fix datetime parsing.")
            exit()

        if debug == 1:
            print(ts_sec, line)
        return ts_sec


# Find current time in seconds since epoch.
def get_current_time():
    return time.time()


def restart_service():
    try:
        # Run the systemctl command using subprocess.
        #   systemctl restart apache2
        syslog.syslog(
            syslog.LOG_ERR,
            f"Restarting {webservice} due to 200 inactivity.",
        )
        print(f"Restarting {webservice} due to 200 inactivity.")
        # TODO Add dry-run mode.
        # print(f"/bin/echo {systemctl_path} restart {webservice}")
        # result = subprocess.run(
        #    ['/bin/echo', systemctl_path, 'restart', webservice],
        #    stdout=subprocess.PIPE,
        #    stderr=subprocess.PIPE
        result = subprocess.run(
            [systemctl_path, "restart", webservice],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if debug == 1:
            print(result.stdout, result.stderr, result.returncode)

        if result.returncode == 0:
            print("Service restarted successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error restarting service: {e.stderr.decode()}")
    except FileNotFoundError:
        print("systemctl not found. Make sure systemd is installed.")


def check_for_200():
    result = read_last_matching_line(logfile)
    if result:
        if debug == 1:
            print(f"Found last matching line: {result}")
        last_200_time = process_log_time(result)
        if debug == 1:
            print(last_200_time)
        current_time = get_current_time()
        if debug == 1:
            print(current_time)
            print(current_time - last_200_time, ">", WINDOW_SECONDS)
        if (current_time - last_200_time) > WINDOW_SECONDS:
            syslog.syslog("Engaging {webservice} restart!")
            print(f"Engaging {webservice} restart!")
            restart_service()

    else:
        if debug == 1:
            print("No match found.")
            print("The logs might have just rotated.")


def main():
    syslog.syslog("Process started.")

    while True:
        check_for_200()

        if debug == 1:
            print(f"Waiting for {WAIT_SECONDS} seconds...")
        # Wait for the approximate time for new 200 codes to come in.
        time.sleep(WAIT_SECONDS)


if __name__ == "__main__":
    main()
