
import os, sys, subprocess, webbrowser, time, socket, shutil, pathlib

BASE = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent)).resolve()
APP_DIR = BASE if (BASE / "app.py").exists() else pathlib.Path(__file__).parent.resolve()

# Prepare local data directories
data_dir = APP_DIR / "data"
uploads_dir = data_dir / "uploads"
data_dir.mkdir(exist_ok=True, parents=True)
uploads_dir.mkdir(exist_ok=True, parents=True)

# Env for the app
os.environ.setdefault("FC_DB_PATH", str(data_dir / "fluxo.db"))
os.environ.setdefault("FC_UPLOAD_DIR", str(uploads_dir))

# Streamlit server config: use fixed port if free, else pick any
def find_free_port(preferred=8501):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

port = find_free_port(8501)
url = f"http://127.0.0.1:{port}"

# Build command
cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port), "--server.address", "127.0.0.1"]
# On first run, set a minimal config to avoid sharing telemetry prompts
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

# Launch server
proc = subprocess.Popen(cmd, cwd=str(APP_DIR))
time.sleep(2)
try:
    webbrowser.open(url)
except:
    pass

# Wait until server exits
proc.wait()
sys.exit(proc.returncode)
