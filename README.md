# Pterodactyl Port Mapper for OPNsense

Automatically synchronize Pterodactyl server ports with OPNsense firewall NAT rules.

## 📋 Features

- ✅ Automatic port synchronization every 60 seconds (configurable)
- ✅ Bulk updates: All ports updated at once
- ✅ Smart detection: Updates only when changes occur
- ✅ Port protection: Protected ports (SSH, HTTP, etc.) never forwarded
- ✅ Automatic cleanup: Orphaned ports removed automatically
- ✅ Docker support with Docker Compose

## 🔧 Requirements

- Pterodactyl Panel with Application API Key
- OPNsense Firewall with API access
- Python 3.7+ or Docker

## 📦 Installation

### Option 1: Docker with .env file (Recommended)

1. **Clone repository:**
```bash
git clone <repository-url>
cd PetrodactylPortMapper
```

2. **Create configuration:**
```bash
cp .env.example .env
nano .env
```

3. **Start container:**
```bash
docker-compose up -d
```

4. **View logs:**
```bash
docker-compose logs -f
```

### Option 2: Docker with direct configuration

If you don't want to use a `.env` file:

1. **Clone repository:**
```bash
git clone <repository-url>
cd PetrodactylPortMapper
```

2. **Edit docker-compose.yml:**
```bash
nano docker-compose.yml
```
Uncomment and fill in your API keys and configuration in the `environment` section.

3. **Start container:**
```bash
docker-compose up -d
```

### Option 3: Manual Python installation

1. **Clone repository:**
```bash
git clone <repository-url>
cd PetrodactylPortMapper
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create configuration:**
```bash
cp .env.example .env
nano .env
```

5. **Start script:**
```bash
python main.py
```

## ⚙️ Configuration (.env)

```bash
# Pterodactyl API
PTERODACTYL_PANEL_URL=https://panel.example.com
PTERODACTYL_API_KEY=ptla_your_application_api_key

# OPNsense API
OPNSENSE_URL=https://192.168.1.1
OPNSENSE_API_KEY=your_api_key
OPNSENSE_API_SECRET=your_api_secret
OPNSENSE_VERIFY_SSL=false

# Port Mapping Configuration
ALIAS_NAME=pterodactyl_ports
SYNC_INTERVAL=60

# Protected ports (comma-separated) - will NEVER be forwarded
EXCLUDED_PORTS=22,80,443,3306,5432,6379,8006,9090
```

## 🔐 OPNsense Setup

### Step 1: Create API Keys

1. **Log into OPNsense**
2. Navigate to: **System → Access → Users**
3. Select your admin user or create a new user for the API
4. Scroll to **API keys** and click **"+"**
5. **Note down:**
   - API Key (e.g., `rEDXpKba+fLVfNX...`)
   - API Secret (e.g., `I4xyP5uLJ2lgDId...`)
6. Add these to your `.env` file

### Step 2: Create Alias

1. Navigate to: **Firewall → Aliases**
2. Click **"+"** (Add)
3. Configure the alias:
   - **Enabled:** ✓ (enabled)
   - **Name:** `pterodactyl_ports` (must match ALIAS_NAME in .env)
   - **Type:** Port(s)
   - **Content:** (leave empty - will be filled automatically)
   - **Description:** `Dynamic port forwards for Pterodactyl servers`
4. Click **Save**
5. Click **Apply** in the top right

### Step 3: Create NAT Port Forward Rule

1. Navigate to: **Firewall → NAT → Port Forward**
2. Click **"+"** (Add)
3. Configure the rule:

   **Translation:**
   - **Interface:** WAN (your external interface)
   - **Protocol:** TCP
   - **Source:** any
   - **Source Port:** (empty)
   
   **Destination:**
   - **Destination:** WAN address
   - **Destination Port:** `pterodactyl_ports` (select the alias!)
   
   **Redirect Target:**
   - **Redirect target IP:** `192.168.x.x` (IP of your Pterodactyl host)
   - **Redirect target port:** `pterodactyl_ports` (select the alias!)
   
   **Misc:**
   - **Description:** `Pterodactyl Auto Port Forwarding`
   - **NAT reflection:** Use system default
   - **Filter rule association:** Pass

4. Click **Save**
5. Click **Apply changes** in the top right

### Step 4: Verify Firewall Rule (Optional)

The NAT rule automatically creates a firewall rule. Check under:
- **Firewall → Rules → WAN**
- You should see a rule: `NAT Pterodactyl Auto Port Forwarding`

## 🚀 Usage

### With Docker

```bash
# Start container
docker-compose up -d

