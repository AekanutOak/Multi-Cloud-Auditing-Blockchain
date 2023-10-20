from flask import (
    Flask, 
    request, 
)

from Crypto.Hash import SHA256
from hashlib import sha256

import contract_interface

import json
import os
import random
import requests

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)

with open(os.path.join(current_path,"./config.json"),"r") as f:
    config = json.loads(f.read())

with open(os.path.join(current_path,"./csp_list.json"),"r") as f:
    address = json.loads(f.read())

CSP_1_URL = "http://"+config["CSP-1"]["host"]+":"+str(config["CSP-1"]["port"])
CSP_2_URL = "http://"+config["CSP-2"]["host"]+":"+str(config["CSP-2"]["port"])
CSP_3_URL = "http://"+config["CSP-3"]["host"]+":"+str(config["CSP-3"]["port"])
CSP_list = [CSP_1_URL,CSP_2_URL,CSP_3_URL]

with open(os.path.join(current_path,"./csp_list.json"),"r") as f:
    address = json.loads(f.read())
organizer_address = address["organizer"]

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from organizer"

@app.route("/download", methods=["POST"])
def download():

    with open(os.path.join(current_path,"./organizer_data/file_track.json"),"r") as f:
        file_track = json.loads(f.read())

    data = request.get_json()

    file_ID = sha256((data["filename"]+data["account_address"]).encode()).hexdigest()
    block_locations = file_track[file_ID]["blocks"]
    number_of_block = len(block_locations)

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

    file_merge = b""
    for i in range(number_of_block):
        file_merge += (file[f"block{i}"]).encode("latin-1")
        
        # To reduce storage complexity, remove each block after concat
        del file[f"block{i}"]

    return {"status":1,"output":{"file_data":file_merge.decode("latin-1"),"file_ID":file_ID}}


@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    filename = data["filename"]
    file_ID = data["file_ID"]
    file_desc = data["file_desc"]
    file_owner = data["account_address"]
    filesize = data["filesize"]
    data = data["file_blocks"]
    access_control = {file_owner:"rw",organizer_address:"o-"}

    with open(os.path.join(current_path,"./organizer_data/file_track.json"),"r") as f:
        file_track = json.loads(f.read())

    if(file_ID in file_track):
        return {"status":0,"output":"File is duplicated"}
    
    file_track[file_ID] = {
        "filename":filename,
        "ID":file_ID,
        "desc":file_desc,
        "owner":file_owner,
        "size":filesize,
        "ACL":access_control,
        "blocks":{}
    }

    CSP_distribute = [{file_ID:{}},{file_ID:{}},{file_ID:{}}]
    for i in range(len(data)):
        CSP_choice = random.choice([0,1,2])
        CSP_distribute[CSP_choice][file_ID][f"block{i}"] = data[i]
        file_track[file_ID]["blocks"][f"block{i}"] = CSP_list[CSP_choice]    
    
    with open(os.path.join(current_path,"./organizer_data/file_track.json"),"w") as f:
        json.dump(file_track,f,indent=4)

    print("update file track on organizer successfully")

    for i in range(len(CSP_list)):
        response = requests.post(
                CSP_list[i]+"/upload", 
                json={"data":CSP_distribute[i]}
        )

        print(f"distribute file to CSP-{i} successfully")
    
    return {"status":1,"output":"success"}

@app.route("/challenge", methods=["POST"])
def challenge():
    global organizer_address

    data = request.get_json()
    file_ID = data["file_ID"]

    with open(os.path.join(current_path,"./contract_list.json"),"r") as f:
        contract_list = json.loads(f.read())

    contract_address = contract_list[file_ID]
    contract_interface.select_contract(file_ID,contract_address)
    challenge = contract_interface.get_challenge(organizer_address)["output"]

    print("recieve challenge ",challenge)
    with open(os.path.join(current_path,"./organizer_data/file_track.json"),"r") as f:
        file_track = json.loads(f.read())

    block_locations = file_track[file_ID]["blocks"]
    temp_dict = {}
    for i in challenge:
        temp_dict[f"block{i}"] = block_locations[f"block{i}"]

    block_locations = temp_dict
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

    block_locations = []
    for i in range(len(challenge)):
        data = file[f"block{challenge[i]}"]
        data = data.encode("latin-1")
        data = SHA256.new(data)
        block_locations.append(data.hexdigest())

    contract_interface.submit_response(organizer_address,block_locations)
    return {"status":1,"output":"submit response"}

if __name__ == '__main__':
    print("Starting on ip "+config["Organizer"]["host"])
    print()

    app.run(debug=True,host=config["Organizer"]["host"],port=config["Organizer"]["port"])

