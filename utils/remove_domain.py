import json
import os

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path, "../config.json")

with open(config_path, "r") as f:
    config = json.loads(f.read())
    
def remove_host_entry(ip_address, domain_name):
    try:
        hosts_file_path = r'C:\Windows\System32\drivers\etc\hosts'

        # Read the hosts file and store its contents
        with open(hosts_file_path, 'r') as hosts_file:
            lines = hosts_file.readlines()

        # Filter out the added mapping
        with open(hosts_file_path, 'w') as hosts_file:
            for line in lines:
                if not f'{ip_address}\t{domain_name}' in line:
                    hosts_file.write(line)

        print(f'Removed mapping: {ip_address} -> {domain_name}')
    except Exception as e:
        print(f'Error: {str(e)}')

remove_host_entry(config["CSP-1"]["host"], config["CSP-1"]["domain"])
remove_host_entry(config["CSP-2"]["host"], config["CSP-2"]["domain"])
remove_host_entry(config["CSP-3"]["host"], config["CSP-3"]["domain"])
remove_host_entry(config["Organizer"]["host"], config["Organizer"]["domain"])
