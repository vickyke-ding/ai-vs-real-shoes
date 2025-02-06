from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import json
import os

app = Flask(__name__)
CORS(app)

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

# 确保 responses.json 存在
if not os.path.exists(responses_file):
    with open(responses_file, "w") as f:
        json.dump([], f)

# 读取已有的 responses.json（避免重启时数据丢失）
with open(responses_file, "r") as f:
    responses = json.load(f)

@app.route('/')
def home():
    return "Flask server is running on Render!"

@app.route('/get_image', methods=['GET'])
def get_image():
    if not shoes:
        return jsonify({"error": "No images found"}), 500
    shoe = random.choice(shoes)  # 随机选一张鞋子图片
    return jsonify({"image_url": shoe["url"], "label": shoe["label"]})

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    if "image_url" not in data or "choice" not in data:
        return jsonify({"error": "Invalid data"}), 400

    # 记录用户的选择
    responses.append(data)

    # 把数据存入文件
    with open(responses_file, "w") as f:
        json.dump(responses, f, indent=4)

    return jsonify({"message": "Response recorded!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # 获取 Render 端口
    app.run(host='0.0.0.0', port=port)  # 绑定 0.0.0.0 让外部可访问
