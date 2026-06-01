# setup_instance.py
# Deploys to the already-running EC2 instance at 3.111.36.4
# Run this after the instance is fully booted.

import os
import time
import subprocess
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'BE', '.env'))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PUBLIC_IP    = "3.111.36.4"
PEM_PATH     = os.path.join(os.path.dirname(__file__), "classifier-key.pem")
BASE         = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
USER         = "ubuntu"


def run_ssh(cmd, timeout=300):
    full = [
        "ssh", "-i", PEM_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{USER}@{PUBLIC_IP}", cmd
    ]
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip():
        print(f"    {r.stdout.strip()}")
    if r.returncode != 0 and r.stderr.strip():
        print(f"    STDERR: {r.stderr.strip()}")
    return r.returncode == 0


def run_scp(local, remote):
    cmd = [
        "scp", "-i", PEM_PATH,
        "-o", "StrictHostKeyChecking=no",
        local, f"{USER}@{PUBLIC_IP}:{remote}"
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def wait_for_ssh(max_wait=180):
    print("  Waiting for SSH...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = subprocess.run(
                ["ssh", "-i", PEM_PATH, "-o", "StrictHostKeyChecking=no",
                 "-o", "ConnectTimeout=5", f"{USER}@{PUBLIC_IP}", "echo ready"],
                capture_output=True, text=True, timeout=10
            )
            if "ready" in r.stdout:
                print("  SSH ready!")
                return
        except Exception:
            pass
        print("  ..retrying in 8s")
        time.sleep(8)
    raise TimeoutError("SSH not ready after 3 min")


if __name__ == "__main__":
    print("=" * 55)
    print(f"  Deploying to EC2: {PUBLIC_IP}")
    print("=" * 55)

    wait_for_ssh()

    # Ensure directories exist
    print("\n[1/5] Creating directories...")
    run_ssh("mkdir -p /home/ubuntu/classifier/BE/app /home/ubuntu/classifier/FE")

    # Copy source files
    print("\n[2/5] Copying source files...")
    files = [
        ("BE/app/__init__.py", "/home/ubuntu/classifier/BE/app/__init__.py"),
        ("BE/app/utils.py",    "/home/ubuntu/classifier/BE/app/utils.py"),
        ("BE/app/schemas.py",  "/home/ubuntu/classifier/BE/app/schemas.py"),
        ("BE/app/model.py",    "/home/ubuntu/classifier/BE/app/model.py"),
        ("BE/app/main.py",     "/home/ubuntu/classifier/BE/app/main.py"),
        ("BE/requirements.txt","/home/ubuntu/classifier/BE/requirements.txt"),
        ("FE/app.py",          "/home/ubuntu/classifier/FE/app.py"),
        ("FE/requirements.txt","/home/ubuntu/classifier/FE/requirements.txt"),
    ]
    for local_rel, remote in files:
        run_scp(os.path.join(BASE, local_rel), remote)
        print(f"    Copied {local_rel}")

    # Write .env
    env_tmp = os.path.join(os.path.dirname(__file__), "_tmp.env")
    with open(env_tmp, "w") as f:
        f.write(f"GROQ_API_KEY={GROQ_API_KEY}\nGROQ_MODEL=llama-3.1-8b-instant\n")
    run_scp(env_tmp, "/home/ubuntu/classifier/BE/.env")
    os.remove(env_tmp)
    print("    Copied .env")

    # Install BE deps
    print("\n[3/5] Installing backend dependencies (~90s)...")
    run_ssh(
        "cd /home/ubuntu/classifier/BE && "
        "python3 -m venv venv && source venv/bin/activate && "
        "pip install -q -r requirements.txt && deactivate",
        timeout=300
    )
    print("    Backend deps installed")

    # Install FE deps
    print("\n[4/5] Installing frontend dependencies (~90s)...")
    run_ssh(
        "cd /home/ubuntu/classifier/FE && "
        "python3 -m venv venv && source venv/bin/activate && "
        "pip install -q -r requirements.txt && deactivate",
        timeout=300
    )
    print("    Frontend deps installed")

    # Setup & start systemd services
    print("\n[5/5] Starting services...")
    run_ssh("""sudo bash -c 'cat > /etc/systemd/system/classifier-be.service << EOF
[Unit]
Description=Sentiment Classifier Backend
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/classifier/BE
EnvironmentFile=/home/ubuntu/classifier/BE/.env
ExecStart=/home/ubuntu/classifier/BE/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF'""")

    run_ssh("""sudo bash -c 'cat > /etc/systemd/system/classifier-fe.service << EOF
[Unit]
Description=Sentiment Classifier Frontend
After=classifier-be.service
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/classifier/FE
Environment=BACKEND_URL=http://localhost:8000
ExecStart=/home/ubuntu/classifier/FE/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF'""")

    run_ssh("sudo systemctl daemon-reload && sudo systemctl enable classifier-be classifier-fe && sudo systemctl start classifier-be classifier-fe")

    # Verify
    print("\n  Verifying (waiting 10s for services to start)...")
    time.sleep(10)
    run_ssh("curl -s http://localhost:8000/health")

    print()
    print("=" * 55)
    print("  DEPLOYMENT COMPLETE!")
    print("=" * 55)
    print(f"  Frontend  :  http://{PUBLIC_IP}:8501")
    print(f"  Backend   :  http://{PUBLIC_IP}:8000")
    print(f"  API Docs  :  http://{PUBLIC_IP}:8000/docs")
    print()
    print(f"  SSH: ssh -i {PEM_PATH} ubuntu@{PUBLIC_IP}")
    print("=" * 55)
