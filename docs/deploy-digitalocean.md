# Deploy a KCP Peer Node on DigitalOcean

**Time:** ~15 minutes  
**Cost:** ~$6/month (Basic Droplet, 1 GB RAM)  
**Result:** A production KCP peer with HTTPS, auto-restart, and Let's Encrypt SSL

---

## Overview

DigitalOcean Droplets are the simplest way to run a persistent KCP peer. This guide walks you through the entire process: creating the Droplet, installing Docker, launching the peer, and registering it in the public network.

---

## Step 1 — Create a Droplet

In the DigitalOcean dashboard:

1. **Create → Droplets**
2. **Region:** Choose the closest to your users (or any region for community peer)
3. **Image:** `Ubuntu 24.04 LTS x64`
4. **Size:** `Basic → 1 GB / 1 vCPU / 25 GB SSD` (~$6/month)
   - 512 MB works for a light peer, 1 GB is recommended for comfort
5. **Authentication:** Add your SSH key (or create one)
6. **Hostname:** e.g., `kcp-peer`
7. Click **Create Droplet**

Note your Droplet's **public IP** — you'll need it to configure DNS.

---

## Step 2 — Point a domain to your Droplet

In your DNS provider (DigitalOcean DNS, Cloudflare, etc.):

```
A    mypeer.example.com    →    <DROPLET_IP>
```

Wait a few minutes for DNS propagation:
```bash
dig +short mypeer.example.com
# Should return your Droplet IP
```

---

## Step 3 — Connect and bootstrap

```bash
ssh root@<DROPLET_IP>

# Create a dedicated user (optional but recommended)
adduser kcp
usermod -aG sudo kcp
su - kcp
```

---

## Step 4 — Install Docker

```bash
# Official one-liner
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### Configure Docker to use /dados (if you have a separate volume)

If your Droplet has a mounted volume at `/dados` (more disk space):

```bash
# Stop Docker first
sudo systemctl stop docker

# Configure data-root
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "data-root": "/dados/docker"
}
EOF

sudo mkdir -p /dados/docker
sudo systemctl start docker
docker info | grep "Docker Root Dir"
# Should show: Docker Root Dir: /dados/docker
```

---

## Step 5 — Clone and configure the peer

```bash
# Clone to /dados for more disk space (or ~ if no separate volume)
cd /dados
git clone https://github.com/kcp-protocol/kcp.git
cd kcp

# Configure
cp docker/.env.example docker/.env
nano docker/.env
```

Edit these values in `.env`:

```env
KCP_NODE_ID=my-peer-name          # unique identifier, e.g. "alice-do-nyc"
KCP_USER_ID=you@example.com       # your e-mail
KCP_TENANT_ID=community
KCP_PORT=8800
KCP_DATA_HOST=/dados/kcp-data     # use /dados for more disk space
```

---

## Step 6 — Open the firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Let's Encrypt challenge)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

> You do **not** need to open port 8800 publicly — nginx will proxy to it internally.

---

## Step 7 — Start the peer

```bash
cd /dados/kcp/docker
docker compose up -d

# Verify it's running
curl http://localhost:8800/kcp/v1/health
```

---

## Step 8 — Install nginx and obtain SSL certificate

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d mypeer.example.com --non-interactive --agree-tos -m you@example.com
```

Create the nginx site config:

```bash
sudo tee /etc/nginx/sites-available/kcp-peer <<'NGINX'
server {
    listen 80;
    server_name mypeer.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mypeer.example.com;

    ssl_certificate     /etc/letsencrypt/live/mypeer.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mypeer.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Rate limiting — protect against abuse
    limit_req_zone $binary_remote_addr zone=kcp_write:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=kcp_read:10m rate=60r/m;

    location /kcp/v1/artifacts {
        limit_req zone=kcp_write burst=20 nodelay;
        proxy_pass http://127.0.0.1:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        limit_req zone=kcp_read burst=30 nodelay;
        proxy_pass http://127.0.0.1:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
    }
}
NGINX

sudo ln -s /etc/nginx/sites-available/kcp-peer /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Verify HTTPS:
```bash
curl https://mypeer.example.com/kcp/v1/health
# Should return {"status":"ok",...}
```

---

## Step 9 — Enable auto-restart on reboot

Docker containers with `restart: unless-stopped` (set in `docker-compose.yml`) restart automatically after a reboot.

Test it:
```bash
sudo reboot
# After ~30 seconds:
ssh user@<DROPLET_IP>
curl http://localhost:8800/kcp/v1/health
```

---

## Step 10 — Publish a test artifact

```bash
curl -s https://mypeer.example.com/kcp/v1/artifacts \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Hello from my DigitalOcean peer",
    "content": "KCP peer running on DigitalOcean.",
    "tags": ["test", "digitalocean"],
    "visibility": "public"
  }' | python3 -m json.tool
```

---

## Step 11 — Register in the public network

Get your node's UUID from the health endpoint:
```bash
curl -s https://mypeer.example.com/kcp/v1/health | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])"
```

Then open a PR to add your peer — see [PEER_SUBMISSION.md](../.github/PEER_SUBMISSION.md).

---

## Maintenance

### Update to a new KCP version

```bash
cd /dados/kcp
git pull
cd docker
docker compose build --no-cache
docker compose up -d
```

### View logs

```bash
docker compose logs -f kcp-peer
# Or via journald:
sudo journalctl -u docker -f
```

### Monitor disk usage

```bash
df -h /dados
docker system df
```

### Renew SSL certificate (automatic)

Certbot installs a systemd timer that renews automatically. To check:
```bash
sudo certbot renew --dry-run
```

---

## Cost estimate

| Resource | Monthly cost |
|----------|-------------|
| Droplet (1 GB / 1 vCPU) | ~$6 |
| Bandwidth (1 TB included) | $0 |
| Optional: Volume 10 GB | ~$1 |
| **Total** | **~$6–7/month** |

---

## Related docs

- [Generic Docker Deploy Guide](deploy-docker.md)
- [RFC KCP-004 — Network Deployment Models](../rfcs/kcp-004-network-models.md)
- [Peer Submission Guide](../.github/PEER_SUBMISSION.md)
