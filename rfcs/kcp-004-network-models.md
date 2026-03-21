# RFC KCP-004: Network Deployment Models

**Status:** Draft  
**Created:** March 2026  
**Author:** KCP Protocol Working Group  
**Supersedes:** Sections 3.1–3.3 of ARCHITECTURE.md

---

## Abstract

KCP is a protocol, not a hosted service. This RFC defines the canonical deployment models
for KCP networks — from a single developer's laptop to a global federated mesh — and
establishes the economic and governance principles that allow the public network to grow
without requiring centralized funding or a single operator to bear the cost.

The core insight: **the public KCP network should follow the same model as the internet
itself** — no single entity owns or funds it; every participant runs their own node for
their own benefit, and the network emerges from that self-interest.

---

## 1. The Problem with "We Run the Network"

The KCP project currently operates 3 public peers (peer04, peer05, peer07) as a
proof-of-concept. This is the right move for the MVP phase. However, it creates a
dangerous dependency:

- **Financial**: every peer costs money every month, indefinitely
- **Operational**: the project becomes a hosting provider, not a protocol
- **Trust**: a network run by one entity is not a decentralized network
- **Scaling**: 3 → 10 → 100 peers cannot be self-funded by a single team

The long-term goal is for the KCP project to **run zero peers in production**. The
peers we run today exist to validate the protocol. The protocol's success will be
measured by how many peers other people choose to run.

---

## 2. Deployment Models

