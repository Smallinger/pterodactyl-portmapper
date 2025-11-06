# 🚀 Pterodactyl Port Mapper for OPNsense

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/Smallinger/pterodactyl-portmapper/pkgs/container/pterodactyl-portmapper)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Automatically synchronize port forwarding between **Pterodactyl Panel** and **OPNsense Firewall**. No manual NAT rule management needed!

---

## 📋 Features

- ✅ **Automatic Sync** - Checks every 60 seconds for changes
- ✅ **Bulk Updates** - All ports updated at once (no port loss)
- ✅ **Smart Detection** - Only updates when changes occur
- ✅ **Port Protection** - Critical ports (SSH, HTTP, etc.) never forwarded
- ✅ **Auto Cleanup** - Removes orphaned ports automatically
- ✅ **Docker Ready** - Pre-built images available on GitHub Container Registry
- ✅ **Multi-Platform** - Supports AMD64 and ARM64 (Raspberry Pi!)

---

## 🎯 Quick Start (Docker)

**1. Create `.env` file:**
```bash
cat > .env << 'EOF'
PTERODACTYL_PANEL_URL=https://your-panel.com
PTERODACTYL_API_KEY=ptla_your_api_key
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your_opnsense_key
OPNSENSE_API_SECRET=your_opnsense_secret
ALIAS_NAME=pterodactyl_ports
EXCLUDED_PORTS=22,80,443,3306,5432,6379,8006,9090
EOF
```

**2. Download and start:**
```bash
curl -O https://raw.githubusercontent.com/Smallinger/pterodactyl-portmapper/main/docker-compose.ghcr.yml
docker-compose -f docker-compose.ghcr.yml up -d
```

**3. View logs:**
```bash
docker-compose -f docker-compose.ghcr.yml logs -f
```

✅ **Done!** Ports will sync automatically every 60 seconds.

---

## 📦 Installation Options

### Option 1: Pre-built Docker Image (Recommended 🚀)

Uses the pre-built image from GitHub Container Registry.

```bash
# Pull latest image
docker pull ghcr.io/smallinger/pterodactyl-portmapper:latest

# Create .env file (see Quick Start above)

# Run with Docker Compose
curl -O https://raw.githubusercontent.com/Smallinger/pterodactyl-portmapper/main/docker-compose.ghcr.yml
docker-compose -f docker-compose.ghcr.yml up -d

# Or run with Docker directly
docker run -d \
  --name pterodactyl-portmapper \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/smallinger/pterodactyl-portmapper:latest
```

### Option 2: Build from Source

Clone and build the image yourself.

```bash
git clone https://github.com/Smallinger/pterodactyl-portmapper.git
cd pterodactyl-portmapper
cp .env.example .env
nano .env  # Edit with your credentials
docker-compose up -d
```

### Option 3: Manual Python Installation

For development or custom deployments.

```bash
# Clone repository
git clone https://github.com/Smallinger/pterodactyl-portmapper.git
cd pterodactyl-portmapper

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python main.py
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PTERODACTYL_PANEL_URL` | ✅ | - | Your Pterodactyl Panel URL |
| `PTERODACTYL_API_KEY` | ✅ | - | Application API key (starts with `ptla_`) |
| `OPNSENSE_URL` | ✅ | - | OPNsense firewall URL |
| `OPNSENSE_API_KEY` | ✅ | - | OPNsense API key |
| `OPNSENSE_API_SECRET` | ✅ | - | OPNsense API secret |
| `ALIAS_NAME` | ✅ | `pterodactyl_ports` | Name of the OPNsense alias |
| `EXCLUDED_PORTS` | ❌ | `22,80,443,...` | Comma-separated list of protected ports |
| `SYNC_INTERVAL` | ❌ | `60` | Sync interval in seconds |
| `OPNSENSE_VERIFY_SSL` | ❌ | `false` | Verify SSL certificates |

### Example `.env` File

```bash
# Pterodactyl Configuration
PTERODACTYL_PANEL_URL=https://panel.example.com
PTERODACTYL_API_KEY=ptla_your_application_api_key_here

# OPNsense Configuration
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=rEDXpKba+fLVfNX...
OPNSENSE_API_SECRET=I4xyP5uLJ2lgDId...
OPNSENSE_VERIFY_SSL=false

# Alias Configuration
ALIAS_NAME=pterodactyl_ports
SYNC_INTERVAL=60

# Protected Ports (SSH, HTTP, HTTPS, databases, etc.)
EXCLUDED_PORTS=22,80,443,3306,5432,6379,8006,9090
```

---

## 🔐 OPNsense Setup

Before running the script, you need to configure OPNsense:

### 1️⃣ Create API Keys

1. Log into OPNsense
2. Go to **System → Access → Users**
3. Select your user or create a dedicated API user
4. Scroll to **API keys** → Click **"+"**
5. Copy the **API Key** and **API Secret**
6. Add them to your `.env` file

### 2️⃣ Create Alias

1. Go to **Firewall → Aliases**
2. Click **"+"** to add a new alias
3. Configure:
   - **Name:** `pterodactyl_ports` (must match `.env`)
   - **Type:** `Port(s)`
   - **Content:** (leave empty)
   - **Description:** `Auto-managed Pterodactyl ports`
