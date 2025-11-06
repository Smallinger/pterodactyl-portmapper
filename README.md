# 🚀 Pterodactyl Port Mapper for OPNsense

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/Smallinger/pterodactyl-portmapper/pkgs/container/pterodactyl-portmapper)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Automatically synchronize port forwarding between **Pterodactyl Panel** and **OPNsense Firewall**. No manual NAT rule management needed!

## ✨ Features

- ✅ Automatic sync every 60 seconds
- ✅ Bulk updates (no port loss)
- ✅ Protected ports (SSH, HTTP, etc.)
- ✅ Auto cleanup of orphaned ports
- ✅ Docker ready with pre-built images

---

## 🚀 Quick Start

### Option 1: Pre-built Docker Image (Recommended)

```bash
# 1. Create .env file
cat > .env << 'EOF'
PTERODACTYL_PANEL_URL=https://your-panel.com
PTERODACTYL_API_KEY=ptla_your_api_key
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your_opnsense_key
OPNSENSE_API_SECRET=your_opnsense_secret
ALIAS_NAME=pterodactyl_ports
EXCLUDED_PORTS=22,80,443,3306,5432,6379,8006,9090
EOF

# 2. Download and start
curl -O https://raw.githubusercontent.com/Smallinger/pterodactyl-portmapper/main/docker-compose.ghcr.yml
docker-compose -f docker-compose.ghcr.yml up -d

# 3. View logs
docker-compose -f docker-compose.ghcr.yml logs -f
```

### Option 2: Build from Source

```bash
# 1. Clone and configure
git clone https://github.com/Smallinger/pterodactyl-portmapper.git
cd pterodactyl-portmapper
cp .env.example .env
nano .env  # Edit with your credentials

# 2. Start
docker-compose up -d

# 3. View logs
docker-compose logs -f
```

---

## ⚙️ Configuration

Edit your `.env` file:

```bash
# Pterodactyl
PTERODACTYL_PANEL_URL=https://panel.example.com
PTERODACTYL_API_KEY=ptla_your_key_here

# OPNsense
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your_key
OPNSENSE_API_SECRET=your_secret
OPNSENSE_VERIFY_SSL=false

# Settings
ALIAS_NAME=pterodactyl_ports
SYNC_INTERVAL=60
EXCLUDED_PORTS=22,80,443,3306,5432,6379,8006,9090
```

---

## 🔐 OPNsense Setup

### 1. Create API Keys
- **System → Access → Users** → Your user → **API keys** → Click **"+"**
- Copy **API Key** and **API Secret** to `.env`

### 2. Create Alias
- **Firewall → Aliases** → Click **"+"**
- **Name:** `pterodactyl_ports`
- **Type:** `Port(s)`
- **Content:** (leave empty)
- Click **Save** → **Apply**

### 3. Create NAT Rule
- **Firewall → NAT → Port Forward** → Click **"+"**

| Field | Value |
|-------|-------|
| **Interface** | WAN |
| **Protocol** | TCP |
| **Destination** | WAN address |
| **Destination Port** | `pterodactyl_ports` (alias) |
| **Redirect Target IP** | Your Pterodactyl host IP |
| **Redirect Target Port** | `pterodactyl_ports` (alias) |

- Click **Save** → **Apply changes**

✅ Done! The script will now auto-manage ports.

---

##  Troubleshooting

| Problem | Solution |
|---------|----------|
| "Alias not found" | Check alias name matches `ALIAS_NAME` in `.env` |
| "401 Unauthorized" | Verify API credentials |
| "SSL Error" | Set `OPNSENSE_VERIFY_SSL=false` |
| Ports not forwarding | Verify NAT rule uses alias for both destination and target |

**View logs:**
```bash
docker-compose -f docker-compose.ghcr.yml logs -f
```

---

## � Security

**Protected ports** (never forwarded):
`22` (SSH), `80` (HTTP), `443` (HTTPS), `3306` (MySQL), `5432` (PostgreSQL), `6379` (Redis), `8006` (Proxmox), `9090` (Management)

**Customize:** Edit `EXCLUDED_PORTS` in `.env`

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 💖 Support

- ⭐ **Star this repo** if you find it useful!
- � **Issues:** [GitHub Issues](https://github.com/Smallinger/pterodactyl-portmapper/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Smallinger/pterodactyl-portmapper/discussions)

### Support My Work

If you like what I do, consider supporting me:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/smallpox)

---

Made with ❤️ for the Pterodactyl and OPNsense community
1. Check the logs
2. Review OPNsense API documentation
3. Create an issue in the repository

## 🎯 Roadmap

- [ ] Web UI for monitoring
- [ ] Prometheus metrics export
- [ ] Multi-firewall support
- [ ] Port range support
- [ ] UDP protocol support
