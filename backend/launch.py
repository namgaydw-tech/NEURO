"""One-shot launcher: sets env, starts server, prints PID."""
import os, sys, subprocess, time

os.environ["JWT_SECRET"] = "dev-secret-key-for-testing-change-in-production-12345678"
os.environ["ENABLE_DEMO_DATA"] = "true"
os.environ["APP_ENV"] = "development"
os.environ["HALLUCINATION_CHECK"] = "true"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".freebuff", "backend.log"), "w"),
    stderr=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".freebuff", "backend.log.err"), "w"),
    creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
)

print(f"Backend started with PID: {proc.pid}")
# Wait a few seconds to verify it's still alive
time.sleep(3)
if proc.poll() is None:
    print("Server is alive and listening")
else:
    print(f"Server exited with code {proc.returncode}")
    sys.exit(1)
