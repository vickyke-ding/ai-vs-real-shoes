from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import json

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
responses = []

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

    # 可选：把数据存入文件
    with open("responses.json", "w") as f:
        json.dump(responses, f, indent=4)

    return jsonify({"message": "Response recorded!"})

if __name__ == '__main__':
    app.run(debug=True)
