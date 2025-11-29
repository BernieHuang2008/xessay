# 配置说明

## API密钥配置

为了保护敏感信息，API密钥已移至配置文件中。请按以下步骤进行配置：

### 1. 复制配置文件模板
```bash
cd backend
cp config.py.template config.py
```

### 2. 编辑配置文件
打开 `backend/config.py` 文件，填写正确的API密钥：

```python
# PaddleOCR API 配置
PADDLE_OCR_TOKEN = "你的PaddleOCR_Token"

# LLM API 配置
LLM_API_KEY = "你的LLM_API_Key"
```

### 3. 注意事项
- `config.py` 文件已加入 `.gitignore`，不会被提交到版本控制
- 请妥善保管你的API密钥，不要将其公开或分享
- 如果需要部署到生产环境，请确保配置文件的安全性

### 4. 支持的LLM API
当前配置支持阿里云DashScope（通义千问）API，如需使用其他LLM服务，请修改配置文件中的：
- `LLM_API_URL`: API端点地址
- `LLM_MODEL`: 模型名称

### 5. 故障排除
如果启动时提示配置文件错误：
1. 检查 `backend/config.py` 是否存在
2. 检查配置文件中的API密钥是否正确填写
3. 确保没有语法错误