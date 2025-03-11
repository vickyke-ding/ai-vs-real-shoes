from flask import Flask, request, jsonify
from google.cloud import vision
from google.oauth2 import service_account
from flask_cors import CORS
import random
import json
import os
import base64

app = Flask(__name__)
CORS(app)

# Load Google credentials and setup the Vision API client
key_path = 'google-credentials.json'
key_json = base64.b64decode(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_BASE64'))
with open(key_path, "w") as key_file:
    key_file.write(key_json.decode('utf-8'))
credentials = service_account.Credentials.from_service_account_file(key_path)
client = vision.ImageAnnotatorClient(credentials=credentials)

# Load shoe images URLs from files
with open("ai_urls.txt", "r") as f, open("real_urls.txt", "r") as fr:
    ai_shoes = [{"url": line.strip(), "label": "AI"} for line in f.readlines()]
    real_shoes = [{"url": line.strip(), "label": "Real"} for line in fr.readlines()]
shoes = ai_shoes + real_shoes

# Load or initialize responses data
responses_file = "responses.json"
if not os.path.exists(responses_file):
    responses = []
else:
    with open(responses_file, "r") as f:
        responses = json.load(f)

@app.route('/')
def home():
    return "Flask server is running on Render!"

@app.route('/get_image', methods=['GET'])
def get_image():
    if not shoes:
        return jsonify({"error": "No images found"}), 500
    return jsonify(random.choice(shoes))

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    if "image_url" not in data or "choice" not in data:
        return jsonify({"error": "Invalid data"}), 400
    responses.append(data)
    with open(responses_file, "w") as f:
        json.dump(responses, f, indent=4)
    return jsonify({"message": "Response recorded!"})

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    image_url = request.json.get("image_url")
    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400
    image = vision.Image(source=vision.ImageSource(image_uri=image_url))
    response = client.label_detection(image=image)
    labels = [label.description for label in response.label_annotations]
    return jsonify({"image_url": image_url, "labels": labels})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
