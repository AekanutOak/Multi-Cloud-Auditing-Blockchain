from solcx import compile_standard, install_solc
from web3 import Web3
from hashlib import sha256

import json
import random
import os

install_solc("0.8.19")
current_path = os.path.dirname(__file__)

# Retrieve config file
with open(os.path.join(current_path,"./config.json"),"r") as f:
    config = json.loads(f.read())["Blockchain"]
    
    if(config["access_mode"] == "by_ip"):
        blockchain_address = config["protocol"]+"://"+config["ip"]+":"+str(config["port"])
    
    else:
        blockchain_address = config["protocol"]+"://"+config["domain"]+":"+str(config["port"])

# Retrieve list of all user in blockchain
with open(os.path.join(current_path,"./user_list.json"), "r") as f:
    user_list = json.loads(f.read())

sol_file_path = os.path.join(current_path,"../solidity/file_contract.sol")
sol_file_name = "file_contract.sol"
contract_name = "FileContract"

with open(sol_file_path,"r") as f:
    contract_file = f.read()

complied_contract_solidity = compile_standard(
    {
        "language": "Solidity",
        "sources": {sol_file_name: {"content": contract_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.19"
)

bytecode = complied_contract_solidity["contracts"][sol_file_name][contract_name]["evm"]["bytecode"]["object"]
abi = complied_contract_solidity["contracts"][sol_file_name][contract_name]["abi"]

def deploy_contract(
        deploy_address:str,
        block_tag:list[str],
        filename:str,
        description:str,
        owner_key:str,size:int
    ) -> dict:

    file_ID = sha256((filename+deploy_address).encode()).hexdigest()

    with open(os.path.join(current_path,f"../abi/{file_ID}.json"),"w") as f:
        json.dump(abi,f)

    web3 = Web3(Web3.HTTPProvider(blockchain_address))
    file_contract = web3.eth.contract(abi=abi,bytecode=bytecode)

    if(not block_tag):
       return {"status":0,
               "output":"List of block should not be empty"}
    
    if(not filename):
        return {"status":0,
                "output":"filename should not be empty"}
    
    if(not owner_key):
        return {"status":0,
                "output":"key should not be empty"}
    
    if(size <= 0):
        return {"status":0,
                "output":"file size is invalid"}
    
    with open(os.path.join(current_path,"./contract_list.json"),"r") as f:
        contract_list = json.load(f)
    
    constructor_parameters = {
        "_blockTag": block_tag, 
        "_filename": filename,
        "_description":description,
        "_owner_key":owner_key,
        "_size":size}

    tx_hash = file_contract.constructor(**constructor_parameters).transact({'from': deploy_address})
    transaction_confirm = web3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = transaction_confirm['contractAddress']

    contract_list[file_ID] = contract_address
        
    with open(os.path.join(current_path,"./contract_list.json"),"w") as f:
        json.dump(contract_list,f, indent=4)   

    return {"status":1,
            "output":contract_address}