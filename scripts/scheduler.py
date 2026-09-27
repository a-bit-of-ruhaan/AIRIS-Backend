import time
import subprocess
import os
import sys

def job():
    print("Running collection cycle...")
    try:
        # Run the cycle script
        script_path = os.path.join(os.path.dirname(__file__), 'run_cycle.py')
        subprocess.run([sys.executable, script_path], check=True)
        print("Cycle completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running cycle: {e}")

if __name__ == "__main__":
    print("Scheduler started. Running initial job...")
    job() # Run once on startup
    
    interval_hours = 6
    print(f"Entering schedule loop (runs every {interval_hours} hours)...")
    while True:
        time.sleep(interval_hours * 60 * 60)
        job()

