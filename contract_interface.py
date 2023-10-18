from web3 import Web3
from web3.exceptions import ContractLogicError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import json, random, os
import datetime


# You can enable this warning later, this warning has no effect to this project
import warnings
warnings.filterwarnings("ignore")

current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path,"config.json")

with open(config_path,"r") as f:
    config = json.loads(f.read())["Blockchain"]

    if(config["access_mode"] == "by_ip"):
        blockchain_address = config["protocol"]+"://"+config["ip"]+":"+str(config["port"])

    else:
        blockchain_address = config["protocol"]+"://"+config["domain"]+":"+str(config["port"])

with open(os.path.join(current_path,"./user_list.json"), "r") as f:
    user_list = json.loads(f.read())

file_contract = ""

def initial_contract(_contract_address,_file_ID):
    global file_contract
    with open(os.path.join(current_path,f"./abi/{_file_ID}.json"),"r") as f:
        contract_abi = f.read()

    web3 = Web3(Web3.HTTPProvider(blockchain_address))
    file_contract = web3.eth.contract(address=_contract_address,abi=contract_abi)

def get_file_metadata(caller_address):
    try:
        tx = file_contract.functions.get_file_metadata().call({'from': caller_address})
        metadata = {
            "file_ID":tx[0],
            "filename":tx[1],
            "owner_address":tx[2],
            "file_desc":tx[3],
            "created_date":tx[4],
            "last_update":tx[5],
            "file_size":tx[6],
            "number_of_block":tx[7]
        }
        return {"status":1,"output":metadata}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
def get_block_tag(caller_address):
    try:
        tx = file_contract.functions.get_block_tag().call({'from': caller_address})
        return {"status":1,"output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}

def get_log_data(caller_address):
    try:
        tx = file_contract.functions.get_log_data().call({'from': caller_address})
        return {"status":1,"output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
def get_key(caller_address):
    try:
        tx = file_contract.functions.get_key().call({'from': caller_address})
        return {"status":1,"output":tx}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}

def assign_ACL(caller_address,address_list:list[str],permission_list:list[str]):
    username = user_list[caller_address]
    if(len(address_list) != len(permission_list)):
        return {"status":0,"output":"Number of address of permission does not match."}
    
    for permission in permission_list:
        if(len(permission) != 2):
            return {"status":0,"output":"Permission should be 2 length string"}
        
        if(permission not in ["r-","--","rw","-w"]):
            return {"status":0,"output":"Permission read should be r-, --, -w, or rw"}
        
        
    for address in address_list:
        if(address not in user_list):
            return {"status":0,"output":f"unknown user address {address}"}

    with open(os.path.join(current_path,f'./{username}/private_key.pem'), 'rb') as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)

    ciphertext = get_key(caller_address)

    if(ciphertext["status"] <= 0):
        return {"status":0,"output":ciphertext["output"]}
    
    ciphertext = ciphertext["output"].encode("latin-1")
    key = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    )

    key_list = []
    for address in address_list:
        username = user_list[address]
        with open(os.path.join(f'./{username}/public_key.pem'), 'rb') as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
    
        ciphertext = public_key.encrypt(
            key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        key_list.append(key.decode("latin-1"))

    try:
        tx = file_contract.functions.assign_ACL(address_list,permission_list,key_list).transact({'from': caller_address})
        return {"status":1,"output":"success to assign new ACL"}

    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}

def revoke_users(caller_address,address_list:list[str]):
    try:
        tx = file_contract.functions.revoke_users(address_list).transact({'from': caller_address})
        return {"status":1,"output":"success"}
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
def get_set_of_tag(caller_address,block_index_list:list[int]):
    try:
        tx = file_contract.functions.get_set_of_tag(block_index_list).call({"from": caller_address})
        return {"status":1,"output":tx}
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}

def custom_log(caller_address,log_data):
    try:
        tx = file_contract.functions.custom_log(log_data).transact({"from": caller_address})
        return {"status":1,"output":"success"}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}

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

def get_response(caller_address):
    try:
        tx = file_contract.functions.get_response().call({"from":caller_address})
        return {"status":1, "output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def response_to_challenge(caller_address, block_list):
    try:
        tx = file_contract.functions.response_to_challenge(block_list).transact({"from":caller_address})
        return {"status":1, "output":"success"}

    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}
    
def get_owner_address():
    tx = file_contract.functions.get_owner_address().call()
    return {"status":1,"output":tx}

def get_ACL(user_address):
    try:
        tx = file_contract.functions.get_ACL(user_address).call()
        return {"status":1,"output":tx}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}

def get_all_ACL(caller_address):
    try:
        tx = file_contract.functions.get_all_ACL().call({"from":caller_address})
        result = dict(zip(tx[0],tx[1]))
        return {"status":1,"output":result}
    
    except ValueError as e:
        return {"status":0,"output":e.args[0]["message"]}
    
    except ContractLogicError as e:
        return {"status":0,"output":e.message}

def get_file_list(caller_address):
    own_list = []
    share_list = []
    with open(os.path.join(current_path,"./contract_list.json"),"r") as f:
        contract_list = json.loads(f.read())

    for key,value in contract_list.items():
        initial_contract(value,key)
        if(get_owner_address()["output"] == caller_address):
            access_control = get_all_ACL(caller_address)

            if(access_control["status"] <= 0):
                return {"status":0,"output":access_control["output"]}
            
            access_control = access_control["output"]
            metadata = get_file_metadata(caller_address)
            if(metadata["status"] <= 0):
                return {"status":0,"output":metadata["output"]}
            
            metadata = metadata["output"]
            create_time = datetime.datetime.utcfromtimestamp(metadata["created_date"])
            update_time = datetime.datetime.utcfromtimestamp(metadata["last_update"])
            # Format the datetime object as yyyy-mm-dd hh:mm:ss
            metadata["created_date"] = create_time.strftime('%Y-%m-%d %H:%M:%S')
            metadata["last_update"] = update_time.strftime('%Y-%m-%d %H:%M:%S')
            metadata["access_control"] = access_control
            own_list.append(metadata)

        else:
            ACL = get_ACL(caller_address)
            if(ACL["status"] <= 0):
                return {"status":0,"output":ACL["output"]}
            
            ACL = ACL["output"]
            if('r' in ACL):
                metadata = get_file_metadata(caller_address)
                if(metadata["status"] <= 0):
                    return {"status":0,"output":metadata["output"]}
            
                metadata = metadata["output"]
                create_time = datetime.datetime.utcfromtimestamp(metadata["created_date"])
                update_time = datetime.datetime.utcfromtimestamp(metadata["last_update"])
                # Format the datetime object as yyyy-mm-dd hh:mm:ss
                metadata["created_date"] = create_time.strftime('%Y-%m-%d %H:%M:%S')
                metadata["last_update"] = update_time.strftime('%Y-%m-%d %H:%M:%S')
                metadata["ACL"] = ACL
                share_list.append(metadata)

    return {"status":1,
            "output":{"own_list":own_list,"share_list":share_list}}