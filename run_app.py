import subprocess
import threading
import os

# Define the paths to your directories
FRONTEND_DIR = r"D:\Desktop\Navigatto_modules\project\frontend"
BACKEND_DIR = r"D:\Desktop\Navigatto_modules\project\backend"

def run_frontend():
    print("Starting Frontend...")
    subprocess.run("npm run dev", shell=True, cwd=FRONTEND_DIR)

def run_backend():
    print("Starting Backend...")
    subprocess.run("python -m uvicorn main:app --reload --port 8000", shell=True, cwd=BACKEND_DIR)

if __name__ == "__main__":
    # Create threads so both commands run at the same time
    frontend_thread = threading.Thread(target=run_frontend)
    backend_thread = threading.Thread(target=run_backend)

    # Start both
    frontend_thread.start()
    backend_thread.start()

    # Keep the script alive while they run
    frontend_thread.join()
    backend_thread.join()