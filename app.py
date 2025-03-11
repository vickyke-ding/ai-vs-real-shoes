from flask import Flask, request, jsonify
from google.cloud import vision
from flask_cors import CORS
import random
import os
import base64
from google.oauth2 import service_account
import json

app = Flask(__name__)
CORS(app)

# 检查是否在本地运行
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64"):
    print("🔹 Running in Render: Decoding Base64 credentials...")

    # 解码 Base64 环境变量
    key_path = "google-credentials.json"
    with open(key_path, "w") as key_file:
        key_json = base64.b64decode(os.environ["GOOGLE_APPLICATION_CREDENTIALS_BASE64"])
        key_file.write(key_json.decode('utf-8'))
else:
    print("🔹 Running locally: Using local credentials file...")

    # 本地运行，直接使用 JSON 文件
    key_path = r"E:\CSE598\NUSCENCE\cse598-453406-dcdc34361783.json"

# 确保 JSON 文件存在
if not os.path.exists(key_path):
    raise FileNotFoundError(f"❌ Credentials file not found: {key_path}")

# 读取 Google Cloud 凭据
credentials = service_account.Credentials.from_service_account_file(key_path)
client = vision.ImageAnnotatorClient(credentials=credentials)

print("✅ Google Cloud Vision API Initialized Successfully!")

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

    if not data:
        return jsonify({"error": "No data received"}), 400

    try:
        # 🚀 解析用户评分数据
        shadow = int(data.get('shadow', 5))
        content = int(data.get('content', 5))
        texture = int(data.get('texture', 5))
        physics = int(data.get('physics', 5))
        image_url = data.get("image_url")

        print(f"✅ Received scores: Shadow={shadow}, Content={content}, Texture={texture}, Physics={physics}")

        feedback_list = []

        # **🔹 Step 1: 评分分析反馈**
        if shadow < 4:
            feedback_list.append("🕶️ Shadows look unrealistic or misaligned. AI-generated images often struggle with shadow consistency.")
        elif shadow > 8:
            feedback_list.append("✅ Shadows look natural with proper gradation. This suggests real-world lighting.")

        if content < 4:
            feedback_list.append("📸 The context of the shoe appears strange or inconsistent. AI-generated shoes sometimes have unusual backgrounds or missing details.")
        elif content > 8:
            feedback_list.append("✅ The shoe's context looks realistic, with logical placement in the image.")

        if texture < 4:
            feedback_list.append("🧐 The shoe texture appears too smooth or inconsistent. AI-generated textures often lack fine details like stitching, scuffs, or reflections.")
        elif texture > 8:
            feedback_list.append("✅ The material representation looks great! High-quality textures with natural imperfections usually indicate a real photo.")

        if physics < 4:
            feedback_list.append("⚠️ The shoe does not obey physical rules, like gravity or surface interaction. AI often struggles with how objects cast shadows and interact with surfaces.")
        elif physics > 8:
            feedback_list.append("✅ The physics of the shoe look realistic! The shoe correctly follows natural forces like gravity and pressure.")

        # **🔹 Step 2: 调用 Google Vision API 进行 AI 识别**
        if image_url:
            try:
                image = vision.Image()
                image.source.image_uri = image_url
                response = client.label_detection(image=image)
                labels = response.label_annotations

                # 提取 Google 识别的主要标签，并按置信度排序
                label_data = sorted(
                    [{"description": label.description, "score": label.score} for label in labels],
                    key=lambda x: x["score"],
                    reverse=True
                )

                print(f"🖼️ Vision API Labels: {label_data}")

                # **🔍 Step 3: 结合 Vision 结果进行 AI 检测**
                ai_related_keywords = ["CGI", "Artificial", "Fake", "Generated", "Illustration"]
                ai_detected = any(label["description"] in ai_related_keywords for label in label_data)

                if ai_detected:
                    feedback_list.append("⚠️ Google AI detected potential AI-generated content.")
                else:
                    # **✅ 更详细的“真实照片”分析**
                    if label_data:
                        top_label = label_data[0]  # 取置信度最高的标签
                        feedback_list.append(
                            f"✅ Google AI identified this as a real photo because it strongly matches '{top_label['description']}' "
                            f"with a confidence of {top_label['score']:.2f}."
                        )
                    else:
                        feedback_list.append("✅ Google AI identified this as a real photo, but no dominant label was detected.")

            except Exception as e:
                feedback_list.append(f"⚠️ Error analyzing image with AI: {str(e)}")

        # **🔹 Step 4: 额外的教育性建议**
        educational_tips = []
        if shadow < 4:
            educational_tips.append("💡 Tip: In real photos, shadows should match the light source. If you see inconsistent shadows, it's likely AI-generated.")
        if texture < 4:
            educational_tips.append("💡 Tip: AI-generated textures often lack wear and tear, reflections, or fine details like stitching. Look closely!")
        if physics < 4:
            educational_tips.append("💡 Tip: Check if the object interacts naturally with the surface it's on. AI sometimes creates floating or distorted objects.")

        feedback_list.extend(educational_tips)

        # **🔹 Step 5: 返回最终反馈**
        if not feedback_list:
            feedback_list.append("🤔 No major issues detected. Looks fine!")

        return jsonify({"feedback": feedback_list})

    except ValueError:
        return jsonify({"error": "Invalid input: Scores must be numbers."}), 400


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

        label_data = [{"description": label.description, "score": label.score} for label in labels]

        # 额外分析 AI 可能性
        ai_related_keywords = ["CGI", "Artificial", "Fake", "Generated", "Illustration"]
        ai_confidence = any(label["description"] in ai_related_keywords for label in label_data)

        return jsonify({
            "image_url": image_url,
            "labels": label_data,
            "ai_detected": ai_confidence
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
