from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from web3 import Web3
from web3.exceptions import ContractLogicError

# You can enable this warning later, this warning has no effect to this project
import datetime
import json
import random
import os
import warnings

warnings.filterwarnings("ignore")

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

# Establish smart contract instance
file_contract = None
account_list = None

def select_contract(file_ID:str,contract_address:str) -> dict:
    global file_contract, account_list

    try:
        with open(os.path.join(current_path,f"../abi/{file_ID}.json"),"r") as f:
            contract_abi = f.read()

    except:
        return {"status":0,"output":"No such a file ID"}
    

    web3 = Web3(Web3.HTTPProvider(blockchain_address))
    account_list = web3.eth.accounts

    try:
        file_contract = web3.eth.contract(address=contract_address,abi=contract_abi)

    except:
        return {"status":0,"output":"Either contract address or blockchain address is invalid"}
    
    return {"status":1,"output":f"select contract address {contract_address} successfully."}

def get_metadata(caller_address:str) -> dict:
    global file_contract
    output = file_contract.functions.get_metadata().call({"from":caller_address})
    keys = ["filename","description","create","updated","size","blocks","owner"]
    output = dict(zip(keys,output))

    return {"status":1,"output":output}

def get_all_tag(caller_address:str) -> dict:
    global file_contract
    output = file_contract.functions.get_all_tag().call({"from":caller_address})
    return {"status":1,"output":output}

def get_tags(caller_address:str,tag_list:list[int]) -> dict:
    global file_contract
    output = file_contract.functions.get_tags(tag_list).call({"from":caller_address})
    return {"status":1,"output":output}

def get_owner_address():
    global file_contract
    output = file_contract.functions.get_owner_address().call()
    return {"status":1,"output":output}

def get_ACL(account_address:str) -> dict:
    global file_contract

    output = file_contract.functions.get_ACL(account_address).call()
    return {"status":1,"output":output} 

def assign_ACL(caller_address:str,users:list[str],permissions:list[str],keys:list[str]=[""]) -> dict:
    username = user_list[caller_address]
    if(len(users) != len(permissions)):
        return {"status":0,"output":"Number of address of permission does not match."}
    
    for permission in permissions:
        if(len(permission) != 2):
            return {"status":0,"output":"Permission should be 2 length string"}
        
        if(permission not in ["r-","--","rw","-w"]):
            if(permission in ["o-"]):
                try:
                    tx = file_contract.functions.assign_ACL(permissions,["" for i in range(len(users))],users).transact({'from': caller_address})
                    return {"status":1,"oiutput":"Assign permission to organizer successfully"}
                
                except ValueError as e:
                    return {"status":0,"output":e.args[0]["message"]}
                
            else:
                return {"status":0,"output":"Permission read should be r-, --, -w, or rw"}
            
    for address in users:
        if(address not in user_list):
            return {"status":0,"output":f"unknown user address {address}"}

    with open(os.path.join(current_path,f'../{username}/private_key.pem'), 'rb') as key_file:
        private_key = RSA.import_key(key_file.read())

    ciphertext = get_key(caller_address)

    if(ciphertext["status"] <= 0):
        print("error here")
        return {"status":0,"output":ciphertext["output"]}
    
    ciphertext = ciphertext["output"].encode("latin-1")

    cipher = PKCS1_OAEP.new(private_key)
    key = cipher.decrypt(ciphertext)

    key_list = []
    for address in users:
        username = user_list[address]
        with open(os.path.join(current_path,f'../{username}/public_key.pem'), 'rb') as key_file:
            public_key = RSA.import_key(key_file.read())
    
        cipher = PKCS1_OAEP.new(public_key)
        ciphertext = cipher.encrypt(key).decode("latin-1")
        key_list.append(ciphertext)

    tx = file_contract.functions.assign_ACL(permissions,key_list,users).transact({'from': caller_address})
    return {"status":1,"output":"success to assign new ACL"}

    
