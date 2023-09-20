from solcx import compile_standard, install_solc
from web3 import Web3
import json, random, os

# Specify the solidity compiler version
install_solc("0.8.19")

# The network address that the program will connect is stored in file
# Please change to content of that file to change the network address
current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path,"config.json")

with open(config_path,"r") as f:
    config = json.loads(f.read())["Blockchain"]

if(config["access_mode"] == "by_ip"):
    blockchain_address = config["protocol"]+"://"+config["ip"]+":"+str(config["port"])

else:
    blockchain_address = config["protocol"]+"://"+config["domain"]+":"+str(config["port"])

print(blockchain_address)