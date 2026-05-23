import subprocess
import time
import os
import webbrowser
import threading

# Define paths
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")
frontend_dir = os.path.join(root_dir, "frontend")

# Define python executable inside venv
python_exe = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
if not os.path.exists(python_exe):
    # Fallback to general python if venv not found
    python_exe = "python"

print("="*60)
print("             PlacementCrack Platform Bootloader             ")
print("="*60)

# 1. Start backend server
print("\n[1/3] Launching Python FastAPI secure backend server...")
backend_process = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
    cwd=backend_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# 2. Start frontend dev server binding to IPv4 on port 3000 to prevent EACCES errors
print("[2/3] Launching React & Vite frontend developer suite...")
frontend_process = subprocess.Popen(
    ["cmd", "/c", "npm run dev -- --host 127.0.0.1 --port 3000"],
    cwd=frontend_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# URLs
frontend_url = "http://127.0.0.1:3000"
backend_url = "http://localhost:8000"
docs_url = "http://localhost:8000/docs"

time.sleep(3)  # Let them boot up a bit

print("\n" + "="*60)
print("  PLACEMENTCRACK PLATFORM IS NOW LIVE!")
print(f"  -> Frontend Client: {frontend_url}")
print(f"  -> Backend API:    {backend_url}")
print(f"  -> Swagger Docs:   {docs_url}")
print("="*60)
print("\n[3/3] Opening your default browser to PlacementCrack Gateway...")

# Automatically open browser
webbrowser.open(frontend_url)

print("\nMonitoring logs... Press Ctrl+C to terminate both servers and exit...\n")

# Monitored loop to read output and keep script alive, plus handle clean terminate on exit
try:
    def monitor_stream(process, prefix):
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Clean potential unicode from logs as well
                    clean_line = line.encode('ascii', errors='ignore').decode('ascii')
                    print(f"[{prefix}] {clean_line.strip()}")
        except Exception:
            pass
        finally:
            try:
                process.stdout.close()
            except Exception:
                pass
        
    t1 = threading.Thread(target=monitor_stream, args=(backend_process, "Backend"), daemon=True)
    t2 = threading.Thread(target=monitor_stream, args=(frontend_process, "Frontend"), daemon=True)
    
    t1.start()
    t2.start()
    
    while True:
        # Check if either process died
        if backend_process.poll() is not None:
            print("\n[Warning] Backend process exited unexpectedly.")
            break
        if frontend_process.poll() is not None:
            print("\n[Warning] Frontend process exited unexpectedly.")
            break
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[Shutting Down] Terminating processes gracefully...")
finally:
    # Graceful shutdown of subprocesses in Windows
    if backend_process.poll() is None:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)], capture_output=True)
        except Exception:
            backend_process.terminate()
            
    if frontend_process.poll() is None:
        try:
            # Kill command process and its children so port is cleanly freed
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], capture_output=True)
        except Exception:
            frontend_process.terminate()
            
    print("Both servers cleanly shut down. Goodbye!")
