#!/usr/bin/env python3
"""
Pterodactyl <-> OPNsense NAT Sync
Automatically synchronizes port forwarding rules between Pterodactyl and OPNsense
"""

import requests
import json
import os
import time
from typing import List, Dict, Set
from dotenv import load_dotenv
from datetime import datetime

# Load .env file
load_dotenv()


class PterodactylAPI:
    def __init__(self, panel_url: str, api_key: str):
        """Initialize Pterodactyl API connection"""
        self.panel_url = panel_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_all_servers(self) -> List[Dict]:
        """Fetch all servers with allocations from Pterodactyl Panel"""
        servers = []
        page = 1
        
        while True:
            url = f"{self.panel_url}/api/application/servers?include=allocations&page={page}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ Error fetching servers: {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            data = response.json()
            servers.extend(data['data'])
            
            meta = data.get('meta', {}).get('pagination', {})
            if meta.get('current_page', 1) >= meta.get('total_pages', 1):
                break
            
            page += 1
        
        return servers
    
    def extract_allocations(self, servers: List[Dict]) -> List[Dict]:
        """Extract all allocations with server information"""
        allocations = []
        
        for server in servers:
            attributes = server.get('attributes', {})
            server_name = attributes.get('name', 'Unknown')
            server_id = attributes.get('identifier', 'Unknown')
            server_uuid = attributes.get('uuid', 'Unknown')
            
            relationships = attributes.get('relationships', {})
            allocations_data = relationships.get('allocations', {}).get('data', [])
            
            for allocation in allocations_data:
                alloc_attrs = allocation.get('attributes', {})
                allocations.append({
                    'server_name': server_name,
                    'server_id': server_id,
                    'server_uuid': server_uuid,
                    'ip': alloc_attrs.get('ip', 'Unknown'),
                    'port': alloc_attrs.get('port', 0),
                    'is_default': alloc_attrs.get('is_default', False),
                    'allocation_id': allocation.get('object') + '_' + str(alloc_attrs.get('id', 0))
                })
        
        return allocations


