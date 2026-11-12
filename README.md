# Keylogger Project

## Description

This is a keylogger project that records keystrokes, clipboard content, active window titles, and sends the collected data to a Discord webhook. This tool is intended strictly for educational purposes or for monitoring devices that you own, with explicit consent from all users of the device.

## Features
- Records keystrokes and saves them to a log file.
- Captures clipboard content and logs it.
- Logs the titles of active windows.
- Sends collected data to a Discord webhook at regular intervals.

## Installation

To install and use this keylogger, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/Ludusm11/input_logger.git
   cd input_logger
   ```

2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

After installation, you can run the keylogger with the following command:

```sh
python keylog.py
```

Make sure to configure the `DISCORD_WEBHOOK_URL` in the script before running it.


- **Discord**: ludvs

---

Thank you for using this project.
