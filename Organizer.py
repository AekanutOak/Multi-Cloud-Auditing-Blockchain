from flask import Flask, request, render_template, redirect, url_for
import os, json, requests

# Prevent relative path error when working with other local computers
current_path = os.path.dirname(__file__)
config_path = os.path.join(current_path,"config.json")

with open(config_path,"r") as f:
    config = json.loads(f.read())

CSP_1_URL = "http://"+config["CSP-1"]["host"]+":"+str(config["CSP-1"]["port"])
CSP_2_URL = "http://"+config["CSP-2"]["host"]+":"+str(config["CSP-2"]["port"])
CSP_3_URL = "http://"+config["CSP-3"]["host"]+":"+str(config["CSP-3"]["port"])

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from organizer"

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']

    if file.filename == '':
        return "No selected file"
    
    if file:
        response = requests.post(
            CSP_1_URL+"/upload", 
            files={'file': (file.filename, file)}
        )

        if response.status_code == 200:
            return "File uploaded successfully to CSP-1"
        else:
            return "Failed to upload file to CSP-1", 500
    
if __name__ == '__main__':
    print("Starting on ip "+config["Organizer"]["host"])
    print()

    app.run(debug=True,host=config["Organizer"]["host"],port=config["Organizer"]["port"])

