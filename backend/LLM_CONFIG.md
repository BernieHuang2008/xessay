# LLM API 配置说明

## 配置步骤

1. **打开 app.py 文件**
   - 找到第19-21行的LLM API配置部分

2. **修改API配置**
   ```python
   # LLM API 配置
   LLM_API_URL = "your-llm-api-url"  # 替换为实际的LLM API地址
   LLM_API_KEY = "your-api-key"      # 替换为实际的API密钥
   LLM_MODEL = "your-model-name"     # 替换为实际的模型名称
   ```

## 支持的API类型

### OpenAI API
```python
LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_API_KEY = "sk-your-openai-api-key"
LLM_MODEL = "gpt-3.5-turbo"  # 或 "gpt-4"
```

### 其他兼容OpenAI格式的API
```python
# 例如：Azure OpenAI
LLM_API_URL = "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-07-01-preview"
LLM_API_KEY = "your-azure-api-key"
LLM_MODEL = "gpt-35-turbo"

# 例如：其他第三方API
LLM_API_URL = "https://api.your-provider.com/v1/chat/completions"
LLM_API_KEY = "your-api-key"
LLM_MODEL = "your-model-name"
```

## 功能说明

配置完成后，系统将在OCR完成后自动执行以下步骤：

1. **OCR处理**：将用户上传的图片转换为文本
2. **生成提纲**：使用`gen_user_outline.txt`中的prompt，将OCR内容发送给AI生成结构化提纲
3. **评价提纲**：使用`ai_judge_outline.txt`中的prompt，对生成的提纲进行评价和打分
4. **保存结果**：将所有结果保存到对应session的`essay_outlines`中：
   - `text_content`: 用户原始内容（OCR结果）
   - `structured_content`: AI生成的JSON格式提纲
   - `ai_judgement`: AI评价结果（包含分数和建议）

## 测试API连接

可以通过以下方式测试API是否配置正确：

1. 修改配置后重启服务器
2. 上传一张包含文字的图片
3. 查看服务器日志，确认AI处理步骤是否成功
4. 检查返回的JSON中是否包含`structured_content`和`ai_judgement`字段

## 错误处理

- 如果LLM API调用失败，OCR结果仍会保存
- 错误信息会记录在日志和返回结果中
- 系统会继续运行，不会因为AI处理失败而崩溃