KCP defines four canonical deployment models. They are not mutually exclusive —
an organization can run a private hub internally while also connecting to the public
federated mesh.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KCP Deployment Models                          │
├──────────────┬─────────────────┬──────────────────┬───────────────────┤
│  Mode 1      │  Mode 2         │  Mode 3          │  Mode 4           │
│  Local       │  Private Hub    │  Community Peer  │  Federated Mesh   │
├──────────────┼─────────────────┼──────────────────┼───────────────────┤
│ SQLite on    │ Self-hosted     │ Operator runs a  │ Hubs and peers    │
│ developer   │ server inside   │ public node for  │ from different    │
│ machine.     │ org firewall.   │ their community. │ orgs sync via     │
│              │                 │                  │ mTLS.             │
│ No network.  │ No public       │ Open to anyone   │                   │
│ No peers.    │ exposure.       │ who respects ToS.│ Hub-to-hub ACL.   │
│              │                 │                  │                   │
│ Who pays:    │ Who pays:       │ Who pays:        │ Who pays:         │
│ Nobody.      │ The company.    │ The operator.    │ Each participant  │
│ (local disk) │ (internal IT)   │ (voluntary/paid) │ pays for itself.  │
└──────────────┴─────────────────┴──────────────────┴───────────────────┘
```

### 2.1 Mode 1 — Local (Embedded)

The SDK runs in-process. No server, no network, no configuration. All data lives
in a local SQLite file.

**Use case:** Individual developer, AI assistant (Claude/Cursor), single-user workflow.

**Infrastructure cost:** Zero. Runs on the developer's own machine.

**Who runs it:** Anyone. The SDK ships with this as the default mode.

---

### 2.2 Mode 2 — Private Hub

An organization deploys a KCP node (or hub server) inside their own infrastructure.
All knowledge artifacts stay within the organization's perimeter. Sync between
employees happens through this central node.

**Use case:** Enterprise team, agency, consulting firm, research lab.

**Infrastructure cost:** One server (VPS, container, on-prem). Equivalent to running
any internal API. The organization owns and pays for this, like they would for any
internal tool.

**Who runs it:** The organization's IT or platform team. Not the KCP project.

**Key property:** This is **fully private**. No artifact ever leaves the organization's
network unless explicitly configured. The organization controls encryption keys,
access control, and data retention.

---

### 2.3 Mode 3 — Community Peer (Public Node)

A person or organization runs a public KCP node and opens it to the community.
This is analogous to running a public DNS resolver, a Tor exit node, a Mastodon
instance, or a BitTorrent tracker.

**Use case:** Developer community, open-source project, university, research group,
cloud provider offering KCP as a feature.

**Infrastructure cost:** Borne by the operator. The KCP project provides the software
and the specification but does not subsidize the server.

**Why would someone do this?**

- **Developers**: run their own node for control + contribute to the network
- **Companies**: offer "KCP hosting" as a product or feature (like email hosting)
- **Universities**: host a node for their research community
- **Cloud providers**: integrate KCP as a managed service
- **Open-source projects**: host a node for their community's shared knowledge

**Incentive structure:** Operators gain:
1. A node under their control (not dependent on any central party)
2. Access to all public artifacts from the federated mesh
3. Reputation as a reliable network participant
4. Potential to offer paid services on top (private namespaces, storage quotas, etc.)

---

### 2.4 Mode 4 — Federated Mesh

Multiple hubs and community peers establish bilateral or multilateral sync
agreements. Each hub decides which peers to sync with and what to share
(controlled by ACL policies).

**Use case:** Cross-organization knowledge sharing, research consortia,
multi-tenant SaaS platforms.

**Infrastructure cost:** Each participant pays for their own node. Sync is
peer-to-peer; there is no central broker.

**Key property:** This is the **end state** of the KCP network. No central server.
No single point of failure or funding. Every participant is a node. The network
is the sum of its participants.

---

## 3. The Public Network: Who Runs It?

The KCP public network is not a service provided by the KCP project.
It is a **voluntary mesh** of nodes operated by community members who choose to
run a public peer. The KCP project's role is to:

1. **Define the protocol** (this spec and the related RFCs)
2. **Ship the reference implementation** (SDK + node software)
3. **Maintain the bootstrap registry** (peers.json — a list of known public peers)
4. **Run reference nodes** during early phases to validate the protocol

Point 4 is explicitly **temporary**. The reference nodes (peer04, peer05, peer07)
exist to prove the protocol works in production. As community peers appear, the
KCP project should decommission or repurpose its own nodes.

### 3.1 The peers.json Bootstrap Registry

`peers.json` (served at `kcp-protocol.org/peers.json`) is the canonical bootstrap
list. It is a **curated list of well-known public peers**, not an exhaustive index.

Any peer can submit a pull request to be listed. To be listed, a peer must:

- Run a publicly accessible KCP node
- Maintain >95% uptime over 30 days (verified by automated health checks)
- Respect the KCP Public Network Terms (no spam, no illegal content, GDPR-compliant)
- Accept responsibility for the artifacts published through their node

**Critical**: the bootstrap list is a starting point, not a dependency. After first
contact with any peer, a node discovers the rest of the network via gossip. A node
does not need `peers.json` to function — it only needs one known peer URL.

### 3.2 Governance of the Public Network

The public network has no central authority. There is no one who can delete an
artifact from all nodes simultaneously or force all nodes to follow a rule.
This is intentional.

What exists:
- **The protocol spec**: defines what a valid KCP artifact is
- **The bootstrap registry**: lists community-trusted starting points
- **ACL**: each artifact's visibility is controlled by its publisher
- **Node operator ToS**: each operator defines their own rules for their node

This model is analogous to the web: there is no one who controls all websites,
but there are standards (HTTP, HTML), a bootstrap list of well-known domains
(DNS), and individual site operators who set their own rules.

---

## 4. The Private Network: Fully Self-Contained

A private KCP network is a closed set of nodes that sync only with each other.
It does not connect to the public federated mesh unless explicitly configured.

```
┌─────────────────────────────────────────────────────────┐
│                  Acme Corp Private Network              │
│                                                         │
│   ┌──────────┐     sync      ┌──────────┐              │
│   │ KCP Hub  │◄─────────────►│ KCP Node │              │
│   │ (HQ)     │               │ (NY)     │              │
│   └──────────┘               └──────────┘              │
│        ▲                          ▲                     │
│        │ sync                     │ sync                │
│        ▼                          ▼                     │
│   ┌──────────┐               ┌──────────┐              │
│   │ KCP Node │               │ KCP Node │              │
│   │ (London) │               │ (SP)     │              │
│   └──────────┘               └──────────┘              │
│                                                         │
│  All nodes on Acme infrastructure.                      │
│  Zero KCP project involvement.                          │
│  Zero dependency on public peers.                       │
└─────────────────────────────────────────────────────────┘
```

**Key properties of a private network:**
- All nodes managed by the organization
- All data encrypted and within organizational control
- No public network access required
- The organization defines its own peer discovery (static list or internal DNS)
- Can optionally connect to specific public peers for specific use cases
  (e.g., publish certain artifacts publicly while keeping others private)

**Deployment options:**
- Single server with multiple node instances (current proof-of-concept)
- Kubernetes cluster with one pod per logical peer
- One server per geographic region (recommended for production)
- Serverless / containerized via any cloud provider

---

## 5. Network Topology Decision Tree

```
Are your artifacts sensitive / internal-only?
├── YES → Mode 2 (Private Hub) or Mode 4 (Federated, internal only)
│         You own the infra. KCP project not involved.
│
└── NO → Do you want to contribute to the public network?
         ├── YES → Mode 3 (Community Peer)
         │         You run a node. Others can sync with you.
         │
         └── NO → Do you need to share with others at all?
                  ├── YES → Use Mode 3 or Mode 4 with a trusted peer
                  └── NO  → Mode 1 (Local). Zero infrastructure needed.
