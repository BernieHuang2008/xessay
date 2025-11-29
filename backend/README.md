# 作文训练系统后端服务

一个基于 Flask 的后端 API 服务，为作文训练系统提供数据支持。

## 功能特性

### ✅ 完整的 API 支持
- **Session 管理**: 用户会话创建和查询
- **审题训练**: 题目获取和分析提交
- **仿写训练**: 材料获取和作品提交  
- **文件上传**: 图片文件安全上传和存储
- **历史记录**: 自动保存和加载用户作品

### 🛠️ 技术特性
- **跨域支持**: CORS 配置，支持前端调用
- **文件管理**: 安全的文件上传和存储
- **数据持久化**: JSON 文件存储，简单可靠
- **日志系统**: 完整的请求和错误日志
- **管理接口**: 数据查看和重置功能

## 快速开始

### 1. 环境准备

确保已安装 Python 3.7+：
```bash
python --version
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5005` 启动

### 4. 验证运行

访问 `http://localhost:5005` 查看 API 信息

## API 接口详解

### Session 管理

#### GET /getSessionDetail
```
URL: http://localhost:5005/getSessionDetail?sessionid=test
功能: 获取或创建 session 信息
返回: 用户名、创建时间、状态等信息
```

### 审题训练

#### GET /getEssayTopic  
```
URL: http://localhost:5005/getEssayTopic?sessionid=test
功能: 获取作文题目（Markdown 格式）
返回: 完整的题目内容和要求
```

#### POST /submitEssayOutline
```
URL: http://localhost:5005/submitEssayOutline?sessionid=test
功能: 提交审题分析图片
格式: multipart/form-data
字段: image (图片文件)
```

### 仿写训练

#### GET /getImitation
```
URL: http://localhost:5005/getImitation?sessionid=test  
功能: 获取仿写材料和历史作品
返回: 多段原文 + 用户历史仿写图片
```

#### POST /submitImitation
```
URL: http://localhost:5005/submitImitation?sessionid=test&imitid=1
功能: 提交仿写作品图片
格式: multipart/form-data
字段: image (图片文件)
```

## 数据结构

### 目录结构
```
backend/
├── app.py              # 主服务文件
├── requirements.txt    # 依赖包列表
├── data/              # 数据存储目录
│   └── data.json      # 主数据文件
├── uploads/           # 用户上传文件
└── README.md          # 说明文档
```

### 数据格式

#### Sessions 数据
```json
{
  "sessions": {
    "session_id": {
      "session_id": "string",
      "user_name": "string", 
      "created_at": "timestamp",
      "status": "active|completed"
    }
  }
}
```

#### 仿写材料数据
```json
{
  "imitations": {
    "default": {
      "1": {
        "origin_md": "原文内容(Markdown)",
        "prev_works": ["base64图片数据"]
      }
    }
  }
}
```

## 内置示例数据

### 作文题目
- **题目**: "成长路上的那盏灯"
- **类型**: 记叙文，600字以上
- **要求**: 具体事例、真实感受、结构完整
- **提示**: 人物之灯、知识之灯、精神之灯、经历之灯

### 仿写材料
1. **春天的色彩** - 学习颜色词和比喻修辞
2. **雨的交响曲** - 学习动词使用和天气描写  
3. **奶奶的手** - 学习外貌描写和情感表达

## 管理功能

### 查看数据
```bash
# 查看所有 sessions
curl http://localhost:5005/admin/sessions

# 查看所有提交记录
curl http://localhost:5005/admin/submissions
```

### 重置数据
```bash
curl -X POST http://localhost:5005/admin/reset
```

### 查看上传文件
```
URL: http://localhost:5005/uploads/filename.png
功能: 直接访问上传的图片文件
```

## 配置说明

### 端口配置
在 `app.py` 文件末尾修改：
```python
app.run(host='0.0.0.0', port=5005, debug=True)
```

### 文件上传限制
支持的图片格式：PNG, JPG, JPEG, GIF

### 数据存储
- 使用 JSON 文件存储，位于 `data/data.json`
- 上传文件存储在 `uploads/` 目录
- 自动创建必要的目录结构

## 安全特性

### 文件安全
- 文件名过滤和清理
- 文件类型验证
- 唯一文件名生成（防止覆盖）

### 输入验证
- 参数完整性检查
- 错误处理和友好提示
- 日志记录便于调试

## 扩展功能

### 数据库支持
可以将 JSON 存储替换为数据库：
- SQLite（轻量级）
- PostgreSQL（生产环境）
- MongoDB（文档型）

### 身份认证
添加用户认证系统：
- JWT Token 认证
- Session 管理
- 权限控制

### 文件存储
升级文件存储方案：
- 云存储（OSS、S3）
- CDN 加速
- 图片压缩优化

## 故障排除

### 常见问题

**Q: 启动时提示端口被占用**
```bash
# 查看端口占用
netstat -ano | findstr :5005
# 或使用其他端口
python app.py  # 修改代码中的端口号
```

**Q: 跨域请求被拒绝**
```
确认已安装 flask-cors：
pip install flask-cors
```

**Q: 文件上传失败**
```
检查 uploads 目录权限
检查文件大小和格式
查看后端日志输出
```

### 日志查看
服务运行时会在控制台输出详细日志：
- 请求信息
- 错误详情  
- 文件操作记录

## 生产部署

### 使用 Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5005 app:app
```

### 使用 Docker
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5005
CMD ["python", "app.py"]
```

### 环境变量配置
```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
```

## 许可证

本项目采用 MIT 许可证。