import json
import os

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path, "../config.json")

with open(config_path, "r") as f:
    config = json.loads(f.read())

def add_host_entry(ip_address, domain_name):
    try:
        hosts_file_path = r'C:\Windows\System32\drivers\etc\hosts'

        # Read the hosts file and store its contents
        with open(hosts_file_path, 'r') as hosts_file:
            lines = hosts_file.readlines()

        # Check if the entry already exists
        entry_exists = False
        for line in lines:
            if f'{ip_address}\t{domain_name}' in line:
                entry_exists = True
                break

        # If the entry doesn't exist, add it
        if not entry_exists:
            with open(hosts_file_path, 'a') as hosts_file:
                hosts_file.write(f'{ip_address}\t{domain_name}\n')

            print(f'Added mapping: {ip_address} -> {domain_name}')
        else:
            print(f'Entry already exists: {ip_address} -> {domain_name}')
    except Exception as e:
        print(f'Error: {str(e)}')

add_host_entry(config["CSP-1"]["host"], config["CSP-1"]["domain"])
add_host_entry(config["CSP-2"]["host"], config["CSP-2"]["domain"])
add_host_entry(config["CSP-3"]["host"], config["CSP-3"]["domain"])
add_host_entry(config["Organizer"]["host"], config["Organizer"]["domain"])
