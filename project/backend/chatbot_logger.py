import time
import os
import sys

# Ensure stdout uses UTF-8 to avoid encoding crashes on Windows console when printing special symbols
if sys.platform.startswith("win"):
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

LOG_FILE = "chatbot.log"

def tail_file(filename):
    print("======================================================================")
    print("📋 FLEETIQ CHATBOT TRANSACTIONS & T-SQL LOGS CONSOLE")
    print(f"Watching log file: {os.path.abspath(filename)}")
    print("======================================================================\n")
    
    # Create file if it does not exist
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== Chatbot Logger Session Initialized ===\n")
            
    with open(filename, "r", encoding="utf-8") as f:
        # Go to the end of the file
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.3)
                continue
            sys.stdout.write(line)
            sys.stdout.flush()

if __name__ == "__main__":
    try:
        tail_file(LOG_FILE)
    except KeyboardInterrupt:
        print("\nExiting logger console.")
