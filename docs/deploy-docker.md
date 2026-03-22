# Deploy a KCP Peer Node — Docker Guide

**Time:** ~10 minutes  
**Requirements:** Linux host with Docker installed, public IP or domain  
**Result:** A running KCP peer connected to the public network

---

## Prerequisites

- Linux server (Ubuntu 22.04+ recommended, 512MB RAM minimum, 1GB recommended)
- Docker Engine 24+ and Docker Compose v2
- A domain name pointing to your server (for HTTPS/SSL)
- Port 8800 open in your firewall (or any port you choose)

> **No domain yet?** You can run locally without HTTPS using `http://localhost:8800`.  
> For joining the public network, HTTPS is required.

---

## 1. Install Docker

```bash
# One-liner official install (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

Verify:
```bash
docker --version      # Docker version 24+
docker compose version # Docker Compose version v2+
```

> **DigitalOcean users:** See [deploy-digitalocean.md](deploy-digitalocean.md) for a more detailed walkthrough including Droplet creation.

---

## 2. Clone the repo

```bash
git clone https://github.com/kcp-protocol/kcp.git
cd kcp
```

---

## 3. Configure your peer

```bash
cp docker/.env.example docker/.env
nano docker/.env   # or use your preferred editor
```

Minimum configuration:

```env
KCP_NODE_ID=my-peer-name        # unique, no spaces
KCP_USER_ID=you@example.com     # your contact e-mail
KCP_TENANT_ID=community         # use "community" for public network
KCP_PORT=8800

# Where to store data on the HOST machine
# Use a path with plenty of disk space
KCP_DATA_HOST=/opt/kcp-data     # or /dados/kcp-docker/data on DigitalOcean
```

---

## 4. Start the peer

```bash
cd docker
docker compose up -d
```

Expected output:
```
[+] Running 1/1
 ✔ Container kcp-peer  Started
```

---

## 5. Verify the peer is running

```bash
curl http://localhost:8800/kcp/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "node_id": "...",
  "artifacts": 0,
  "peers": 7,
  "kcp_version": "0.2.0"
}
```

Check logs:
```bash
docker compose logs -f kcp-peer
```

---

## 6. Set up HTTPS with Let's Encrypt

HTTPS is required to join the public network.

### Option A — Nginx on the host (recommended)

```bash
# Install nginx + certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d mypeer.example.com

# Create nginx config
sudo tee /etc/nginx/sites-available/kcp-peer <<'EOF'
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

    location / {
        proxy_pass http://127.0.0.1:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/kcp-peer /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Option B — Nginx in Docker (bundled)

```bash
# Edit docker/nginx.conf — replace KCP_DOMAIN with your domain
sed -i 's/KCP_DOMAIN/mypeer.example.com/g' docker/nginx.conf

# Start with proxy profile
docker compose --profile proxy up -d
```

Verify HTTPS:
```bash
curl https://mypeer.example.com/kcp/v1/health
```

---

## 7. Publish a test artifact

```bash
curl -s https://mypeer.example.com/kcp/v1/artifacts \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Hello from my peer",
    "content": "First artifact published from my KCP node.",
    "tags": ["test", "hello"],
    "visibility": "public"
  }' | python3 -m json.tool
```

You should see an artifact with an `id`, `signature`, and `content_hash` — cryptographically signed by your node.

---

## 8. Join the public network

Once your peer is online and reachable via HTTPS:

1. Fork [github.com/kcp-protocol/kcp](https://github.com/kcp-protocol/kcp)
2. Edit `docs/peers.json` — add your peer entry:

```json
{
  "node_id": "your-node-uuid-from-health-endpoint",
  "url": "https://mypeer.example.com",
  "name": "My KCP Peer",
  "region": "Europe",
  "operator": "your-github-handle",
  "health_url": "https://mypeer.example.com/kcp/v1/health",
  "peers_url": "https://mypeer.example.com/kcp/v1/peers",
  "status": "live"
}
```

3. Open a Pull Request with the title: `feat(peers): add mypeer — Region`
4. The CI will automatically health-check your peer
5. Once CI passes, a maintainer merges the PR
6. Your peer appears on [kcp-protocol.org/status.html](https://kcp-protocol.org/status.html) within 5 minutes

See [PEER_SUBMISSION.md](../.github/PEER_SUBMISSION.md) for the full submission checklist.

---

## Useful commands

```bash
# Start peer
docker compose up -d

# Stop peer
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart

# Update to latest version
git pull
docker compose build
docker compose up -d

# Check artifact count
curl -s http://localhost:8800/kcp/v1/health | python3 -m json.tool

# Open web dashboard
open http://localhost:8800/ui
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | `docker compose logs kcp-peer` — check for port conflicts |
| Health returns 502 | Nginx proxy not reaching container — check port mapping |
| "address already in use" | Another process on port 8800 — change `KCP_PORT` in `.env` |
| SQLite permission error | Check that `KCP_DATA_HOST` dir is writable |
| Peers count = 0 | Normal on first start — peer discovery runs on background |

---

## Hardware requirements

| Setup | RAM | CPU | Disk |
|-------|-----|-----|------|
| Minimal (solo dev) | 256 MB | 1 vCPU | 1 GB |
| Community peer | 512 MB | 1 vCPU | 10 GB |
| Active hub | 1 GB | 2 vCPU | 50 GB |

---

## Related docs

- [Deploy on DigitalOcean](deploy-digitalocean.md)
- [RFC KCP-004 — Network Deployment Models](../rfcs/kcp-004-network-models.md)
- [Peer Submission Guide](../.github/PEER_SUBMISSION.md)
- [KCP Protocol Specification](../SPEC.md)
