from web3 import Web3
import json, random, os
import shutil
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

# Function to generate RSA key pairs
def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key

# Function to save private key to a file
def save_private_key(private_key, file_path):
    with open(file_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

# Function to save public key to a file
def save_public_key(public_key, file_path):
    with open(file_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

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

web3 = Web3(Web3.HTTPProvider(blockchain_address))
addresses = web3.eth.accounts

shutil.rmtree(os.path.join(current_path,"abi"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"abi"))  # Create the directory

with open(os.path.join("./contract_list.json"),"w") as f:
    json.dump({},f)

user_list = {}

for i, address in enumerate(addresses):
    directory_name = f"user{i+1}"
    shutil.rmtree(os.path.join(current_path,directory_name), ignore_errors=True)  # Remove the directory if it exists
    os.mkdir(os.path.join(current_path,directory_name))  # Create the directory


    private_key = generate_rsa_key_pair()
    public_key = private_key.public_key()

    # Save private and public keys to files
    private_key_file_path = os.path.join(directory_name, "private_key.pem")
    public_key_file_path = os.path.join(directory_name, "public_key.pem")

    save_private_key(private_key, private_key_file_path)
    save_public_key(public_key, public_key_file_path)

    user_list[address] = f"user{i+1}"

with open(os.path.join("./user_list.json"),"w") as f:
    json.dump(user_list,f,indent=4)