def revoke_users(caller_address,users:list[str]):
    try:
        tx = file_contract.functions.revoke_users(users).transact({'from': caller_address})
        return {"status":1,"output":"success"}
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
def get_key(caller_address):
    global file_contract
    output = file_contract.functions.get_key().call({"from":caller_address})
    file_contract.functions.get_key().transact({"from":caller_address})
    return {"status":1,"output":output}

def submit_challenge(caller_address,block_index_list):
    try:
        tx = file_contract.functions.submit_challenge(block_index_list).transact({"from": caller_address})
        return {"status":1,"output":"success"}

    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def get_challenge(caller_address):
    try:
        tx = file_contract.functions.get_challenge().call({"from":caller_address})
        return {"status":1,"output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def submit_response(caller_address, block_list):
    try:
        tx = file_contract.functions.submit_response(block_list).transact({"from":caller_address})
        return {"status":1, "output":"success"}

    except ValueError as e:
        return {"status":0,"output":e}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def get_response(caller_address):
    try:
        tx = file_contract.functions.get_response().call({"from":caller_address})
        return {"status":1, "output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def get_all_ACL() -> dict:
    global file_contract, account_list
    accounts = []
    ACLs = []
    for account in account_list:
        ACL = file_contract.functions.get_ACL(account).call()
        if(ACL != ""):
            accounts.append(account)
            ACLs.append(ACL)

    return {"status":1,"output":dict(zip(accounts,ACLs))}

def get_file_list(caller_address):
    global file_contract, account_list

    own_list = []
    share_list = []
    with open(os.path.join(current_path,"./contract_list.json"),"r") as f:
        contract_list = json.loads(f.read())

    for key,value in contract_list.items():
        select_contract(key,value)
        if(get_owner_address()["output"] == caller_address):
            access_control = get_all_ACL()

            if(access_control["status"] <= 0):
                return {"status":0,"output":access_control["output"]}
            
            access_control = access_control["output"]
            metadata = get_metadata(caller_address)
            if(metadata["status"] <= 0):
                return {"status":0,"output":metadata["output"]}
            
            metadata = metadata["output"]
            create_time = datetime.datetime.utcfromtimestamp(metadata["create"])
            update_time = datetime.datetime.utcfromtimestamp(metadata["updated"])
            # Format the datetime object as yyyy-mm-dd hh:mm:ss
            metadata["create"] = create_time.strftime('%Y-%m-%d %H:%M:%S')
            metadata["updated"] = update_time.strftime('%Y-%m-%d %H:%M:%S')
            metadata["ACL"] = access_control
            metadata["owner"] = caller_address
            own_list.append(metadata)

        else:
            ACL = get_ACL(caller_address)
            if(ACL["status"] <= 0):
                return {"status":0,"output":ACL["output"]}
            
            ACL = ACL["output"]
            if('r' in ACL):
                metadata = get_metadata(caller_address)
                if(metadata["status"] <= 0):
                    return {"status":0,"output":metadata["output"]}
            
                metadata = metadata["output"]
                create_time = datetime.datetime.utcfromtimestamp(metadata["create"])
                update_time = datetime.datetime.utcfromtimestamp(metadata["updated"])
                # Format the datetime object as yyyy-mm-dd hh:mm:ss
                metadata["create"] = create_time.strftime('%Y-%m-%d %H:%M:%S')
                metadata["updated"] = update_time.strftime('%Y-%m-%d %H:%M:%S')
                metadata["ACL"] = ACL
                share_list.append(metadata)

    return {"status":1,
            "output":{"own_list":own_list,"share_list":share_list}}

def get_log_data(caller_address):
    global file_contract
    output = []
    tx = file_contract.functions.get_log().call({"from":caller_address})

    for log in tx:
        event_time = datetime.datetime.utcfromtimestamp(log[0])
        event_time = event_time.strftime('%Y-%m-%d %H:%M:%S')
        output.append([event_time, log[1], log[2]])

    return {"status": 1, "output": output}

def get_balance(caller_address):
    web3 = Web3(Web3.HTTPProvider(blockchain_address))
    balance_wei = web3.eth.get_balance(caller_address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return {"status":1,"output":balance_eth}