class OPNsenseAPI:
    def __init__(self, url: str, api_key: str, api_secret: str, alias_name: str, verify_ssl: bool = True):
        """Initialize OPNsense API connection"""
        self.url = url.rstrip('/')
        self.auth = (api_key, api_secret)
        self.alias_name = alias_name
        self.verify_ssl = verify_ssl
        
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_alias_uuid(self) -> str:
        """Get the UUID of the alias"""
        url = f"{self.url}/api/firewall/alias/getAliasUUID/{self.alias_name}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code == 200:
                data = response.json()
                return data.get('uuid', '')
            return ''
        except Exception as e:
            print(f"❌ Error fetching alias UUID: {e}")
            return ''
    
    def get_alias_content(self) -> Dict:
        """Fetch complete alias with all entries"""
        alias_uuid = self.get_alias_uuid()
        if not alias_uuid:
            print(f"❌ Alias '{self.alias_name}' not found!")
            return {}
        
        url = f"{self.url}/api/firewall/alias/getItem/{alias_uuid}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ Error fetching alias: {e}")
            return {}
    
    def get_alias_ports(self) -> Set[int]:
        """Fetch all ports from alias via getItem"""
        alias_uuid = self.get_alias_uuid()
        if not alias_uuid:
            return set()
        
        url = f"{self.url}/api/firewall/alias/getItem/{alias_uuid}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code == 200:
                data = response.json()
                alias_data = data.get('alias', {})
                
                # Content can be either a Dict (with entries) or a string (empty) is
                content = alias_data.get('content', {})
                
                ports = set()
                
                # If content is a Dict (has entries)
                if isinstance(content, dict):
                    for key, value_dict in content.items():
                        # Keys können row_X oder direkt die Ports is
                        # If the key is a number, use it directly
                        if key.isdigit():
                            ports.add(int(key))
                        # Otherwise check row_X format
                        elif key.startswith('row_'):
                            selected_value = value_dict.get('selected', '')
                            if selected_value and str(selected_value).isdigit():
                                ports.add(int(selected_value))
                # If content is a string (kann auch newline-separated is)
                elif isinstance(content, str) and content:
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and line.isdigit():
                            ports.add(int(line))
                
                return ports
            return set()
        except Exception as e:
            print(f"❌ Error fetching ports: {e}")
            return set()
    
    def add_port_to_alias(self, port: int, description: str) -> bool:
        """Add a port to alias via setItem"""
        alias_uuid = self.get_alias_uuid()
        if not alias_uuid:
            print(f"  ❌ Alias '{self.alias_name}' not found!")
            return False
        
        # Get current alias content
        url = f"{self.url}/api/firewall/alias/getItem/{alias_uuid}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code != 200:
                print(f"  ❌ Error fetching alias: {response.text}")
                return False
            
            alias_item = response.json().get('alias', {})
            
            # Extract only the 'selected' values from content
            # Content kann Dict (with entries) oder String (empty/"") is
            content = alias_item.get('content', {})
            current_ports = []
            
            if isinstance(content, dict):
                for key, value_dict in content.items():
                    if key.startswith('row_'):
                        selected = value_dict.get('selected', '')
                        if selected:
                            current_ports.append(selected)
            elif isinstance(content, str) and content:
                current_ports = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Check if port already exists
            port_str = str(port)
            if port_str in current_ports:
                print(f"  ℹ️  Port {port} already in alias")
                return True
            
            # Add new port
            current_ports.append(port_str)
            
            # Extract values - können dict.selected oder direkt string is
            def get_value(field, default=''):
                val = alias_item.get(field, default)
                if isinstance(val, dict):
                    return val.get('selected', default)
                return val if val else default
            
            # Create update payload
            update_data = {
                'alias': {
                    'enabled': get_value('enabled', '1'),
                    'name': get_value('name', self.alias_name),
                    'type': get_value('type', 'port'),
                    'content': '\n'.join(current_ports),  # As newline-separated string
                    'description': get_value('description', '')
                }
            }
            
            # Update via setItem
            url = f"{self.url}/api/firewall/alias/setItem/{alias_uuid}"
            response = requests.post(
                url,
                auth=self.auth,
                json=update_data,
                verify=self.verify_ssl,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'saved':
                    print(f"  ✅ Port {port} added to alias")
                    return True
                else:
                    print(f"  ❌ Error: {result}")
                    return False
            
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
            return False
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def remove_port_from_alias(self, port: int) -> bool:
        """Remove a port from alias via setItem"""
        alias_uuid = self.get_alias_uuid()
        if not alias_uuid:
            print(f"  ❌ Alias '{self.alias_name}' not found!")
            return False
        
        # Get current alias content
        url = f"{self.url}/api/firewall/alias/getItem/{alias_uuid}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code != 200:
                print(f"  ❌ Error fetching alias: {response.text}")
                return False
            
            alias_item = response.json().get('alias', {})
            
            # Extract only the 'selected' values from content
            # Content kann Dict (with entries) oder String (empty/"") is
            content = alias_item.get('content', {})
            current_ports = []
            
            if isinstance(content, dict):
                for key, value_dict in content.items():
                    if key.startswith('row_'):
                        selected = value_dict.get('selected', '')
                        if selected:
                            current_ports.append(selected)
            elif isinstance(content, str) and content:
                current_ports = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Check if port exists
            port_str = str(port)
            if port_str not in current_ports:
                print(f"  ℹ️  Port {port} not found in alias")
                return True
            
            # Remove port
            current_ports.remove(port_str)
            
            # Extract values - können dict.selected oder direkt string is
            def get_value(field, default=''):
                val = alias_item.get(field, default)
                if isinstance(val, dict):
                    return val.get('selected', default)
                return val if val else default
            
            # Create update payload
            update_data = {
                'alias': {
                    'enabled': get_value('enabled', '1'),
                    'name': get_value('name', self.alias_name),
                    'type': get_value('type', 'port'),
                    'content': '\n'.join(current_ports),  # As newline-separated string
                    'description': get_value('description', '')
                }
            }
            
            # Update via setItem
            url = f"{self.url}/api/firewall/alias/setItem/{alias_uuid}"
            response = requests.post(
                url,
                auth=self.auth,
                json=update_data,
                verify=self.verify_ssl,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'saved':
                    print(f"  🗑️  Port {port} removed from alias")
                    return True
                else:
                    print(f"  ❌ Error: {result}")
                    return False
            
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
            return False
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def update_alias_ports(self, ports: Set[int], allocations: List[Dict]) -> bool:
        """Update alias with all ports at once (Bulk Update)"""
        alias_uuid = self.get_alias_uuid()
        if not alias_uuid:
            print(f"❌ Alias '{self.alias_name}' not found!")
            return False
        
        # Get current alias content
        url = f"{self.url}/api/firewall/alias/getItem/{alias_uuid}"
        try:
            response = requests.get(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code != 200:
                print(f"❌ Error fetching alias: {response.text}")
                return False
            
            alias_item = response.json().get('alias', {})
            
            # Extract values - können dict.selected oder direkt string is
            def get_value(field, default=''):
                val = alias_item.get(field, default)
                if isinstance(val, dict):
                    return val.get('selected', default)
                return val if val else default
            
            # Convert all ports to strings and sort them
            port_strings = sorted([str(p) for p in ports])
            
            # Create update payload mit ALLEN Ports
            update_data = {
                'alias': {
                    'enabled': get_value('enabled', '1'),
                    'name': get_value('name', self.alias_name),
                    'type': get_value('type', 'port'),
                    'content': '\n'.join(port_strings),  # All ports as newline-separated string
                    'description': get_value('description', 'Pterodactyl Port Mapper')
                }
            }
            
            # Update via setItem
            url = f"{self.url}/api/firewall/alias/setItem/{alias_uuid}"
            response = requests.post(
                url,
                auth=self.auth,
                json=update_data,
                verify=self.verify_ssl,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'saved':
                    return True
                else:
                    print(f"❌ Error: {result}")
                    return False
            
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def reconfigure_firewall(self) -> bool:
        """Apply firewall changes (reconfigure)"""
        url = f"{self.url}/api/firewall/alias/reconfigure"
        try:
            response = requests.post(url, auth=self.auth, verify=self.verify_ssl)
            if response.status_code == 200:
                print("✅ Firewall reconfigured")
                return True
            print(f"⚠️  Reconfigure failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"❌ Error beim Reconfigure: {e}")
            return False


class PortMapperSync:
    def __init__(self, ptero_api: PterodactylAPI, opnsense_api: OPNsenseAPI, excluded_ports: Set[int] = None):
        """Initialize Sync Manager"""
        self.ptero = ptero_api
        self.opnsense = opnsense_api
        self.excluded_ports = excluded_ports or set()
    
    def sync(self):
        """Perform synchronization"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 70)
        print(f"🔄 Sync started: {timestamp}")
        print("=" * 70)
        
        # 1. Collect all ports from Pterodactyl
        print("\n📡 Fetching Pterodactyl servers...")
        servers = self.ptero.get_all_servers()
        allocations = self.ptero.extract_allocations(servers)
        pterodactyl_ports = {alloc['port'] for alloc in allocations}
        
        # Filter out excluded ports
        if self.excluded_ports:
            blocked_ports = pterodactyl_ports & self.excluded_ports
            if blocked_ports:
                print(f"⚠️  WARNING: {len(blocked_ports)} protected ports found and ignored:")
                for port in sorted(blocked_ports):
                    print(f"   🚫 Port {port} (in EXCLUDED_PORTS)")
            pterodactyl_ports = pterodactyl_ports - self.excluded_ports
        
        print(f"✓ {len(servers)} servers, {len(allocations)} allocations found")
        print(f"📋 Pterodactyl Ports: {sorted(pterodactyl_ports)}")
        
        # 2. Collect all ports from OPNsense
        print("\n🔍 Fetching OPNsense alias...")
        opnsense_ports_raw = self.opnsense.get_alias_ports()
        
        # Check for forbidden ports in alias
        forbidden_in_alias = set()
        if self.excluded_ports:
            forbidden_in_alias = opnsense_ports_raw & self.excluded_ports
            if forbidden_in_alias:
                print(f"⚠️  WARNING: {len(forbidden_in_alias)} protected ports found in alias:")
                for port in sorted(forbidden_in_alias):
                    print(f"   🚫 Port {port} will be removed (in EXCLUDED_PORTS)")
        
        # Clean up OPNsense ports (without protected ports)
        opnsense_ports = opnsense_ports_raw - self.excluded_ports
        
        print(f"✓ {len(opnsense_ports)} ports found in alias")
        print(f"📋 OPNsense Ports: {sorted(opnsense_ports)}")
        
        # 3. Check for differences (including forbidden ports to remove)
        print("\n🔍 Comparing ports...")
        ports_to_add = pterodactyl_ports - opnsense_ports
        ports_to_remove = (opnsense_ports - pterodactyl_ports) | forbidden_in_alias
        
        # If no changes and no forbidden ports
        if not ports_to_add and not ports_to_remove:
            print("✅ No differences - all ports are in sync!")
            print("\n" + "=" * 70)
            print(f"✅ Sync completed: {timestamp}")
            print(f"📊 Status: {len(pterodactyl_ports)} active ports")
            print("=" * 70)
            return
        
        print("⚠️  Differences found:")
        if ports_to_add:
            print(f"\n  ➕ Add: {sorted(ports_to_add)}")
            for allocation in allocations:
                if allocation['port'] in ports_to_add:
                    print(f"     • {allocation['port']} - {allocation['server_name']}")
        
        if ports_to_remove:
            # Differentiate between normal and protected ports
            normal_remove = ports_to_remove - forbidden_in_alias
            if normal_remove:
                print(f"\n  ➖ Remove (orphaned): {sorted(normal_remove)}")
            if forbidden_in_alias:
                print(f"\n  🚫 Remove (protected): {sorted(forbidden_in_alias)}")
        
        # 5. Update and Reconfigure
        print("\n💾 Updating alias...")
        if self.opnsense.update_alias_ports(pterodactyl_ports, allocations):
            print("✅ Alias successfully updated")
            
            print("\n🔄 Applying firewall changes...")
            self.opnsense.reconfigure_firewall()
        else:
            print("❌ Error beim Aktualisieren des Alias")
        
        print("\n" + "=" * 70)
        print(f"✅ Sync completed: {timestamp}")
        print(f"📊 Status: {len(pterodactyl_ports)} active ports")
        print("=" * 70)
    
    def run_continuous(self, interval: int = 60):
        """Run sync continuously"""
        print("🚀 Pterodactyl <-> OPNsense Port Mapper started")
        print(f"⏱️  Sync interval: {interval} seconds")
        print(f"📋 Alias Name: {self.opnsense.alias_name}")
        print("\nPress Ctrl+C to exit...\n")
        
        try:
            while True:
                try:
                    self.sync()
                except Exception as e:
                    print(f"\n❌ Error during sync: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"\n💤 Waiting {interval} seconds until next sync...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Port Mapper is shutting down...")


def main():
    # Load configuration from .env
    PTERO_URL = os.getenv("PTERODACTYL_PANEL_URL")
    PTERO_KEY = os.getenv("PTERODACTYL_API_KEY")
    
    OPNSENSE_URL = os.getenv("OPNSENSE_URL")
    OPNSENSE_KEY = os.getenv("OPNSENSE_API_KEY")
    OPNSENSE_SECRET = os.getenv("OPNSENSE_API_SECRET")
    OPNSENSE_VERIFY_SSL = os.getenv("OPNSENSE_VERIFY_SSL", "true").lower() == "true"
    
    ALIAS_NAME = os.getenv("ALIAS_NAME", "pterodactyl_ports")
    SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "60"))
    
    # Parse EXCLUDED_PORTS from .env (comma-separated list)
    excluded_ports_str = os.getenv("EXCLUDED_PORTS", "")
    excluded_ports = set()
    if excluded_ports_str:
        try:
            excluded_ports = {int(p.strip()) for p in excluded_ports_str.split(',') if p.strip()}
            if excluded_ports:
                print(f"🔒 Protected ports: {sorted(excluded_ports)}")
        except ValueError:
            print("⚠️  Warning: EXCLUDED_PORTS contains invalid values, will be ignored")
    
    # Validation
    if not all([PTERO_URL, PTERO_KEY, OPNSENSE_URL, OPNSENSE_KEY, OPNSENSE_SECRET]):
        print("❌ Error: Not all required environment variables set!")
        print("\nRequired in .env:")
        print("  - PTERODACTYL_PANEL_URL")
        print("  - PTERODACTYL_API_KEY")
        print("  - OPNSENSE_URL")
        print("  - OPNSENSE_API_KEY")
        print("  - OPNSENSE_API_SECRET")
        print("\nOptional:")
        print("  - ALIAS_NAME (default: pterodactyl_ports)")
        print("  - SYNC_INTERVAL (default: 60)")
        print("  - OPNSENSE_VERIFY_SSL (default: true)")
        print("  - EXCLUDED_PORTS (comma-separated, e.g. 22,80,443)")
        return
    
    # Initialize APIs
    ptero_api = PterodactylAPI(PTERO_URL, PTERO_KEY)
    opnsense_api = OPNsenseAPI(OPNSENSE_URL, OPNSENSE_KEY, OPNSENSE_SECRET, ALIAS_NAME, OPNSENSE_VERIFY_SSL)
    
    # Start sync
    sync_manager = PortMapperSync(ptero_api, opnsense_api, excluded_ports)
    sync_manager.run_continuous(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
