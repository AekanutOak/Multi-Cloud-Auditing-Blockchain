import os, json
from flask import Flask, request, send_from_directory

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
storage_folder = os.path.join(current_path,"CSP-3")

config_path = os.path.join(current_path,"../config.json")

with open(config_path,"r") as f:
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
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']

    if file.filename == '':
        return "No selected file"
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        return "File uploaded successfully"
    
if __name__ == '__main__':

    print("Starting on ip "+config["host"])
    print()

    app.run(
        debug = True,
        port = config['port'],
        host = config['host']    
    )