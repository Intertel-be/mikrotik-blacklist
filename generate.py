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
    
    all_cidrs = set()
    
    for source in config['sources']:
        print(f"Fetching {source['name']}...")
        try:
            lines = fetch_list(source['url'])
            for line in lines:
                ip = extract_ipv4(line)
                if ip:
                    all_cidrs.add(ip)
            print(f"  -> Collected {len([line for line in lines if extract_ipv4(line)])} entries")
        except Exception as e:
            print(f"  -> Error: {e}")
    
    print(f"\nTotal unique networks: {len(all_cidrs)}")
    
    sorted_cidrs = sorted(all_cidrs, key=lambda cidr: ipaddress.ip_network(cidr, strict=False))
    
    output_file = Path(config['output']['file'])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        for cidr in sorted_cidrs:
            f.write(f'{cidr}\n')
    
    print(f"\nWrote {len(sorted_cidrs)} CIDR entries to {output_file}")


if __name__ == '__main__':
    main()
