import os, json
from flask import Flask, request, send_from_directory

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
storage_folder = os.path.join(current_path,"CSP-3")

with open(os.path.join(current_path,"../utils/config.json"),"r") as f:
    config = json.loads(f.read())["CSP-3"]

# Check if folder is missing, then create a new one instead
if not os.path.exists(storage_folder):
    os.makedirs(storage_folder)


app = Flask(__name__)

# Register the upload folder name when recieve from http transmission
app.config['UPLOAD_FOLDER'] = storage_folder

@app.route('/')
def index():
    return "Welcome to CSP-3"

@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.get_json()["data"]

    with open(os.path.join(current_path,"./CSP-3/file_track.json"),"r") as f:
        file_track = json.loads(f.read())

    file_track.update(data)

    with open(os.path.join(current_path,"./CSP-3/file_track.json"),"w") as f:
        json.dump(file_track,f,indent=4)
    
    return {"status":1,"output":"success"}
    
@app.route('/download',methods=["POST"])
def download_file():
    data = request.get_json()
    file_ID = data["file_ID"]
    block_list = data["block_list"]
    temp_dict = {}

    with open(os.path.join(current_path,"./CSP-3/file_track.json"),"r") as f:
        file_track = json.loads(f.read())

    for i in block_list:
        temp_dict[f"block{i}"] = file_track[file_ID][f"block{i}"]

    return {"status":1,"output":temp_dict}

if __name__ == '__main__':
    print("Starting on ip "+config["host"])
    print()
    
    app.run(
        debug = True,
        port = config['port'],
        host = config['host']    
    )