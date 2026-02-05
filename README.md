# MikroTik IP Blacklist Generator

An automated IP blacklist aggregator that generates MikroTik RouterOS firewall address lists from multiple threat intelligence sources.

## Overview

This project fetches and consolidates IPv4 addresses from various reputable threat intelligence feeds, then generates a ready-to-use MikroTik RouterOS script that can be directly imported into your router's firewall configuration.

The blacklist is automatically updated daily via GitHub Actions, ensuring your network protection stays current with the latest threat intelligence.

## Features

- **Automated Daily Updates**: GitHub Actions workflow runs daily at 2 AM UTC
- **Multiple Threat Sources**: Aggregates data from 8 trusted security feeds
- **Deduplicated Entries**: Removes duplicate IPs across sources
- **Source Attribution**: Each entry includes comments showing which feed(s) reported it
- **Ready-to-Import**: Generates MikroTik `.rsc` script files
- **IPv4 Support**: Handles both single IPs and CIDR notation

## Threat Intelligence Sources

The blacklist aggregates data from:

- **Spamhaus DROP** - Don't Route Or Peer lists
- **Spamhaus EDROP** - Extended DROP list
- **DShield** - SANS Internet Storm Center block list
- **Blocklist.de** - Attacks registered by fail2ban
- **Feodo Tracker** - Botnet C&C servers
- **FireHOL Level1** - Aggregated attack sources
- **Tor Exit Nodes** - Tor network exit points
- **AbuseIPDB** - Community-reported abusive IPs (100% confidence, 7-day)

## Usage

### Download the Latest Blacklist

The pre-generated blacklist is available in the [`output/`](output/) directory:

- **`output/blacklist.rsc`** - MikroTik RouterOS script (ready to import)
- **`output/blacklist.txt`** - Plain text list of IPs/CIDRs

### Import to MikroTik Router

#### Method 1: Web Interface (WinBox/WebFig)

1. Download `output/blacklist.rsc` from this repository
2. Open your MikroTik router's interface
3. Go to **Files** and upload the `blacklist.rsc` file
4. Open **New Terminal** and run:
   ```
   /import blacklist.rsc
   ```
5. The script will clear any existing "blacklist" address list and populate it with the latest entries

#### Method 2: SSH/Terminal

```bash
# Download the blacklist
curl -o blacklist.rsc https://raw.githubusercontent.com/Intertel-be/mikrotik-blacklist/main/output/blacklist.rsc

# SCP to your router (replace with your router's IP)
scp blacklist.rsc admin@192.168.88.1:/

# SSH into the router and import
ssh admin@192.168.88.1
/import blacklist.rsc
```

### Apply the Blacklist to Firewall

After importing, you need to create firewall rules to use the blacklist:

```routeros
/ip firewall raw add chain=prerouting src-address-list=blacklist action=drop comment="Drop blacklisted IPs"
```

**Note**: Using the RAW table with prerouting chain is more efficient than filter rules, as it drops packets before connection tracking. This significantly reduces CPU load when dealing with large blacklists.

## Configuration

### Customize Sources

Edit `config.yaml` to add, remove, or modify threat intelligence sources:

```yaml
sources:
  - name: Your Custom Source
    url: https://example.com/your-blacklist.txt

output:
  file: output/blacklist.rsc
  list_name: blacklist  # Change the address list name if desired
```

### Generate Manually

Requirements:
- Python 3.11+
- Dependencies: `pyyaml`, `requests`

```bash
# Install dependencies
pip install pyyaml requests

# Generate the blacklist
python generate.py
```

The script will:
1. Fetch all configured threat feeds
2. Parse and extract IPv4 addresses/CIDRs
3. Deduplicate entries
4. Sort by IP address
5. Generate `output/blacklist.rsc` with MikroTik commands

## Output Format

The generated `.rsc` file contains:
- Header with total entry count
- Command to clear existing "blacklist" address list
- Individual add commands for each IP/CIDR with source attribution

Example:
```routeros
# MikroTik RouterOS Blacklist Script
# Total entries: 110411

/ip firewall address-list remove [find list="blacklist"]

/ip firewall address-list add list="blacklist" address=1.10.16.0/20 comment="Spamhaus DROP, FireHOL Level1"
/ip firewall address-list add list="blacklist" address=1.12.226.163/32 comment="Blocklist.de, AbuseIPDB"
```

## Automation

The repository includes a GitHub Actions workflow (`.github/workflows/update-blacklist.yml`) that:

- Runs daily at 2 AM UTC
- Can be manually triggered via "Actions" tab
- Automatically commits and pushes updates when changes are detected

## Important Considerations

### Performance Impact

This blacklist contains **100,000+ entries**. Loading this many address list entries on a MikroTik router can:
- Take several minutes to import
- Consume significant memory (especially on lower-end models)
- Impact firewall processing performance

**Recommendations:**
- Test on non-production routers first
- Monitor CPU/memory usage after import
- Consider filtering sources or using only specific feeds for smaller lists
- For high-traffic networks, consider hardware with adequate resources (e.g., CCR series)

### False Positives

Blocking lists may contain legitimate services:
- **Tor Exit Nodes**: Blocks Tor traffic (may affect privacy-conscious users)
- Cloud provider IPs may occasionally appear on abuse lists
- Review your logs periodically for legitimate blocked traffic

### Updating

Importing the script will **replace all existing entries** in the "blacklist" address list. If you have custom entries, use a different list name in `config.yaml`.

## License

This project is provided as-is. The threat intelligence data belongs to the respective source providers. Please review their terms of service.

## Credits

Maintained by [Intertel](https://github.com/Intertel-be)

Threat intelligence provided by:
- [Spamhaus](https://www.spamhaus.org/)
- [SANS DShield](https://www.dshield.org/)
- [Blocklist.de](https://www.blocklist.de/)
- [Abuse.ch](https://abuse.ch/)
- [FireHOL](https://github.com/ktsaou/blocklist-ipsets)
- [Tor Project](https://www.torproject.org/)
- [AbuseIPDB](https://www.abuseipdb.com/)

## Contributing

Contributions welcome! Feel free to:
- Add new threat intelligence sources
- Improve parsing logic
- Optimize performance
- Report issues

## Disclaimer

This blacklist is provided for network security purposes. Use at your own risk. The maintainers are not responsible for any blocking of legitimate traffic or network issues that may arise from using this blacklist.
