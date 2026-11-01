#!/usr/bin/env bash
# Run as root inside a fresh Ubuntu WSL; follows Docker's signed apt repository.
set -euo pipefail
if [ "$(id -u)" != 0 ]; then
  echo 'Run with sudo bash docker/install_wsl_engine.sh' >&2
  exit 1
fi
if command -v docker >/dev/null; then
  echo 'Docker already exists; leave installation unchanged.'
  docker version
  exit 0
fi
. /etc/os-release
test "$ID" = ubuntu
for package in docker.io containerd runc podman-docker; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    echo "Existing $package needs review; no packages removed." >&2
    exit 1
  fi
done
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