4. Click **Save** → **Apply**

### 3️⃣ Create NAT Port Forward Rule

1. Go to **Firewall → NAT → Port Forward**
2. Click **"+"** to add a rule
3. Configure:

| Field | Value |
|-------|-------|
| **Interface** | WAN |
| **Protocol** | TCP |
| **Destination** | WAN address |
| **Destination Port** | `pterodactyl_ports` (alias) |
| **Redirect Target IP** | Your Pterodactyl host IP (e.g., `192.168.1.100`) |
| **Redirect Target Port** | `pterodactyl_ports` (alias) |
| **Description** | `Pterodactyl Auto Port Forwarding` |

4. Click **Save** → **Apply changes**

✅ **Done!** The script will now manage the alias content automatically.

---

## 🚀 Usage

### Docker Commands

```bash
# Start container
docker-compose -f docker-compose.ghcr.yml up -d

# View logs (live)
docker-compose -f docker-compose.ghcr.yml logs -f

# Stop container
docker-compose -f docker-compose.ghcr.yml down

# Restart container
docker-compose -f docker-compose.ghcr.yml restart

# Check status
docker ps | grep pterodactyl-portmapper
```

### Manual Python

```bash
# Run in foreground
python main.py

# Run in background (Linux/Mac)
nohup python main.py > sync.log 2>&1 &

# Stop background process
pkill -f main.py
```

---

## 📊 Output Example

```
🔒 Protected ports: [22, 80, 443, 3306, 5432, 6379, 8006, 9090]
🚀 Pterodactyl <-> OPNsense Port Mapper started
⏱️  Sync interval: 60 seconds
📋 Alias Name: pterodactyl_ports

======================================================================
🔄 Sync started: 2025-11-06 15:30:00
======================================================================

📡 Fetching Pterodactyl servers...
✓ 2 servers, 3 allocations found
📋 Pterodactyl Ports: [25565, 25566, 30000]

🔍 Fetching OPNsense alias...
✓ 2 ports found in alias
📋 OPNsense Ports: [25565, 25566]

🔍 Comparing ports...
➕ Adding: [30000]

🔄 Updating OPNsense alias...
✓ Alias updated successfully
✓ Firewall reconfigured

======================================================================
✅ Sync completed: 2025-11-06 15:30:01
📊 Status: 3 active ports
======================================================================

💤 Waiting 60 seconds until next sync...
```

---

## 🔒 Security

### Protected Ports

These ports are **never forwarded** to prevent security issues:

| Port | Service |
|------|---------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8006 | Proxmox Web UI |
| 9090 | Management Tools |

**Customize:** Edit `EXCLUDED_PORTS` in `.env`

### Best Practices

- ✅ Use a dedicated API user in OPNsense with minimal permissions
- ✅ Set `OPNSENSE_VERIFY_SSL=true` in production (requires valid SSL cert)
- ✅ Never commit `.env` file to version control
- ✅ Regularly review firewall logs
- ✅ Test in a safe environment first
- ✅ Keep the Docker image updated

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Alias not found"** | Verify alias name matches `ALIAS_NAME` in `.env` |
| **"401 Unauthorized"** | Check API credentials in `.env` and OPNsense |
| **"Ports not forwarding"** | Verify NAT rule uses the alias for both destination and target |
| **"SSL Certificate Error"** | Set `OPNSENSE_VERIFY_SSL=false` or install valid cert |
| **Container won't start** | Run `docker-compose logs` to see error details |
| **Port 80 being forwarded** | Check `EXCLUDED_PORTS` in `.env` includes port 80 |

### Debug Mode

```bash
# View detailed logs
docker-compose -f docker-compose.ghcr.yml logs -f --tail=100

# Check container is running
docker ps | grep pterodactyl

# Restart container
docker-compose -f docker-compose.ghcr.yml restart
```

---

## 📁 Project Structure

```
pterodactyl-portmapper/
├── main.py                     # Main synchronization script
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose for building
├── docker-compose.ghcr.yml     # Docker Compose for GHCR image
├── .env.example                # Example configuration
├── .github/
│   └── workflows/
│       └── docker-publish.yml  # Auto-build on releases
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git exclusions
└── README.md                   # This file
```

---

## 🔄 How It Works

1. **Fetch** - Script queries Pterodactyl API for all server allocations
2. **Filter** - Removes protected ports (SSH, HTTP, etc.)
3. **Compare** - Compares Pterodactyl ports with OPNsense alias
4. **Update** - Bulk updates alias if changes detected
5. **Apply** - Triggers OPNsense firewall reconfiguration
6. **Repeat** - Waits 60 seconds and starts again

**Example Flow:**
- Create Pterodactyl server → Port auto-added to firewall
- Delete Pterodactyl server → Port auto-removed from firewall
- Server uses port 22 → Ignored (protected port)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 💖 Support

- **Issues:** [GitHub Issues](https://github.com/Smallinger/pterodactyl-portmapper/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Smallinger/pterodactyl-portmapper/discussions)
- **Star this repo** if you find it useful! ⭐

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