```

---

## 6. Sustainability Model

### 6.1 The KCP Project's Costs

The KCP project needs to fund only:

| Item | Cost model |
|------|-----------|
| GitHub repository (code, docs, spec) | Free (GitHub) |
| `kcp-protocol.org` domain | ~$15/year |
| Bootstrap registry (`peers.json`) | Free (GitHub Pages) |
| Reference nodes (peer04/05/07) | **Temporary** — transitioning to community-operated |
| CI/CD (tests, builds) | Free (GitHub Actions) |

The goal is for the project's infrastructure cost to approach **zero** as the
community operates its own peers.

### 6.2 Community Peer Operators' Costs

A minimal public KCP peer:

| Configuration | Monthly cost |
|--------------|-------------|
| 1 vCPU, 1GB RAM, 25GB SSD | ~$5–6/month on any cloud provider |
| 2 vCPU, 2GB RAM, 50GB SSD | ~$10–12/month |
| Dedicated bare-metal | $20–50/month |

SSL certificates: free via Let's Encrypt.  
Software: free (MIT license).

A community peer is **cheaper than a Netflix subscription**. The barrier to entry
for an operator is intentionally low.

### 6.3 Commercial Operators

The protocol is open and the software is MIT-licensed. Any company can:

- Offer **KCP hosting** as a service (like email hosting or Git hosting)
- Add proprietary features on top (advanced search, analytics, SLA guarantees)
- Charge for private namespaces, increased storage, or enterprise support
- Integrate KCP into their own AI products

This is the same model as Linux (free OS, Red Hat charges for support),
PostgreSQL (free database, AWS/RDS charges for managed service), or
Matrix/Element (open protocol, commercial hosting).

**The KCP project does not compete with commercial operators.** We maintain
the specification and the reference implementation. Others build the business.

---

## 7. Phase Transition Plan

### Current (Phase 2 — Proof of Concept)
- KCP project runs 3 reference peers (peer04/05/07)
- These prove the protocol works in production
- All on a single host for cost efficiency

### Phase 3 — Community Seeding
- KCP project provides a **one-click deploy** guide for community peers
  (Docker Compose, DigitalOcean 1-Click, Railway, Render, Fly.io)
- First external operators join and get listed in `peers.json`
- KCP project continues running reference peers for stability

### Phase 4 — Protocol Maturity
- 10+ independent community peers operational
- Reference peers decommissioned or repurposed as test nodes
- `peers.json` maintained as community registry (PRs from operators)
- KCP project's infrastructure cost: domain + CI only

### Phase 5 — Ecosystem
- Commercial operators offering managed KCP hosting
- Enterprise deployments of Mode 2 private hubs
- The protocol running on infrastructure we do not control, pay for, or operate
- **This is success**: the protocol is bigger than the project

---

## 8. What This Means for the Roadmap

| Deliverable | Purpose | Who builds |
|-------------|---------|-----------|
| One-click deploy guide (Docker/Compose) | Lower barrier for community operators | KCP project |
| Operator documentation (hardware, config, ToS template) | Enable community peers | KCP project |
| `peers.json` submission process (GitHub PR + automated health check) | Grow the registry | KCP project |
| Commercial hosting guide (how to monetize a KCP node) | Enable ecosystem | KCP project |
| Private hub deployment guide (enterprise Mode 2) | Enable enterprise adoption | KCP project |
| The actual hosting of community peers | **Not KCP project responsibility** | Community |
| The actual hosting of private hubs | **Not KCP project responsibility** | Enterprises |

---

## 9. Summary

| Question | Answer |
|----------|--------|
| Who pays for the public network? | Each operator pays for their own node |
| Who controls the public network? | Nobody — it's a voluntary mesh |
| Who pays for a private network? | The organization that uses it |
| Does the KCP project need to run peers forever? | No — only during early phases |
| Can someone build a business on KCP? | Yes — the protocol is MIT-licensed |
| What does the KCP project actually own? | The spec, the reference implementation, and the bootstrap registry |
| What happens if the KCP project disappears? | The protocol continues. Anyone can fork the spec and the software. |

---

*This RFC defines the network models and sustainability principles for the KCP protocol.
Implementation details for each mode are covered in ARCHITECTURE.md and the respective
deployment guides.*
