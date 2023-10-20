from flask import Flask, request, render_template, redirect, url_for, jsonify
import os, json, requests
import contract_interface
from hashlib import sha256
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def verify_signature(message, signature, public_key):
    # Load the public key
    # Calculate the SHA-256 hash of the message
    digest = hashes.Hash(hashes.SHA256())
    digest.update(message)
    message_hash = digest.finalize()

    # Verify the signature
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True  # Signature is valid
    except:
        return False  # Signature is not valid


current_path = os.path.dirname(__file__)

contract_interface.select_contract("7efe22227f220824fa222b5262f9f96bd4827b20e5fb249c92949c4b7ac9dab2","0x2eba1C85D6B28c871c3E3dfDbf77C19dD5B2E020")

with open(os.path.join(current_path,"./organizer_data/file_track.json"),"r") as f:
    file_track = json.loads(f.read())

with open(os.path.join(current_path,"./config.json"),"r") as f:
    config = json.loads(f.read())


file_ID = "7efe22227f220824fa222b5262f9f96bd4827b20e5fb249c92949c4b7ac9dab2"
block_locations = file_track[file_ID]["blocks"]
temp_dict = {}
challenge = [0,1,2,3,4]
for i in challenge:
    temp_dict[f"block{i}"] = block_locations[f"block{i}"]

block_locations = temp_dict
CSP_1_URL = "http://"+config["CSP-1"]["host"]+":"+str(config["CSP-1"]["port"])
CSP_2_URL = "http://"+config["CSP-2"]["host"]+":"+str(config["CSP-2"]["port"])
CSP_3_URL = "http://"+config["CSP-3"]["host"]+":"+str(config["CSP-3"]["port"])
CSP_list = [CSP_1_URL,CSP_2_URL,CSP_3_URL]

CSP_1 = []
CSP_2 = []
CSP_3 = []

for key,value in block_locations.items():
    if(value == CSP_1_URL):
        CSP_1.append(int(key.replace("block","")))

    if(value == CSP_2_URL):
        CSP_2.append(int(key.replace("block","")))

    if(value == CSP_3_URL):
        CSP_3.append(int(key.replace("block","")))

file = {}

response = requests.post(
        CSP_1_URL+"/download", 
        json={"file_ID":file_ID,"block_list":CSP_1}
    )

file.update(response.json()["output"])

response = requests.post(
    CSP_2_URL+"/download", 
    json={"file_ID":file_ID,"block_list":CSP_2}
)

file.update(response.json()["output"])

response = requests.post(
    CSP_3_URL+"/download", 
    json={"file_ID":file_ID,"block_list":CSP_3}
)

file.update(response.json()["output"])

tags = contract_interface.get_tags("0x42e64601c3b06C9A72ac62bEd67D830b1D69b231",challenge)["output"]
tags = dict(zip(challenge,tags))

with open(os.path.join(current_path,f'../user2/public_key.pem'), 'rb') as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())

tamper_list = []
for i in challenge:
    x = verify_signature(file[f"block{i}"].encode("latin-1"),tags[i].encode("latin-1"),public_key)
    print(x)
    if(not x):
        tamper_list.append(f"block{i}")

print(tamper_list)


