import win32api
from time import sleep
import psutil
import threading
import subprocess

drive_letter = "E:\\"
drivename = "Flatios"
process_name = "SystemSettings.exe"

def check_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            subprocess.call(['taskkill', '/F', '/PID', str(proc.info['pid'])])
            break

def check_drive_label():
    try:
        return win32api.GetVolumeInformation(drive_letter)[0] == drivename 
    except: 
        return False

def main():
    process_thread = threading.Thread(target=check_process, args=(process_name,))
    process_thread.start()
    
while True:
    if not check_drive_label(): main()
    else: print(f"{drivename} Mod Activated Success Software closed :D"); break
    sleep(5)
