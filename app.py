from flask import Flask, request, jsonify
from google.cloud import vision
from google.oauth2 import service_account
from flask_cors import CORS
import random
import json
import os
import base64
from google.oauth2 import service_account
import json

# Decode the base64 environment variable to JSON
key_path = 'google-credentials.json'
with open(key_path, "w") as key_file:
    key_json = base64.b64decode(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_BASE64'))
    key_file.write(key_json.decode('utf-8'))

# Use the credentials file in your application
credentials = service_account.Credentials.from_service_account_file(key_path)

app = Flask(__name__)
CORS(app)

# 请确保你的环境变量已经设置正确的路径或直接在这里指定服务账号密钥的路径
service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not service_account_key_path:
    raise ValueError("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set or incorrect.")

# 从服务账号文件创建认证信息
credentials = service_account.Credentials.from_service_account_file(service_account_key_path)
client = vision.ImageAnnotatorClient(credentials=credentials)

# 读取 GitHub 托管的 AI 生成鞋子 URL
with open("ai_urls.txt", "r") as f:
    ai_shoes = [{"url": line.strip(), "label": "AI"} for line in f.readlines() if line.strip()]

# 读取 GitHub 托管的真实鞋子 URL
with open("real_urls.txt", "r") as f:
    real_shoes = [{"url": line.strip(), "label": "Real"} for line in f.readlines() if line.strip()]

# 合并所有鞋子数据
shoes = ai_shoes + real_shoes

# 存储用户提交的数据
responses_file = "responses.json"
if not os.path.exists(responses_file):
    with open(responses_file, "w") as f:
        json.dump([], f)

# 在应用启动时读取响应文件，如果文件不存在或为空则初始化为空列表
if os.path.exists(responses_file):
    with open(responses_file, "r") as f:
        try:
            responses = json.load(f)
        except json.JSONDecodeError:
            responses = []
else:
    responses = []

@app.route('/')
def home():
    return "Flask server is running on Render!"

@app.route('/get_image', methods=['GET'])
def get_image():
    if not shoes:
        return jsonify({"error": "No images found"}), 500
    shoe = random.choice(shoes)
    return jsonify({"image_url": shoe["url"], "label": shoe["label"]})

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    if "image_url" not in data or "choice" not in data:
        return jsonify({"error": "Invalid data"}), 400

    responses.append(data)
    with open(responses_file, "w") as f:
        json.dump(responses, f, indent=4)

    return jsonify({"message": "Response recorded!"})

@app.route('/evaluate_scores', methods=['POST'])
def evaluate_scores():
    data = request.json
    # Extracting individual scores from the request
    shadow = data.get('shadow', 5)  # Providing default values in case any are missing
    content = data.get('content', 5)
    texture = data.get('texture', 5)
    physics = data.get('physics', 5)

    # Here you might add logic to adjust your AI's behavior based on these scores
    # For example, adjusting the confidence threshold or focusing on certain features

    # Simulate a response or commentary based on the scores
    # In a real scenario, this could be more complex, based on AI analysis
    feedback = f"Received scores - Shadow: {shadow}, Content: {content}, Texture: {texture}, Physics: {physics}"
    return jsonify({"comment": feedback})

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    data = request.json
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    try:
        image = vision.Image()
        image.source.image_uri = image_url
        response = client.label_detection(image=image)
        labels = response.label_annotations
        descriptions = [label.description for label in labels]

        return jsonify({"image_url": image_url, "labels": descriptions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
