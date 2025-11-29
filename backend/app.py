from flask import Flask, request, jsonify, send_from_directory
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
DATA_FOLDER = 'data'
SESSIONS_FOLDER = os.path.join(DATA_FOLDER, 'sessions')
OCR_FOLDER = 'data/ocr_results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# PaddleOCR API 配置
PADDLE_OCR_API_URL = "https://c8s16af3r0gd36g6.aistudio-app.com/layout-parsing"
PADDLE_OCR_TOKEN = "7ad08cbd63f5ba8d355eb517d00a23158c419983"

# 确保必要的文件夹存在
for folder in [DATA_FOLDER, SESSIONS_FOLDER, OCR_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        response = requests.post(PADDLE_OCR_API_URL, json=payload, headers=headers, timeout=30, verify=False)
        
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
        "created_at": datetime.now().isoformat() + "Z",
        "status": "active",
        "essay_outlines": [],
        "imitation_works": {},
        "metadata": {
            "last_updated": datetime.now().isoformat() + "Z",
            "total_submissions": 0
        }
    }

def get_essay_topics():
    """获取作文题目数据"""
    return {
        "essay_topics": {
            "default": """# 作文题目：成长路上的那盏灯

## 题目要求

请以"成长路上的那盏灯"为题，写一篇不少于600字的记叙文。

## 写作要求

1. **题目理解**
   - 题目中的"灯"可以是具体的灯，也可以是比喻义的"灯"
   - "成长路上"指人生成长历程中的某个阶段或时期

2. **内容要求**
   - 要有具体的事例和真实的感受
   - 体现"灯"对自己成长的指引和帮助作用
   - 突出"灯"的重要意义

3. **表达要求**
   - 语言要生动，描写要细致
   - 结构要完整，层次要清楚
   - 感情要真挚，主题要突出

## 写作提示

- **人物之灯**：老师、父母、朋友等给予指导和帮助的人
- **知识之灯**：书籍、学习、智慧等启发思考的事物  
- **精神之灯**：理想、信念、品格等激励前行的力量
- **经历之灯**：挫折、成功、体验等促进成长的经历

## 思考角度

1. 这盏"灯"是什么？在什么情况下出现？
2. 它如何照亮了你前行的道路？
3. 通过这件事，你有什么感悟和成长？
4. 这盏"灯"对你的人生有什么深远影响？"""
        },
        "imitations": {
            "default": {
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
        },
        "submissions": {
            "essay_outlines": {},
            "imitation_works": {}
        }
    }

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

# API 路由

@app.route('/')
def index():
    return jsonify({
        "message": "Essay Training Backend API",
        "version": "1.0.0",
        "endpoints": [
            "GET /getSessionDetail?sessionid=xxx",
            "GET /getEssayTopic?sessionid=xxx", 
            "POST /submitEssayOutline?sessionid=xxx",
            "GET /getImitation?sessionid=xxx",
            "POST /submitImitation?sessionid=xxx&imitid=xxx"
        ]
    })

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
    session_info = {
        "session_id": session_data.get("session_id"),
        "user_name": session_data.get("user_name"),
        "created_at": session_data.get("created_at"),
        "status": session_data.get("status")
    }
    
    logger.info(f"Retrieved session: {sessionid}")
    return jsonify(session_info)

@app.route('/getEssayTopic')
def get_essay_topic():
    """获取作文题目"""
    sessionid = request.args.get('sessionid')
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    # 获取默认题目（可以扩展为根据session返回不同题目）
    essay_topics = get_essay_topics()['essay_topics']
    topic_md = essay_topics.get('default', '# 暂无题目\n\n请联系管理员添加题目内容。')
    
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
            # 保存OCR结果到文件
            ocr_filename = f"outline_{sessionid}_{timestamp}.md"
            ocr_filepath = os.path.join(OCR_FOLDER, ocr_filename)
            
            with open(ocr_filepath, 'w', encoding='utf-8') as ocr_file:
                ocr_file.write(ocr_result["text_content"])
            
            # 记录提交信息到session文件（只存储OCR结果）
            session_data = load_session_data(sessionid)
            
            session_data['essay_outlines'].append({
                "ocr_filename": ocr_filename,
                "ocr_filepath": ocr_filepath,
                "text_content": ocr_result["text_content"],
                "submitted_at": datetime.now().isoformat(),
                "original_filename": secure_filename(file.filename)
            })
            
            session_data['metadata']['total_submissions'] += 1
            save_session_data(sessionid, session_data)
            
            logger.info(f"Essay outline OCR processed for session {sessionid}: {ocr_filename}")
            return jsonify({
                "success": True,
                "message": "Outline submitted and processed successfully",
                "ocr_filename": ocr_filename,
                "text_content": ocr_result["text_content"][:200] + "..." if len(ocr_result["text_content"]) > 200 else ocr_result["text_content"]
            })
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
                    # 读取OCR结果文件
                    if 'ocr_filepath' in work and os.path.exists(work['ocr_filepath']):
                        with open(work['ocr_filepath'], 'r', encoding='utf-8') as f:
                            text_content = f.read()
                            prev_works.append({
                                "text_content": text_content,
                                "submitted_at": work.get('submitted_at', ''),
                                "ocr_filename": work.get('ocr_filename', '')
                            })
                    # 兼容旧格式（如果还有存储的text_content）
                    elif 'text_content' in work:
                        prev_works.append({
                            "text_content": work['text_content'],
                            "submitted_at": work.get('submitted_at', ''),
                            "ocr_filename": work.get('ocr_filename', '')
                        })
                except Exception as e:
                    logger.error(f"Error loading OCR result {work.get('ocr_filepath', 'unknown')}: {e}")
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
            # 保存OCR结果到文件
            ocr_filename = f"imitation_{sessionid}_{imitid}_{timestamp}.md"
            ocr_filepath = os.path.join(OCR_FOLDER, ocr_filename)
            
            with open(ocr_filepath, 'w', encoding='utf-8') as ocr_file:
                ocr_file.write(ocr_result["text_content"])
            
            # 记录提交信息到session文件（只存储OCR结果）
            session_data = load_session_data(sessionid)
            
            if imitid not in session_data['imitation_works']:
                session_data['imitation_works'][imitid] = []
            
            session_data['imitation_works'][imitid].append({
                "ocr_filename": ocr_filename,
                "ocr_filepath": ocr_filepath,
                "text_content": ocr_result["text_content"],
                "submitted_at": datetime.now().isoformat(),
                "original_filename": secure_filename(file.filename)
            })
            
            session_data['metadata']['total_submissions'] += 1
            save_session_data(sessionid, session_data)
            
            logger.info(f"Imitation work OCR processed for session {sessionid}, segment {imitid}: {ocr_filename}")
            return jsonify({
                "success": True,
                "message": "Imitation submitted and processed successfully",
                "ocr_filename": ocr_filename,
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

# OCR结果查看接口
@app.route('/ocr/<filename>')
def ocr_result(filename):
    """查看OCR处理结果"""
    return send_from_directory(OCR_FOLDER, filename)

@app.route('/getOCRResult')
def get_ocr_result():
    """获取指定session的OCR结果"""
    sessionid = request.args.get('sessionid')
    result_type = request.args.get('type', 'essay')  # essay 或 imitation
    
    if not sessionid:
        return jsonify({"error": "Missing sessionid parameter"}), 400
    
    session_data = load_session_data(sessionid)
    
    if result_type == 'essay':
        # 获取审题分析OCR结果
        outlines = session_data.get('essay_outlines', [])
        if outlines:
            latest = outlines[-1]  # 获取最新的
            return jsonify({
                "success": True,
                "result_type": "essay_outline",
                "text_content": latest.get('text_content', ''),
                "submitted_at": latest.get('submitted_at', ''),
                "ocr_filename": latest.get('ocr_filename', '')
            })
    elif result_type == 'imitation':
        # 获取仿写OCR结果
        imitid = request.args.get('imitid')
        if not imitid:
            return jsonify({"error": "Missing imitid parameter for imitation type"}), 400
        
        imitations = session_data.get('imitation_works', {}).get(imitid, [])
        if imitations:
            return jsonify({
                "success": True,
                "result_type": "imitation",
                "works": [{
                    "text_content": work.get('text_content', ''),
                    "submitted_at": work.get('submitted_at', ''),
                    "ocr_filename": work.get('ocr_filename', '')
                } for work in imitations]
            })
    
    return jsonify({
        "success": False,
        "error": "No OCR results found"
    }), 404

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

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("="*50)
    print("Essay Training Backend Server")
    print("="*50)
    print("Available endpoints:")
    print("  GET  /                                  - API信息")
    print("  GET  /getSessionDetail?sessionid=xxx    - 获取session详情")  
    print("  GET  /getEssayTopic?sessionid=xxx       - 获取作文题目")
    print("  POST /submitEssayOutline?sessionid=xxx  - 提交审题分析")
    print("  GET  /getImitation?sessionid=xxx        - 获取仿写材料")
    print("  POST /submitImitation?sessionid=xxx&imitid=xxx - 提交仿写作品")
    print("\nManagement endpoints:")
    print("  GET  /admin/sessions                    - 查看所有sessions")
    print("  GET  /admin/submissions                 - 查看所有提交记录")
    print("  POST /admin/reset                       - 重置数据")
    print("="*50)
    print("Starting server on http://localhost:5005")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    app.run(host='0.0.0.0', port=5005, debug=True, )