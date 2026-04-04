import subprocess
import time
with open("server_log.txt", "w") as f:
    process = subprocess.Popen(["python", "manage.py", "runserver"], stdout=f, stderr=subprocess.STDOUT)
    time.sleep(5)
    if process.poll() is not None:
        print("Server failed to start!")
    else:
        print(f"Server started successfully with PID {process.pid}")
