import os
import sys

import uvicorn

if __name__ == "__main__":
    # Reload is useful in dev but is unreliable on Windows paths with spaces.
    # Opt-in via RELOAD=1 env var; default to off for predictable behavior.
    reload = os.environ.get("RELOAD", "0") == "1"
    # Force line-buffered stdout so logs stream in real time on Windows.
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=reload)
