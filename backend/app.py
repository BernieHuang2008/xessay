import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import logging
import requests
import tempfile
import re

# 导入配置文件
if os.path.exists("config.json"):
    with open("config.json") as f:
        CONFIG = json.load(f)
    PADDLE_OCR_API_URL = CONFIG.get("PADDLE_OCR_API_URL", "")
    PADDLE_OCR_TOKEN = CONFIG.get("PADDLE_OCR_TOKEN", "")
    LLM_API_URL = CONFIG.get("LLM_API_URL", "")
    LLM_API_KEY = CONFIG.get("LLM_API_KEY", "")
else:
    print("警告: config.json 文件不存在，请复制 config.template.json 为 config.json 并填写正确的配置")
    # 使用默认配置
    PADDLE_OCR_API_URL = "https://c8s16af3r0gd36g6.aistudio-app.com/layout-parsing"
    PADDLE_OCR_TOKEN = "your_paddle_ocr_token_here"
    LLM_API_URL = "https://gen.pollinations.ai/v1/chat/completions"
    LLM_API_KEY = "your_llm_api_key_here"
    LLM_MODEL = "qwen-max"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
DATA_FOLDER = 'data'
SESSIONS_FOLDER = os.path.join(DATA_FOLDER, 'sessions')
USERS_FOLDER = os.path.join(DATA_FOLDER, 'users')
PROMPTS_FOLDER = 'prompts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 确保必要的文件夹存在
for folder in [DATA_FOLDER, SESSIONS_FOLDER, USERS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ask_llm(messages: list) -> str:
    import os
    # Use Pollinations AI API for LLM interaction
    url = LLM_API_URL
    api_key = LLM_API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "messages": messages
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    return response

def call_llm_api(messages, max_tokens=2048, temperature=0.7):
    """调用LLM API进行内容生成"""
    try:        
        # response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=60, verify=False)
        response = ask_llm(messages)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "content": result["choices"][0]["message"]["content"]
                # "content": response.text
            }
        else:
            logger.error(f"LLM API request failed with status {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": f"LLM API request failed with status {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error calling LLM API: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def extract_json_from_response(response_text):
    """从LLM响应中提取JSON内容"""
    try:
        # 尝试查找JSON代码块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, response_text)
        
        if match:
            json_str = match.group(1).strip()
            return json.loads(json_str)
        
        # 如果没有找到代码块，尝试直接解析整个响应
        # 找到第一个 { 和最后一个 }
        start = response_text.find('{')
        end = response_text.rfind('}')
        
        if start != -1 and end != -1 and start < end:
            json_str = response_text[start:end+1]
            return json.loads(json_str)
            
        raise ValueError("No valid JSON found in response")
        
    except Exception as e:
        logger.error(f"Error extracting JSON from response: {str(e)}")
        logger.error(f"Response text: {response_text[:500]}...")
        return None

def load_prompt_template(prompt_file):
    """加载prompt模板文件"""
    prompt_path = os.path.join(PROMPTS_FOLDER, prompt_file)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt template {prompt_file}: {str(e)}")
        return None

def generate_user_outline(user_content):
    """使用AI生成用户提纲"""
    prompt_template = load_prompt_template('gen_user_outline.txt')
    if not prompt_template:
        return {"success": False, "error": "Failed to load outline generation prompt"}
    
    # 替换模板中的用户内容
    prompt = str(random.random()) + prompt_template  # 防止缓存
    prompt = prompt.replace('$USER_CONTENT', user_content)
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    result = call_llm_api(messages)
    
    with open("logs_outline_generation.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"prompt:\n{prompt}\n\nresponse:\n{result['content']}\n")

    if result["success"]:
        # 提取JSON内容
        json_content = extract_json_from_response(result["content"])
        if json_content:
            return {"success": True, "outline": json_content}
        else:
            return {"success": False, "error": "Failed to extract JSON from AI response"}
    else:
        return result

def judge_outline(user_content, generated_outline, sessionid):
    """使用AI评价提纲"""
    prompt_template = load_prompt_template('ai_judge_outline.txt')
    if not prompt_template:
        return {"success": False, "error": "Failed to load outline judgment prompt"}
    
    # get std thinking for judgement
    session = load_session_data(sessionid)
    question_id = session.get('question', 'default')
    std_thinking = get_essay_topics(question_id).get("think", "")
    
    # 替换模板中的内容
    prompt = str(random.random()) + prompt_template  # 防止缓存
    prompt = prompt.replace('$USER_CONTENT', user_content)
    prompt = prompt.replace('$GENERATED_OUTLINE', json.dumps(generated_outline, ensure_ascii=False, indent=2))
    prompt = prompt.replace('$STD_THINKING', std_thinking)
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    result = call_llm_api(messages)
    
    with open("logs_outline_judgment.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"prompt:\n{prompt}\n\nresponse:\n{result['content']}\n")

    if result["success"]:
        # 提取JSON内容
        json_content = extract_json_from_response(result["content"])
        if json_content:
            return {"success": True, "judgement": json_content}
        else:
            return {"success": False, "error": "Failed to extract JSON from AI judgment response"}
    else:
        return result

def process_image_with_ocr(file_path):
    """使用PaddleOCR API处理图片并返回OCR结果"""
    try:
        # 读取图片文件并转换为base64
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")
            file_data = file_data
        
        # 设置请求头
        headers = {
            "Authorization": f"token {PADDLE_OCR_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 设置请求数据（fileType=1 表示图片）
        payload = {
            "file": file_data,
            "fileType": 1,
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useTextlineOrientation": False,
            "useChartRecognition": False,
        }
        
        # 发送OCR请求
        response = requests.post(PADDLE_OCR_API_URL, json=payload, headers=headers, timeout=300, verify=False)
        
        if response.status_code == 200:
            result = response.json()["result"]
            
            # 提取Markdown文本内容
            ocr_texts = []
            for res in result["layoutParsingResults"]:
                if "markdown" in res and "text" in res["markdown"]:
                    ocr_texts.append(res["markdown"]["text"])
            
            return {
                "success": True,
                "text_content": "\n\n".join(ocr_texts),
                "raw_result": result
            }
        else:
            logger.error(f"OCR API request failed with status {response.status_code}")
            return {
                "success": False,
                "error": f"OCR API request failed with status {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error processing image with OCR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def load_session_data(sessionid):
    """加载指定session的数据文件"""
    session_file = os.path.join(SESSIONS_FOLDER, f"{sessionid}.json")
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading session {sessionid}: {e}")
            return get_session_template(sessionid)
    return get_session_template(sessionid)

def save_session_data(sessionid, session_data):
    """保存session数据到文件"""
    session_file = os.path.join(SESSIONS_FOLDER, f"{sessionid}.json")
    try:
        session_data['metadata']['last_updated'] = datetime.now().isoformat() + "Z"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving session {sessionid}: {e}")
        return False

def get_all_sessions():
    """获取所有session列表"""
    sessions = {}
    if os.path.exists(SESSIONS_FOLDER):
        for filename in os.listdir(SESSIONS_FOLDER):
            if filename.endswith('.json'):
                sessionid = filename[:-5]  # 移除.json后缀
                session_data = load_session_data(sessionid)
                sessions[sessionid] = {
                    "session_id": session_data.get("session_id", sessionid),
                    "user_name": session_data.get("user_name", f"用户_{sessionid}"),
                    "created_at": session_data.get("created_at", ""),
                    "status": session_data.get("status", "active")
                }
    return sessions

def get_session_template(sessionid):
    """获取session模板数据"""
    return {
        "session_id": sessionid,
        "user_name": f"用户_{sessionid}",
        "session_name": sessionid,  # 默认session名称为sessionid
        "created_at": datetime.now().isoformat() + "Z",
        "status": "active",
        "question": "question_01",
        "essay_outlines": [],
        "imitation_works": {},
        "metadata": {
            "last_updated": datetime.now().isoformat() + "Z",
            "total_submissions": 0
        }
    }

def get_essay_topics(question_id):
    """获取作文题目数据"""
    logger.info(f"Loading essay topic for question ID: {question_id}")
    if os.path.exists(f'./qbank/{question_id}.json'):
        try:
            with open(f'./qbank/{question_id}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading essay topic {question_id}: {e}")
            return {"question": "# 暂无题目\n\n请联系管理员添加题目内容。"}
    else:
        return {"question": "# 暂无题目\n\n请联系管理员添加题目内容。"}

def get_imitation_materials():
    """获取默认仿写材料"""
    return {
        "1": {
            "origin_md": """# 春天的色彩

春天来了，万物复苏。**柳树抽出了新芽，嫩绿嫩绿的，像小姑娘的眉毛。** 桃花开了，粉红粉红的，像小朋友的脸蛋。小草从地里钻出来，绿油油的，像给大地铺上了一层绿毯子。

燕子从南方飞回来了，它们在空中自由地飞翔，叽叽喳喳地叫着，好像在说："春天来了！春天来了！"

## 仿写要求

- **学习重点**：颜色词的使用，比喻修辞手法
- **仿写提示**：选择夏天、秋天或冬天的景物，运用颜色词和比喻，描写季节特色
- **注意事项**：要有具体的景物，生动的比喻，丰富的色彩""",
            "prev_works": []
        },
        "2": {
            "origin_md": """# 雨的交响曲

夏天的雨来得突然，来得猛烈。刚才还是晴空万里，转眼间乌云密布，雷声隆隆。**豆大的雨点砸在地面上，溅起朵朵水花。** 雨越下越大，像瀑布一样从天而降。

雨水冲刷着街道，冲刷着树叶，整个世界都变得清新起来。空气中弥漫着泥土的芬芳，花草也更加翠绿了。

## 仿写要求

- **学习重点**：动词的准确使用，天气变化的描写
- **仿写提示**：选择雪、风或其他天气现象，注意动词的选择和变化过程的描写
- **注意事项**：要写出天气的特点，使用准确的动词，体现变化过程""",
            "prev_works": []
        },
        "3": {
            "origin_md": """# 奶奶的手

奶奶的手很粗糙，上面布满了皱纹，像老树皮一样。但是，**这双手却很温暖，很有力量。** 

小时候，奶奶用这双手给我梳头，给我做饭，给我缝衣服。每当我生病的时候，奶奶就用这双手轻轻地抚摸我的额头，我的病好像就好了一大半。

奶奶的手记录着岁月的痕迹，也记录着对我满满的爱。

## 仿写要求

- **学习重点**：外貌描写，情感表达，对比手法
- **仿写提示**：选择一个亲人的某个部位（如眼睛、声音等），写出特点和情感
- **注意事项**：要有外貌特征，要有情感内容，要表达出深厚的感情""",
            "prev_works": []
        }
    }

def load_user_config(username):
    """加载用户配置文件"""
    user_file = os.path.join(USERS_FOLDER, f"{username}.json")
    if os.path.exists(user_file):
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user config {username}: {e}")
            return get_user_config_template(username)
    return get_user_config_template(username)

def save_user_config(username, user_config):
    """保存用户配置文件"""
    user_file = os.path.join(USERS_FOLDER, f"{username}.json")
    try:
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving user config {username}: {e}")
        return False

def get_user_config_template(username):
    """获取用户配置模板"""
    return {
        "username": username,
        "created_at": datetime.now().isoformat() + "Z",
        "sessions": []
    }

def add_session_to_user(username, session_id, session_name, question_id):
    """为用户添加session记录"""
    user_config = load_user_config(username)
    
    # 检查session是否已存在
    for session in user_config["sessions"]:
        if session["session_id"] == session_id:
            return False  # session已存在
    
    # 添加新session
    new_session = {
        "session_id": session_id,
        "session_name": session_name,
        "question_id": question_id,
        "created_at": datetime.now().isoformat() + "Z"
    }
    user_config["sessions"].append(new_session)
    
    # 保存用户配置
    return save_user_config(username, user_config)

def get_all_questions():
    """获取所有问题列表"""
    questions = []
    qbank_folder = 'qbank'
    
    if os.path.exists(qbank_folder):
        for filename in os.listdir(qbank_folder):
            if filename.startswith('question_') and filename.endswith('.json'):
                question_id = filename[:-5]  # 移除.json后缀
                try:
                    with open(os.path.join(qbank_folder, filename), 'r', encoding='utf-8') as f:
                        question_data = json.load(f)
                        # 提取题目的前100个字符作为简介
                        question_text = question_data.get('question', '')
                        question_brief = question_text[:100] + '...' if len(question_text) > 100 else question_text
                        
                        questions.append({
                            "question_id": question_id,
                            "title": question_brief.split('\n')[0],  # 第一行作为标题
                            "brief": question_brief
                        })
                except Exception as e:
                    logger.error(f"Error loading question {question_id}: {e}")
    
    return sorted(questions, key=lambda x: x['question_id'])

def create_new_session(username, question_id, session_name=None):
    """创建新session"""
    # 生成session_id
    session_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作为session_id
    
    # 如果没有指定session名称，使用question_id作为默认名称
    if not session_name:
        session_name = question_id
    
    created_at = datetime.now().isoformat() + "Z"
    
    # 创建session数据
    session_data = {
        "session_id": session_id,
        "user_name": username,
        "session_name": session_name,
        "created_at": created_at,
        "status": "active",
        "question": question_id,
        "essay_outlines": [],
        "imitation_works": {},
        "metadata": {
            "last_updated": created_at,
            "total_submissions": 0
        }
    }
    
    # 保存session数据
    if save_session_data(session_id, session_data):
        # 将session添加到用户配置
        if add_session_to_user(username, session_id, session_name, created_at):
            return {
                "success": True,
                "session_id": session_id,
                "session_name": session_name,
                "created_at": created_at
            }
        else:
            # 如果添加到用户配置失败，删除已创建的session文件
            session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
            return {
                "success": False,
                "error": "Failed to add session to user config"
            }
    else:
        return {
            "success": False,
            "error": "Failed to create session file"
        }

# API 路由

@app.route('/')
def index():
    return jsonify({
        "message": "Essay Training Backend API",
        "version": "1.0.0",
        "endpoints": [
            "POST /createSession - 创建新session",
            "GET /getUserSessions?username=xxx - 获取用户所有session",
            "GET /getAllQuestions - 获取所有题目列表",
            "GET /getSessionDetail?sessionid=xxx - 获取session详情",
            "GET /getEssayTopic?sessionid=xxx - 获取题目内容", 
            "POST /submitEssayOutline?sessionid=xxx - 提交审题分析",
            "GET /getImitation?sessionid=xxx - 获取仿写材料",
            "POST /submitImitation?sessionid=xxx&imitid=xxx - 提交仿写作品"
        ]
    })



@app.route('/createSession', methods=['POST'])
def create_session():
    """创建新的session"""
    try:
        data = request.get_json()
        username = data.get('username')
        question_id = data.get('question_id')
        session_name = data.get('session_name', question_id)  # 默认使用question_id作为session名称
        
        if not username or not question_id:
            return jsonify({"success": False, "error": "缺少必要参数：username 和 question_id"}), 400
        
        # 生成唯一的session_id
        session_id = f"{username}_{question_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 检查question_id是否存在
        question_file = f'qbank/{question_id}.json'
        if not os.path.exists(question_file):
            return jsonify({"success": False, "error": f"题目 {question_id} 不存在"}), 400
        
        # 创建session数据
        session_data = {
            "session_id": session_id,
            "session_name": session_name,
            "username": username,
            "created_at": datetime.now().isoformat() + "Z",
            "status": "active",
            "question": question_id,
            "essay_outlines": [],
            "imitation_works": {},
            "metadata": {
                "last_updated": datetime.now().isoformat() + "Z",
                "total_submissions": 0
            }
        }
        
        # 保存session文件
        if not save_session_data(session_id, session_data):
            return jsonify({"success": False, "error": "保存session失败"}), 500
        
        # 添加到用户配置
        if not add_session_to_user(username, session_id, session_name, question_id):
            logger.warning(f"Failed to add session {session_id} to user {username} config")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "session_name": session_name,
            "message": "Session创建成功"
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/getUserSessions')
def get_user_sessions():
    """获取用户的所有session"""
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"success": False, "error": "缺少username参数"}), 400
        
        user_data = load_user_config(username)
        
        # 验证session文件是否存在，并获取详细信息
        sessions_with_details = []
        for session in user_data["sessions"]:
            session_id = session["session_id"]
            session_data = load_session_data(session_id)
            
            sessions_with_details.append({
                "session_id": session_id,
                "session_name": session.get("session_name", session_id),
                "question_id": session.get("question_id", session_data.get("question", "unknown")),
                "created_at": session.get("created_at", ""),
                "status": session_data.get("status", "active"),
                "outline_count": len(session_data.get("essay_outlines", [])),
                "last_updated": session_data.get("metadata", {}).get("last_updated", "")
            })
        
        return jsonify({
            "success": True,
            "username": username,
            "sessions": sessions_with_details
        })
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/getAllQuestions')
def get_all_questions_api():
    """获取所有问题列表的API"""
    try:
        questions = get_all_questions()
        return jsonify({
            "success": True,
            "questions": questions
        })
    except Exception as e:
        logger.error(f"Error getting all questions: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/getSessionDetail')
def get_session_detail():
    """获取session详情"""
    sessionid = request.args.get('sessionid')
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    session_data = load_session_data(sessionid)
    
    # 如果是新创建的session，保存到文件
    session_file = os.path.join(SESSIONS_FOLDER, f"{sessionid}.json")
    if not os.path.exists(session_file):
        save_session_data(sessionid, session_data)
        logger.info(f"Created new session: {sessionid}")
    
    # 返回基本session信息
    session_info = session_data
    
    logger.info(f"Retrieved session: {sessionid}")
    return jsonify(session_info)

@app.route('/getEssayTopic')
def get_essay_topic():
    """获取作文题目"""
    sessionid = request.args.get('sessionid')
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    session = load_session_data(sessionid)
    question_id = session.get('question', 'default')
    
    # 获取默认题目（可以扩展为根据session返回不同题目）]
    topic_md = get_essay_topics(question_id)["question"] or '# 暂无题目\n\n请联系管理员添加题目内容。'
    
    logger.info(f"Retrieved essay topic for session: {sessionid}")
    return jsonify({"topic_md": topic_md})

@app.route('/submitEssayOutline', methods=['POST'])
def submit_essay_outline():
    """提交审题分析"""
    sessionid = request.args.get('sessionid')
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 使用临时文件处理上传的图片
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            
            # 使用OCR处理图片
            ocr_result = process_image_with_ocr(temp_file.name)
            
            # 清理临时文件
            # os.unlink(temp_file.name)
        
        if ocr_result["success"]:
            # 使用AI生成提纲
            logger.info(f"Generating outline using AI for session {sessionid}")
            outline_result = generate_user_outline(ocr_result["text_content"])
            
            if outline_result["success"]:
                # 使用AI评价提纲
                logger.info(f"Judging outline using AI for session {sessionid}")
                judgement_result = judge_outline(ocr_result["text_content"], outline_result["outline"], sessionid)
                
                # 准备保存到session的数据
                outline_data = {
                    "text_content": ocr_result["text_content"],
                    "structured_content": outline_result["outline"],
                    "ai_judgement": judgement_result["judgement"] if judgement_result["success"] else {},
                    "submitted_at": datetime.now().isoformat(),
                    "original_filename": secure_filename(file.filename)
                }
                
                # 如果AI评价失败，记录错误但不影响整体流程
                if not judgement_result["success"]:
                    outline_data["judgement_error"] = judgement_result["error"]
                    logger.warning(f"AI judgement failed for session {sessionid}: {judgement_result['error']}")
                
                # 记录提交信息到session文件
                session_data = load_session_data(sessionid)
                session_data['essay_outlines'].append(outline_data)
                session_data['metadata']['total_submissions'] += 1
                save_session_data(sessionid, session_data)
                
                logger.info(f"Essay outline fully processed for session {sessionid}")
                return jsonify({
                    "success": True,
                    "message": "Outline submitted and processed successfully",
                    "text_content": ocr_result["text_content"][:200] + "..." if len(ocr_result["text_content"]) > 200 else ocr_result["text_content"],
                    "structured_content": outline_result["outline"],
                    "ai_judgement": outline_data["ai_judgement"],
                    "judgement_success": judgement_result["success"]
                })
            else:
                # AI生成失败，但OCR成功，仍然保存基本信息
                logger.error(f"AI outline generation failed for session {sessionid}: {outline_result['error']}")
                
                outline_data = {
                    "text_content": ocr_result["text_content"],
                    "structured_content": {},
                    "ai_judgement": {},
                    "generation_error": outline_result["error"],
                    "submitted_at": datetime.now().isoformat(),
                    "original_filename": secure_filename(file.filename)
                }
                
                session_data = load_session_data(sessionid)
                session_data['essay_outlines'].append(outline_data)
                session_data['metadata']['total_submissions'] += 1
                save_session_data(sessionid, session_data)
                
                return jsonify({
                    "success": False,
                    "error": f"OCR succeeded but AI processing failed: {outline_result['error']}",
                    "text_content": ocr_result["text_content"][:200] + "..." if len(ocr_result["text_content"]) > 200 else ocr_result["text_content"]
                }), 500
        else:
            logger.error(f"OCR processing failed for session {sessionid}: {ocr_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}"
            }), 500
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/getImitation')
def get_imitation():
    """获取仿写材料"""
    sessionid = request.args.get('sessionid')
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    # 获取默认仿写材料
    imitations = get_imitation_materials()
    
    # 获取该session的历史仿写作品
    session_data = load_session_data(sessionid)
    session_imitations = session_data.get('imitation_works', {})
    
    # 为每个语段加载历史作品
    for imitid, imitation in imitations.items():
        if imitid in session_imitations:
            works = session_imitations[imitid]
            prev_works = []
            for work in works:
                try:
                    # 直接从 JSON 中读取内容
                    if 'text_content' in work:
                        prev_works.append({
                            "text_content": work['text_content'],
                            "submitted_at": work.get('submitted_at', '')
                        })
                except Exception as e:
                    logger.error(f"Error loading work data: {e}")
                    continue
            
            imitations[imitid]['prev_works'] = prev_works
        else:
            imitations[imitid]['prev_works'] = []
    
    logger.info(f"Retrieved imitation materials for session: {sessionid}")
    return jsonify({"imitations": imitations})

@app.route('/submitImitation', methods=['POST'])
def submit_imitation():
    """提交仿写作品"""
    sessionid = request.args.get('sessionid')
    imitid = request.args.get('imitid')
    
    if not sessionid or not imitid:
        return jsonify({"error": "Missing sessionid or imitid parameter"}), 400
    
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 使用临时文件处理上传的图片
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            
            # 使用OCR处理图片
            ocr_result = process_image_with_ocr(temp_file.name)
            
            # 清理临时文件
            os.unlink(temp_file.name)
        
        if ocr_result["success"]:
            # 记录提交信息到session文件（直接存储OCR结果）
            session_data = load_session_data(sessionid)
            
            if imitid not in session_data['imitation_works']:
                session_data['imitation_works'][imitid] = []
            
            session_data['imitation_works'][imitid].append({
                "text_content": ocr_result["text_content"],
                "submitted_at": datetime.now().isoformat(),
                "original_filename": secure_filename(file.filename)
            })
            
            session_data['metadata']['total_submissions'] += 1
            save_session_data(sessionid, session_data)
            
            logger.info(f"Imitation work OCR processed for session {sessionid}, segment {imitid}")
            return jsonify({
                "success": True,
                "message": "Imitation submitted and processed successfully",
                "imitid": imitid,
                "text_content": ocr_result["text_content"][:200] + "..." if len(ocr_result["text_content"]) > 200 else ocr_result["text_content"]
            })
        else:
            logger.error(f"OCR processing failed for session {sessionid}, imitid {imitid}: {ocr_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}"
            }), 500
    
    return jsonify({"error": "Invalid file type"}), 400


# 管理接口（可选）
@app.route('/admin/sessions')
def admin_sessions():
    """管理接口：查看所有sessions"""
    sessions = get_all_sessions()
    return jsonify(sessions)

@app.route('/admin/session/<sessionid>')
def admin_session_detail(sessionid):
    """管理接口：查看指定session详情"""
    session_data = load_session_data(sessionid)
    return jsonify(session_data)

@app.route('/admin/reset/<sessionid>', methods=['POST'])
def admin_reset_session(sessionid):
    """管理接口：重置指定session数据"""
    try:
        session_file = os.path.join(SESSIONS_FOLDER, f"{sessionid}.json")
        if os.path.exists(session_file):
            os.remove(session_file)
        logger.info(f"Session {sessionid} reset successfully")
        return jsonify({"message": f"Session {sessionid} reset successfully"})
    except Exception as e:
        logger.error(f"Error resetting session {sessionid}: {e}")
        return jsonify({"error": f"Failed to reset session: {str(e)}"}), 500

@app.route('/getStandardOutlines')
def get_standard_outlines():
    """获取标准提纲"""
    try:
        sessionid = request.args.get('sessionid')
        if not sessionid:
            return jsonify({'error': '缺少session ID参数'}), 400
            
        # 获取会话信息
        session_file = os.path.join(SESSIONS_FOLDER, f'{sessionid}.json')
        if not os.path.exists(session_file):
            return jsonify({'error': '会话不存在'}), 404
            
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            
        question_id = session_data.get('question')
        if not question_id:
            return jsonify({'error': '会话中没有题目信息'}), 400
            
        # 读取题目文件获取标准提纲
        question_file = os.path.join('qbank', f'{question_id}.json')
        if not os.path.exists(question_file):
            return jsonify({'error': '题目文件不存在'}), 404
            
        with open(question_file, 'r', encoding='utf-8') as f:
            question_data = json.load(f)
            
        outlines = question_data.get('outlines', [])
        return jsonify({
            'status': 'success',
            'outlines': outlines,
            'think': question_data.get('think', ''),
            'question_text': question_data.get('question', '')
        })
        
    except Exception as e:
        logger.error(f"获取标准提纲出错: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/uploadImage', methods=['POST'])
def upload_image():
    """上传图片"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file :
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 简单处理文件名，保留扩展名或默认为png
            ext = os.path.splitext(file.filename)[1]
            if not ext:
                ext = '.png'
                
            filename = f"upload_{timestamp}_{str(uuid.uuid4())[:8]}{ext}"
            uploads_dir = os.path.join(DATA_FOLDER, 'uploads')
            
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, filename)
            file.save(file_path)
            
            return jsonify({
                "success": True,
                "message": "Image uploaded successfully",
                "filename": filename
            })
        except Exception as e:
            logger.error(f"Error saving uploaded image: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # print("="*50)
    # print("Essay Training Backend Server")
    # print("="*50)
    # print("Available endpoints:")
    # print("  GET  /                                  - API信息")
    # print("  GET  /getSessionDetail?sessionid=xxx    - 获取session详情")  
    # print("  GET  /getEssayTopic?sessionid=xxx       - 获取作文题目")
    # print("  POST /submitEssayOutline?sessionid=xxx  - 提交审题分析(含AI处理)")
    # print("  GET  /getImitation?sessionid=xxx        - 获取仿写材料")
    # print("  POST /submitImitation?sessionid=xxx&imitid=xxx - 提交仿写作品")
    # print("  GET  /getOCRResult?sessionid=xxx&type=essay - 获取OCR结果")
    # print("  GET  /getStandardOutlines?sessionid=xxx - 获取标准提纲")
    # print("\nTesting endpoints:")
    # print("  POST /test/ai                           - 测试AI处理功能")
    # print("\nManagement endpoints:")
    # print("  GET  /admin/sessions                    - 查看所有sessions")
    # print("  GET  /admin/session/<sessionid>         - 查看指定session详情")
    # print("  POST /admin/reset/<sessionid>           - 重置指定session")
    # print("="*50)
    # print("Starting server on http://localhost:5005")
    # print("Press Ctrl+C to stop")
    # print("="*50)
    
    app.run(host='0.0.0.0', port=5005, debug=True)
