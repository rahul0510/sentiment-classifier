# deploy_ec2.py
# Phase 1: Launch EC2 t2.micro, open ports, wait until SSH is ready
# Phase 2: SCP project files, install deps, start services via SSH

import boto3
import os
import time
import subprocess
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'BE', '.env'))

# ── Config ─────────────────────────────────────────────────────────────────────
AWS_REGION     = "ap-south-1"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

AMI_ID        = "ami-0f58b397bc5c1f2e8"   # Ubuntu 22.04 LTS ap-south-1
INSTANCE_TYPE = "t3.micro"   # free-tier eligible in ap-south-1
KEY_NAME      = "classifier-key"
SG_NAME       = "classifier-sg"
PEM_PATH      = os.path.join(os.path.dirname(__file__), f"{KEY_NAME}.pem")
BASE          = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Minimal user-data: just install Python and create directory structure
MINIMAL_USER_DATA = """#!/bin/bash
apt-get update -y
apt-get install -y python3-pip python3-venv
mkdir -p /home/ubuntu/classifier/BE/app
mkdir -p /home/ubuntu/classifier/FE
chown -R ubuntu:ubuntu /home/ubuntu/classifier
"""

# ── Boto3 ──────────────────────────────────────────────────────────────────────
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)
ec2        = session.resource("ec2")
ec2_client = session.client("ec2")


# ── Phase 1: Provision ────────────────────────────────────────────────────────

def create_key_pair():
    try:
        ec2_client.delete_key_pair(KeyName=KEY_NAME)
        if os.path.exists(PEM_PATH):
            os.remove(PEM_PATH)
        print("  Deleted old key pair")
    except Exception:
        pass
    kp = ec2_client.create_key_pair(KeyName=KEY_NAME)
    with open(PEM_PATH, "w") as f:
        f.write(kp["KeyMaterial"])
    os.chmod(PEM_PATH, 0o600)
    print(f"  Key pair saved -> {PEM_PATH}")


def create_security_group():
    try:
        existing = ec2_client.describe_security_groups(GroupNames=[SG_NAME])
        sg_id = existing["SecurityGroups"][0]["GroupId"]
        print(f"  Reusing security group: {sg_id}")
        return sg_id
    except Exception:
        pass
    sg    = ec2_client.create_security_group(
        GroupName=SG_NAME,
        Description="Classifier: SSH + BE:8000 + FE:8501",
    )
    sg_id = sg["GroupId"]
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22,   "ToPort": 22,   "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 8501, "ToPort": 8501, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        ],
    )
    print(f"  Security group created: {sg_id}  (ports 22, 8000, 8501)")
    return sg_id


def launch_instance(sg_id):
    instances = ec2.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        MinCount=1, MaxCount=1,
        UserData=MINIMAL_USER_DATA,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "sentiment-classifier"}],
        }],
    )
    instance = instances[0]
    print(f"  Instance launched: {instance.id}")
    print("  Waiting for instance to start (~30s)...")
    instance.wait_until_running()
    instance.reload()
    ip = instance.public_ip_address
    print(f"  Instance running: {ip}")
    return instance, ip


# ── Phase 2: Deploy via SSH/SCP ───────────────────────────────────────────────

def ssh(ip, cmd, timeout=120):
    """Run a command on the remote instance via SSH."""
    full_cmd = [
        "ssh", "-i", PEM_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"ubuntu@{ip}", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}")
    return result.stdout.strip()


def scp(ip, local_path, remote_path):
    """Copy a file to the remote instance via SCP."""
    cmd = [
        "scp", "-i", PEM_PATH,
        "-o", "StrictHostKeyChecking=no",
        local_path, f"ubuntu@{ip}:{remote_path}"
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def wait_for_ssh(ip, max_wait=180):
    """Poll until SSH is accepting connections."""
    print("  Waiting for SSH to be ready...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            result = subprocess.run(
                ["ssh", "-i", PEM_PATH, "-o", "StrictHostKeyChecking=no",
                 "-o", "ConnectTimeout=5", f"ubuntu@{ip}", "echo ok"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("  SSH is ready!")
                return True
        except Exception:
            pass
        time.sleep(8)
    raise TimeoutError("SSH never became ready")


def deploy_files(ip):
    """SCP all project files to the instance."""
    print("  Copying project files...")
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
        scp(ip, os.path.join(BASE, local_rel), remote)
        print(f"    Copied {local_rel}")

    # Write .env with the Groq key
    env_content = f"GROQ_API_KEY={GROQ_API_KEY}\nGROQ_MODEL=llama-3.1-8b-instant\n"
    env_path = os.path.join(os.path.dirname(__file__), "_tmp.env")
    with open(env_path, "w") as f:
        f.write(env_content)
    scp(ip, env_path, "/home/ubuntu/classifier/BE/.env")
    os.remove(env_path)
    print("    Copied .env")


def install_and_start(ip):
    """Install deps and register systemd services."""
    print("  Installing dependencies (this takes ~2 min)...")

    ssh(ip, (
        "cd /home/ubuntu/classifier/BE && "
        "python3 -m venv venv && "
        "source venv/bin/activate && "
        "pip install -q -r requirements.txt && "
        "deactivate"
    ), timeout=300)
    print("    BE deps installed")

    ssh(ip, (
        "cd /home/ubuntu/classifier/FE && "
        "python3 -m venv venv && "
        "source venv/bin/activate && "
        "pip install -q -r requirements.txt && "
        "deactivate"
    ), timeout=300)
    print("    FE deps installed")

    # Write systemd service files
    be_service = """[Unit]
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
WantedBy=multi-user.target"""

    fe_service = """[Unit]
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
WantedBy=multi-user.target"""

    # Write service files via echo
    ssh(ip, f"echo '{be_service}' | sudo tee /etc/systemd/system/classifier-be.service > /dev/null")
    ssh(ip, f"echo '{fe_service}' | sudo tee /etc/systemd/system/classifier-fe.service > /dev/null")

    ssh(ip, "sudo systemctl daemon-reload && sudo systemctl enable classifier-be classifier-fe && sudo systemctl start classifier-be classifier-fe")
    print("    Services started")


def verify(ip):
    """Hit the health endpoint to confirm the BE is up."""
    print("  Verifying backend health...")
    time.sleep(8)
    result = ssh(ip, "curl -s http://localhost:8000/health")
    print(f"    Health response: {result}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Sentiment Classifier -- EC2 Deployment")
    print("=" * 60)

    create_key_pair()
    sg_id              = create_security_group()
    instance, public_ip = launch_instance(sg_id)

    # Wait extra 20s for OS to fully boot before SSH
    print("  Giving OS 20s to fully boot...")
    time.sleep(20)

    wait_for_ssh(public_ip)
    deploy_files(public_ip)
    install_and_start(public_ip)
    verify(public_ip)

    print()
    print("=" * 60)
    print("  DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"  Frontend  :  http://{public_ip}:8501")
    print(f"  Backend   :  http://{public_ip}:8000")
    print(f"  API Docs  :  http://{public_ip}:8000/docs")
    print()
    print(f"  SSH       :  ssh -i {PEM_PATH} ubuntu@{public_ip}")
    print("=" * 60)
