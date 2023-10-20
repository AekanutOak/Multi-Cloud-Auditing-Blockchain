from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request
)

from hashlib import sha256

import contract_deploy as smart_contract
import contract_interface

import json
import math
import os
import random
import requests

def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    return ciphertext

def decrypt_data(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    unpadded_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return unpadded_data

def split_data(data, num_blocks):
    # Calculate the block size
    data_length = len(data)
    block_size = (data_length + num_blocks - 1) // num_blocks

    # Split the encrypted data into blocks
    parts = [data[i:i + block_size] for i in range(0, data_length, block_size)]

    return parts

def generate_tags(blocks, private_key):
    tags = []
    cipher = pkcs1_15.new(private_key)

    for block in blocks:
        # Calculate the SHA-256 hash of the block
        block_hash = SHA256.new(block).hexdigest()

        # Encrypt the hash and get a binary tag
        # tag = cipher.sign(bytes.fromhex(block_hash))
        
        tags.append(block_hash)

    return tags

def verify_tag(data, received_tag, public_key):
    # Create a cipher object with PKCS1 OAEP padding
    cipher = pkcs1_15.new(public_key)
    if(data == received_tag):
        return True
    return False

current_path = os.path.dirname(__file__)

with open(os.path.join(current_path,"./csp_list.json"),"r") as f:
    address = json.loads(f.read())
    
with open(os.path.join(current_path,"./config.json"),"r") as f:
    config = json.loads(f.read())
    
with open(os.path.join(current_path,"./user_list.json"), "r") as f:
    user_list = json.loads(f.read())

organizer_address = address["organizer"]
organizer_URL = "http://"+config["Organizer"]["host"]+":"+str(config["Organizer"]["port"])

account_address = None
balance = None
username = None
status_upload = None

app = Flask(__name__)

@app.route("/")
def metamask_login():
    return render_template("landing.html")

@app.route('/authenticate', methods=['POST'])
def authenticate():
    global account_address, username, balance

    # Get the Ethereum address from the JSON data in the request body
    data = request.get_json()
    account_address = data.get('userAddress')
    balance = contract_interface.get_balance(account_address)["output"]
    username = user_list[account_address]
    print(f"Login with username {username}")
    return jsonify({'message': 'Authentication successful'})

    
@app.route('/index.html')
def index():
    global status_upload

    file_list = contract_interface.get_file_list(account_address)
    own_list = file_list["output"]["own_list"]
    share_list = file_list["output"]["share_list"]

    if(status_upload != None):
        status = status_upload["output"]
        status_upload = None
        return render_template('index.html',account_address=account_address,own_list=own_list,share_list=share_list,msg=status,balance=balance)

    return render_template('index.html',account_address=account_address,own_list=own_list,share_list=share_list,balance=balance)

@app.route('/upload', methods=['POST'])
def upload():

    global account_address
    global status_upload
    global username

    file = request.files['file']
    description = request.form.get('description')

    if file.filename == '':
        return "No selected file"
    
    if file:

        filename = file.filename
        file.seek(0, 2) 
        filesize = file.tell()
        file.seek(0) 
        file_ID = sha256((filename+account_address).encode()).hexdigest()

        with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
            contract_list = json.load(f)

        if(file_ID in contract_list):
            return {"status":0,"output":"Filename is duplicated"}

        with open(os.path.join(current_path,f'../{username}/private_key.pem'), 'rb') as key_file:
            private_key = RSA.import_key(key_file.read())

        # Load the public key
        with open(os.path.join(current_path,f'../{username}/public_key.pem'), 'rb') as key_file:
            public_key = RSA.import_key(key_file.read())

        sym_key = get_random_bytes(32)
        file = encrypt_data(file.read(),sym_key)

        print("Encrypt file successfully")
        blocks = split_data(file, 10)

        
        # Create a cipher object with PKCS1 OAEP padding
        cipher = PKCS1_OAEP.new(public_key)
        ciphertext = cipher.encrypt(sym_key).decode("latin-1")
        print("Encrypt symmetric key successfully")
        # Generate tags for each block and store them in a list
        tags = generate_tags(blocks, private_key)

        smart_contract.deploy_contract(
            account_address,
            tags,
            filename,
            description,
            ciphertext,
            filesize
        )
        
        blocks = [block.decode("latin-1") for block in blocks]
        
        data = {
            "file_blocks":blocks,
            "filename":filename,
            "file_ID":file_ID,
            "file_desc":description,
            "account_address":account_address,
            "filesize":filesize
        }

        print("Deploy contract successfully")
        response = requests.post(
            organizer_URL+"/upload", 
            json=data
        )

        with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
            contract_list = json.load(f)
            
        contract_interface.select_contract(file_ID,contract_list[file_ID])
        contract_interface.assign_ACL(account_address,[organizer_address],["o-"])

        if response.status_code == 200:

            status_upload = {"status":1,"output":"upload successfully"}
            owner_address = account_address
            file_ID = sha256((filename+owner_address).encode()).hexdigest()

            with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
                contract_list = json.load(f)

            block_list = [i for i in range(len(blocks))]

            contract_address = contract_list[file_ID]
            contract_interface.select_contract(file_ID,contract_address)
            contract_interface.submit_challenge(account_address,block_list)

            print("submit challenge ",block_list)
            response = requests.post(organizer_URL+"/challenge",json={"file_ID":file_ID})
            response = contract_interface.get_response(account_address)["output"]
            username = user_list[account_address]

            with open(os.path.join(current_path,f'../{username}/public_key.pem'), 'rb') as key_file:
                public_key = RSA.import_key(key_file.read())

            tamper_list = []
            tags = contract_interface.get_tags(account_address,block_list)["output"]

            for i in range(len(response)):
                result = verify_tag((response[i]),(tags[i]),public_key)
                if(not result):
                    tamper_list.append(f"block{block_list[i]}")
                    
            if(tamper_list):
                return {"status":1,"output":"file is tampered"}
            else:
                return redirect("/index.html")

        else:
            status_upload = {"status":0,"output":"fail to upload"}
            return redirect("/index.html")
        
@app.route('/download', methods=['POST'])
def download():
    global account_address
    data = request.get_json()

    print(data["owner_address"])
    response = requests.post(
        organizer_URL+"/download", 
        json={"filename":data["filename"],"account_address":data["owner_address"]} 
    )

    file_ID = response.json()["output"]["file_ID"]
    response = response.json()["output"]["file_data"]

    print("Aggegrate all data blocks successfully")

    with open(os.path.join(current_path,"./contract_list.json"),"r") as f:
        contract_list = json.loads(f.read())

    contract_interface.select_contract(contract_list[file_ID],file_ID)
    print("Retrieve contract for the file successfully")
    enc_sym_key = contract_interface.get_key(account_address)["output"].encode("latin-1")
    print("Retrieve sym key successfully")

    with open(os.path.join(current_path,"./user_list.json"), "r") as f:
        user_list = json.loads(f.read())

    username = user_list[account_address]

    with open(os.path.join(current_path,f'../{username}/private_key.pem'), 'rb') as key_file:
        private_key = RSA.import_key(key_file.read())

    # Create a cipher object with PKCS1 OAEP padding
    cipher = PKCS1_OAEP.new(private_key)
    sym_key = cipher.decrypt(enc_sym_key)
    print("Decrypt symmetric key with private key successfully")

    plaintext = decrypt_data(response.encode("latin-1"),sym_key)
    with open(f"./{username}/{data['filename']}","wb") as f:
        f.write(plaintext)

    print("Save file successfully")
    return {"status":1,"output":"success"}

@app.route("/view_log",methods=["POST"])
def view_log():
    global account_address
    data = request.get_json()
    filename = data["filename"]
    file_ID = sha256((filename+account_address).encode()).hexdigest()
    with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
        contract_list = json.load(f)

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(contract_address,file_ID)
    log = contract_interface.get_log_data(account_address)
    return {"status":log["status"],"output":log["output"]}

@app.route("/view_ACL",methods=["POST"])
def view_ACL():
    global account_address
    data = request.get_json()
    filename = data["filename"]
    file_ID = sha256((filename+account_address).encode()).hexdigest()
    with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
        contract_list = json.load(f)

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(contract_address,file_ID)
    ACL = contract_interface.get_all_ACL()
    return {"status":ACL["status"],"output":ACL["output"]}

@app.route("/revoke",methods=["POST"])
def revoke():
    global account_address

    data = request.get_json()
    filename = data["filename"]
    user_address = data["user_address"]
    
    print("revoke ", user_address)
    file_ID = sha256((filename+account_address).encode()).hexdigest()
    with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
        contract_list = json.load(f)

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(contract_address,file_ID)
    contract_interface.revoke_users(account_address,[user_address])

    return redirect("index.html")

@app.route("/assign_ACL",methods=["POST"])
def assign_ACL():
    filename = request.form.get('filename')
    caller_address = request.form.get("owner_address")
    ACLs = request.form.get("ACL")
    user_address = request.form.get("user_address")
    file_ID = sha256((filename+caller_address).encode()).hexdigest()

    if(caller_address == user_address):
        return redirect("index.html")

    with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
        contract_list = json.load(f)

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(contract_address,file_ID)
    contract_interface.assign_ACL(caller_address,[user_address],[ACLs])
    return redirect("index.html")

@app.route('/audit', methods=['POST'])
def audit():
    global account_address, username

    data = request.form
    filename = data.get("filename")
    owner_address = data.get("owner_address")
    blocks = int(data.get("blocks"))
    threshold = int(data.get("threshold"))
    file_ID = sha256((filename+owner_address).encode()).hexdigest()

    with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
        contract_list = json.load(f)

    threshold = math.ceil((threshold / 100) * blocks)
    block_list = [i for i in range(blocks)]
    block_list = random.sample(block_list, k=threshold)

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(file_ID,contract_address)
    contract_interface.submit_challenge(account_address,block_list)

    print("submit challenge ",block_list)
    response = requests.post(organizer_URL+"/challenge",json={"file_ID":file_ID})
    response = contract_interface.get_response(account_address)["output"]
    username = user_list[account_address]

    with open(os.path.join(current_path,f'../{username}/public_key.pem'), 'rb') as key_file:
        public_key = RSA.import_key(key_file.read())

    tamper_list = []
    tags = contract_interface.get_tags(account_address,block_list)["output"]

    for i in range(len(response)):
        result = verify_tag((response[i]),(tags[i]),public_key)
        print(result)
        if(not result):
            tamper_list.append(f"block{block_list[i]}")
        
    if(tamper_list):
        return {"status":0,"output":tamper_list}
    
    return {"status":1,"output":tamper_list}


    
if __name__ == '__main__':
    print("Starting on ip "+config["Client"]["host"])
    print()

    app.run(debug=True,host=config["Client"]["host"],port=config["Client"]["port"])

