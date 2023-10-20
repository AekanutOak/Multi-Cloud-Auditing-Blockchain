from web3 import Web3
import json, random, os
import shutil
from Crypto.PublicKey import RSA

# The network address that the program will connect is stored in file
# Please change to content of that file to change the network address
current_path = os.path.dirname(__file__)

with open(os.path.join("./utils/config.json"),"r") as f:
    config = json.loads(f.read())["Blockchain"]

    if(config["access_mode"] == "by_ip"):
        blockchain_address = config["protocol"]+"://"+config["ip"]+":"+str(config["port"])

    else:
        blockchain_address = config["protocol"]+"://"+config["domain"]+":"+str(config["port"])

web3 = Web3(Web3.HTTPProvider(blockchain_address))
addresses = web3.eth.accounts

shutil.rmtree(os.path.join(current_path,"./abi"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"./abi"))  # Create the directory

shutil.rmtree(os.path.join(current_path,"./utils/organizer_data"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"./utils/organizer_data"))  # Create the directory

with open(os.path.join(current_path,"./utils/contract_list.json"),"w") as f:
    json.dump({},f)

with open(os.path.join(current_path,"./utils/organizer_data/file_track.json"),"w") as f:
    json.dump({},f)

shutil.rmtree(os.path.join(current_path,"./CSP/CSP-1"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"./CSP/CSP-1"))  # Create the directory

shutil.rmtree(os.path.join(current_path,"./CSP/CSP-2"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"./CSP/CSP-2"))  # Create the directory

shutil.rmtree(os.path.join(current_path,"./CSP/CSP-3"), ignore_errors=True)  # Remove the directory if it exists
os.mkdir(os.path.join(current_path,"./CSP/CSP-3"))  # Create the directory

with open(os.path.join(current_path,"./CSP/CSP-1/file_track.json"),"w") as f:
    json.dump({},f)

with open(os.path.join(current_path,"./CSP/CSP-2/file_track.json"),"w") as f:
    json.dump({},f)

with open(os.path.join(current_path,"./CSP/CSP-3/file_track.json"),"w") as f:
    json.dump({},f)

user_list = {}

for i, address in enumerate(addresses):
    directory_name = f"user{i+1}"
    shutil.rmtree(os.path.join(current_path,directory_name), ignore_errors=True)  # Remove the directory if it exists
    os.mkdir(os.path.join(current_path,directory_name))  # Create the directory


    # Generate a new RSA key pair with a key size of 2048 bits
    key = RSA.generate(2048)

    # Extract the private and public keys
    private_key = key.export_key()
    public_key = key.publickey().export_key()

    # Save private and public keys to files
    private_key_file_path = os.path.join(directory_name, "private_key.pem")
    public_key_file_path = os.path.join(directory_name, "public_key.pem")

    # Save the keys to files or use them as needed
    with open(private_key_file_path, "wb") as private_key_file:
        private_key_file.write(private_key)

    with open(public_key_file_path, "wb") as public_key_file:
        public_key_file.write(public_key)


    user_list[address] = f"user{i+1}"

with open(os.path.join(current_path,"./utils/user_list.json"),"w") as f:
    json.dump(user_list,f,indent=4)

with open(os.path.join(current_path,"./utils/csp_list.json"),"w") as f:
    json.dump({},f)

addresses = addresses[len(addresses)-3:len(addresses)]

csp_list = {}
csp_list["organizer"] = addresses[len(addresses)-4]
for i in range(len(addresses)):
    csp_list[f"CSP-{i}"] = addresses[i]

with open(os.path.join(current_path,"./utils/csp_list.json"),"w") as f:
    json.dump(csp_list,f,indent=4)
    