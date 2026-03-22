# KCP Peer Submission Guide

Thank you for running a KCP peer! This document explains how to register your peer in the official `peers.json` registry so it appears on the public network.

---

## Prerequisites checklist

Before submitting, verify that your peer meets all requirements:

- [ ] Peer is running and publicly accessible via HTTPS
- [ ] Domain has a valid TLS certificate (Let's Encrypt is fine)
- [ ] `GET https://your-peer.example.com/kcp/v1/health` returns HTTP 200
- [ ] Health response includes `status: "ok"` and `kcp_version`
- [ ] Port 443 is open and reachable from the internet
- [ ] Your peer has been stable for at least 24 hours

Verify all of the above:
```bash
curl -s https://your-peer.example.com/kcp/v1/health | python3 -m json.tool
```

Expected response:
```json
{
  "status": "ok",
  "node_id": "your-uuid-here",
  "kcp_version": "0.2.0",
  "artifacts": 0,
  "peers": 7
}
```

---

## How to submit

### 1. Fork the repository

Click **Fork** on [github.com/kcp-protocol/kcp](https://github.com/kcp-protocol/kcp).

### 2. Create a branch

```bash
git clone https://github.com/YOUR_USERNAME/kcp.git
cd kcp
git checkout -b add-peer/my-peer-name
```

### 3. Add your peer to `docs/peers.json`

Open `docs/peers.json` and add your entry to the `"peers"` array:

```json
{
  "node_id": "YOUR-NODE-UUID",
  "url": "https://your-peer.example.com",
  "name": "My KCP Peer",
  "region": "Europe",
  "operator": "your-github-handle",
  "health_url": "https://your-peer.example.com/kcp/v1/health",
  "peers_url": "https://your-peer.example.com/kcp/v1/peers",
  "status": "live"
}
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `node_id` | ✅ | UUID from `/kcp/v1/health` — must be unique |
| `url` | ✅ | Base URL of your peer (HTTPS, no trailing slash) |
| `name` | ✅ | Human-readable name (max 50 chars) |
| `region` | ✅ | One of: `North America`, `South America`, `Europe`, `Asia`, `Africa`, `Oceania` |
| `operator` | ❌ | Your GitHub handle or organization name |
| `health_url` | ✅ | Full URL to health endpoint |
| `peers_url` | ✅ | Full URL to peers endpoint |
| `status` | ✅ | Must be `"live"` |

> **Get your `node_id`:**
> ```bash
> curl -s https://your-peer.example.com/kcp/v1/health | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])"
> ```

### 4. Commit and push

```bash
git add docs/peers.json
git commit -m "feat(peers): add my-peer-name — Region"
git push origin add-peer/my-peer-name
```

### 5. Open a Pull Request

- Go to your fork on GitHub
- Click **Compare & pull request**
- Title: `feat(peers): add my-peer-name — Region`
- Body: describe your peer (location, purpose, etc.) — optional but appreciated

### 6. Wait for CI

The GitHub Actions CI will automatically:
1. Detect the new/modified entry in `docs/peers.json`
2. Call `GET <health_url>` from GitHub's infrastructure
3. Validate the response matches the expected schema
4. Comment the result on your PR ✅ or ❌

### 7. Merge

Once CI passes, a maintainer will review and merge. Your peer will appear on [kcp-protocol.org/status.html](https://kcp-protocol.org/status.html) within 5 minutes.

---

## After your PR is merged

- Your peer is discoverable by all KCP nodes that bootstrap from `peers.json`
- It appears on the public status page
- Other peers may sync artifacts to/from yours (if ACL allows)

---

## Removal

If you need to take your peer offline:

1. Open a PR changing your entry's `status` to `"offline"`
2. Or open an issue and a maintainer will update it

Peers that fail health checks for **7 consecutive days** are automatically moved to `status: "offline"` by the CI monitoring job.

---

## Questions?

Open an issue at [github.com/kcp-protocol/kcp/issues](https://github.com/kcp-protocol/kcp/issues) with the label `peer-submission`.
