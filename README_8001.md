# Running the app on port 8001

Files added:

- `run_server_8001.ps1` — PowerShell script to start the app on port 8001 and capture logs.
- `start_server_8001.bat` — Batch wrapper that calls the PowerShell script.

Quick usage (PowerShell):

```powershell
# run with default (127.0.0.1:8001)
.\run_server_8001.ps1

# or explicitly set host/port
.\run_server_8001.ps1 -Host '0.0.0.0' -Port 8001
```

From CMD you can run the batch wrapper:

```cmd
start_server_8001.bat
```

Logs will be written to `uvicorn_out_8001.log` and `uvicorn_err_8001.log` in the repository root.

Notes:
- The script attempts a best-effort stop of any process listening on the selected port before launching uvicorn.
- If you have a privileged service listening on a port, stopping it may require Administrator rights.
- The script assumes `python` and required dependencies are on `PATH`.
how to run: In one powershell activate the venv and type this
uvicorn main:app --reload --port 8001

In teh next window type this:
python -m http.server 8002
