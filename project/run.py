import subprocess
import time
import sys
import os

# ==============================================================================
# NAVIGATTO PROJECT STARTUP SCRIPT
# ==============================================================================
# NOTE: Before running this script, please make sure your Redis server is running!
#
# -> To start Redis via Docker, run this command in your terminal:
#      docker start my-redis
#
# -> If you are running it for the very first time, use this instead:
#      docker run -d --name my-redis -p 6379:6379 redis

# ==============================================================================

def main():
    print("🚀 Starting Navigatto Project Services...\n")
    print("⚠️  Ensure your Redis Docker container is running! (Check the script comments for the command)\n")
    
    # Define commands with 'start cmd /k' to force visible pop-up windows on Windows
    backend_cmd = 'start cmd /k "TITLE Navigatto_Backend && python -m uvicorn main:app --reload --reload-exclude *.db --reload-exclude *.log --port 8000"'
    celery_cmd = 'start cmd /k "TITLE Navigatto_Celery && python -m celery -A maintenance_module.celery_app worker --loglevel=info -P solo"'
    frontend_cmd = 'start cmd /k "TITLE Navigatto_Frontend && npm run dev"'
    
    try:
        # 1. Start Backend
        print("[1/3] Starting FastAPI Backend...")
        subprocess.Popen(backend_cmd, cwd="backend", shell=True)
        time.sleep(2) # Give backend a second to initialize
        
        # 2. Start Celery Worker
        print("[2/3] Starting Celery Worker...")
        subprocess.Popen(celery_cmd, cwd="backend", shell=True)
        time.sleep(2)
        
        # 3. Start Frontend
        print("[3/3] Starting React/Vite Frontend...")
        subprocess.Popen(frontend_cmd, cwd="frontend", shell=True)
        
        print("\n✅ All services started in separate terminal windows!")
        print("🛑 Press Ctrl+C in THIS window to kill all services and exit.")
        
        # Keep the main script running in an infinite loop
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        # Force kill the windows using their Window Titles
        subprocess.call('taskkill /F /T /FI "WINDOWTITLE eq Navigatto_Backend*"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call('taskkill /F /T /FI "WINDOWTITLE eq Navigatto_Celery*"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call('taskkill /F /T /FI "WINDOWTITLE eq Navigatto_Frontend*"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()




#celery -A maintenance_module.celery_app worker --loglevel=info -P solo
#C:\Python313\python.exe -m uvicorn main:app --reload --port 8000