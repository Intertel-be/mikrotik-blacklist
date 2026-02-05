#!/usr/bin/env python3

import yaml
import requests
import ipaddress
from pathlib import Path


def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def fetch_list(url):
    headers = {'User-Agent': 'IP-Blacklist-Fetcher/1.0'}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text.split('\n')


def extract_ipv4(line):
    line = line.strip()
    
    if not line or line.startswith('#') or line.startswith(';'):
        return None
    
    if '#' in line:
        line = line.split('#')[0].strip()
    if ';' in line:
        line = line.split(';')[0].strip()
    
    if '\t' in line:
        fields = line.split('\t')
        if len(fields) >= 2:
            ip_part = fields[0].strip()
            netmask = fields[1].strip()
            try:
                prefix_len = sum(bin(int(octet)).count('1') for octet in netmask.split('.'))
                line = f'{ip_part}/{prefix_len}'
            except:
                line = ip_part
        else:
            line = fields[0].strip()
    
    token = line.split()[0] if line.split() else ''
    
    if not token:
        return None
    
    try:
        network = ipaddress.ip_network(token, strict=False)
        if network.version == 4:
            return str(network)
    except ValueError:
        pass
    
    return None


def main():
    config = load_config()
    
    # Dictionary to store CIDR -> source name mapping
    cidr_sources = {}
    
    for source in config['sources']:
        print(f"Fetching {source['name']}...")
        try:
            lines = fetch_list(source['url'])
            count = 0
            for line in lines:
                ip = extract_ipv4(line)
                if ip:
                    # If IP already exists, append source name
                    if ip in cidr_sources:
                        cidr_sources[ip] += f", {source['name']}"
                    else:
                        cidr_sources[ip] = source['name']
                    count += 1
            print(f"  -> Collected {count} entries")
        except Exception as e:
            print(f"  -> Error: {e}")
    
    print(f"\nTotal unique networks: {len(cidr_sources)}")
    
    sorted_cidrs = sorted(cidr_sources.keys(), key=lambda cidr: ipaddress.ip_network(cidr, strict=False))
    
    output_file = Path(config['output']['file'])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    list_name = config['output'].get('list_name', 'blacklist')
    
    with open(output_file, 'w') as f:
        # Write header
        f.write('# MikroTik RouterOS Blacklist Script\n')
        f.write(f'# Total entries: {len(sorted_cidrs)}\n')
        f.write('\n')
        
        # Remove existing entries from the list
        f.write(f'/ip firewall address-list remove [find list="{list_name}"]\n')
        f.write('\n')
        
        # Add all CIDR entries with source as comment
        for cidr in sorted_cidrs:
            source_comment = cidr_sources[cidr]
            f.write(f'/ip firewall address-list add list="{list_name}" address={cidr} comment="{source_comment}"\n')
    
    print(f"\nWrote {len(sorted_cidrs)} entries to {output_file}")
    print(f"Address list name: {list_name}")


if __name__ == '__main__':
    main()
