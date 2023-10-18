from flask import Flask, request, render_template, redirect, url_for, jsonify
import os, json, requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import contract_interface
import contract_deploy as smart_contract

def sha256_hash(data):
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data.encode('utf-8'))  # Encode the data as bytes
    hash_value = digest.finalize()
    return hash_value

def generate_aes_key():
    key = Fernet.generate_key()
    return key

def split_data_into_blocks(file_data, num_blocks, fernet_key):
    # Encrypt the entire file data with the Fernet key
    fernet = Fernet(fernet_key)
    encrypted_data = fernet.encrypt(file_data)
    print("Encrypted successfully")
    # Calculate the block size
    data_length = len(encrypted_data)
    block_size = data_length // num_blocks

    # Split the encrypted data into blocks
    parts = []
    start = 0
    for _ in range(num_blocks):
        end = min(start + block_size, data_length)
        block_data = encrypted_data[start:end]
        parts.append(block_data)
        start = end

    print("Split successfully")
    return parts

def generate_tags(blocks, private_key):
    tags = []
    for block in blocks:
        # Calculate the SHA-256 hash of the block
        digest = hashes.Hash(hashes.SHA256())
        digest.update(block)
        block_hash = digest.finalize()

        # Sign the hash of the block
        signature = private_key.sign(
            block_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        tags.append(signature.decode("latin-1"))

    print("Generate tag successfully")
    return tags

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path,"config.json")

with open(config_path,"r") as f:
    config = json.loads(f.read())

with open(os.path.join(current_path,"./user_list.json"), "r") as f:
    user_list = json.loads(f.read())

organizer_URL = "http://"+config["Organizer"]["host"]+":"+str(config["Organizer"]["port"])
account_address = ""
username = ""

app = Flask(__name__)

@app.route("/")
def metamask_login():
    return render_template("landing.html")

@app.route('/authenticate', methods=['POST'])
def authenticate():
    global account_address, username
    try:
        # Get the Ethereum address from the JSON data in the request body
        data = request.get_json()
        account_address = data.get('userAddress')
        username = user_list[account_address]
        return jsonify({'message': 'Authentication successful'})

    except Exception as e:
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 400

@app.route('/index.html')
def index():
    file_list = contract_interface.get_file_list(account_address)
    own_list = file_list["output"]["own_list"]
    share_list = file_list["output"]["share_list"]
    return render_template('index.html',account_address=account_address,own_list=own_list,share_list=share_list)

@app.route('/upload', methods=['POST'])
def upload():

    global username,account_address

    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']

    if file.filename == '':
        return "No selected file"
    
    if file:

        filename = file.filename
        file_ID = sha256_hash(filename+account_address).hex()

        with open(os.path.join(current_path,f'./contract_list.json'), 'r') as f:
            contract_list = json.load(f)

        if(file_ID in contract_list):
            return {"status":0,"output":"Filename is duplicated"}

        with open(os.path.join(current_path,f'./{username}/private_key.pem'), 'rb') as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)

        # Load the public key
        with open(os.path.join(current_path,f'./{username}/public_key.pem'), 'rb') as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())

        # Generate AES key and use it to encrypt each block
        # Then encrypt the AES key with public key
        sym_key = generate_aes_key()
        blocks = split_data_into_blocks(file.read(), 5, sym_key)

        ciphertext = public_key.encrypt(
            sym_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode("latin-1")
        
        print("Encrypt symmetric key successfully")
        # Generate tags for each block and store them in a list
        tags = generate_tags(blocks, private_key)

        file.seek(0, 2)  # Move the file pointer to the end to get the filesize
        filesize = file.tell()
        file.seek(0)  # Reset the file pointer to the beginning for further use
        
        file_desc = "Test file"

        file_contract = smart_contract.deploy_contract(
            account_address,
            tags,
            file_ID,
            filename,
            file_desc,
            ciphertext,
            filesize
            )
        
        print("Deploy contract successfully")
        response = requests.post(
            organizer_URL+"/upload", 
            files={'file': (file.filename, file)}
        )

        if response.status_code == 200:
            return "File uploaded successfully to organizer"
        else:
            return "Failed to upload file to organizer", 500
    
if __name__ == '__main__':
    print("Starting on ip "+config["Client"]["host"])
    print()

    app.run(host=config["Client"]["host"],port=config["Client"]["port"])

