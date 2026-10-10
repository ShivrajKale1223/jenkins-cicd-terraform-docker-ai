#!/bin/bash
# EC2 user_data: runs once, as root, on first boot (Amazon Linux 2023, t3.micro)
# Logs: /var/log/cloud-init-output.log

# ---------- 1. Swap (t3.micro has only 1 GB RAM) ----------
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# ---------- 2. Base packages (critical: stop if these fail) ----------
set -e
dnf update -y
dnf install -y docker git java-21-amazon-corretto   # current Jenkins needs Java 21
systemctl enable --now docker

# ---------- 3. Jenkins ----------
wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io-2023.key
dnf install -y jenkins

# Jenkins must be able to run docker
usermod -aG docker jenkins

# Use the real disk for temp files (/tmp on a 1 GB instance is tiny and takes the node offline)
mkdir -p /var/lib/jenkins/tmp
chown jenkins:jenkins /var/lib/jenkins/tmp
mkdir -p /etc/systemd/system/jenkins.service.d
cat > /etc/systemd/system/jenkins.service.d/override.conf <<'CONF'
[Service]
Environment="JAVA_OPTS=-Djava.awt.headless=true -Djava.io.tmpdir=/var/lib/jenkins/tmp"
CONF
systemctl daemon-reload

# Start Jenkins BEFORE the optional tools, so a later failure can never block it
systemctl enable --now jenkins

# ---------- 4. Optional tools (a failure here must not stop the server) ----------
set +e
# Trivy: use the official install script instead of a hard-coded version URL
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin || true

echo "install-jenkins.sh finished"