# View live logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart after changes
docker-compose restart
```

### Manual

```bash
# Run in foreground
python main.py

# Run in background (Linux/Mac)
nohup python main.py > sync.log 2>&1 &

# Run as Windows Service (with NSSM)
nssm install PterodactylPortMapper "C:\Path\To\Python\python.exe" "C:\Path\To\main.py"
nssm start PterodactylPortMapper
```

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
✓ 2 servers, 2 allocations found
📋 Pterodactyl Ports: [20000, 20001]

🔍 Fetching OPNsense alias...
✓ 2 ports found in alias
📋 OPNsense Ports: [20000, 20001]

🔍 Comparing ports...
✅ No differences - all ports are in sync!

======================================================================
✅ Sync completed: 2025-11-06 15:30:00
📊 Status: 2 active ports
======================================================================

💤 Waiting 60 seconds until next sync...
```

## 🔒 Security

### Protected Ports

The script automatically prevents forwarding of critical system ports:
- `22` - SSH
- `80` - HTTP
- `443` - HTTPS
- `3306` - MySQL
- `5432` - PostgreSQL
- `6379` - Redis
- `8006` - Proxmox Web UI
- `9090` - Portainer/Management Tools

**Customization:** Edit `EXCLUDED_PORTS` in the `.env` file.

### Best Practices

1. ✅ Use a **dedicated API user** in OPNsense
2. ✅ Set **OPNSENSE_VERIFY_SSL=true** in production (after SSL certificate setup)
3. ✅ Store the `.env` file **securely** (contains API keys)
4. ✅ Regularly check logs for anomalies
5. ✅ Test in a **test environment** first

## 🐛 Troubleshooting

### Problem: "Alias not found"
**Solution:** Make sure the alias name in OPNsense exactly matches `ALIAS_NAME` in `.env`.

### Problem: "401 Unauthorized"
**Solution:** Check your API keys in the `.env` file and in OPNsense.

### Problem: "Ports not being forwarded"
**Solution:** 
1. Check the NAT Port Forward rule
2. Make sure the alias is used as **Destination Port** AND **Redirect Target Port**
3. Check firewall logs: **Firewall → Log Files → Live View**

### Problem: "SSL Certificate Verify Failed"
**Solution:** Set `OPNSENSE_VERIFY_SSL=false` in `.env` or install a valid SSL certificate in OPNsense.

### Problem: Docker container won't start
**Solution:**
```bash
# Check logs
docker-compose logs

# Check container status
docker-compose ps

# Verify .env file
cat .env
```

## 📁 Project Structure

```
PetrodactylPortMapper/
├── main.py      # Main script
├── requirements.txt      # Python dependencies
├── .env                  # Configuration (don't commit!)
├── .env.example          # Example configuration
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker Compose config
├── .dockerignore         # Docker ignore rules
└── README.md             # This file
```

## 🔄 Workflow

1. **Create Pterodactyl server** → Port automatically forwarded in OPNsense
2. **Delete Pterodactyl server** → Port automatically removed from OPNsense
3. **Manual port in alias** → Removed (if not in Pterodactyl)
4. **Protected port** → Ignored and never forwarded

## 📝 License

MIT License

## 🤝 Support

If you have problems:
1. Check the logs
2. Review OPNsense API documentation
3. Create an issue in the repository

## 🎯 Roadmap

- [ ] Web UI for monitoring
- [ ] Prometheus metrics export
- [ ] Multi-firewall support
- [ ] Port range support
- [ ] UDP protocol support
