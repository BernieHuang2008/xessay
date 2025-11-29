# OCR + AI 处理功能使用说明

## 功能概述

本系统在OCR完成后会自动执行以下AI处理流程：

1. **OCR文本提取** - 将用户上传的图片转换为文字
2. **AI生成提纲** - 使用AI根据用户内容生成结构化提纲  
3. **AI评价分析** - 对生成的提纲进行评分和改进建议

## 配置步骤

### 1. 配置LLM API

编辑 `app.py` 文件，修改第19-21行的配置：

```python
# LLM API 配置
LLM_API_URL = "https://api.openai.com/v1/chat/completions"  # 你的API地址
LLM_API_KEY = "sk-your-api-key-here"                      # 你的API密钥  
LLM_MODEL = "gpt-3.5-turbo"                              # 使用的模型
```

### 2. 启动服务器

```bash
cd backend
python app.py
```

## 使用流程

### 方式1：通过前端界面

1. 访问前端页面
2. 选择session
3. 上传包含文字的图片
4. 系统自动完成OCR + AI处理
5. 查看结果中的：
   - `text_content`: 原始OCR文字
   - `structured_content`: AI生成的提纲
   - `ai_judgement`: AI评价结果

### 方式2：直接API调用

```bash
curl -X POST "http://localhost:5005/submitEssayOutline?sessionid=test" \
  -F "image=@your_image.jpg"
```

### 方式3：使用测试接口

```bash
python test_ai.py
```

或直接调用测试API：

```bash
curl -X POST "http://localhost:5005/test/ai" \
  -H "Content-Type: application/json" \
  -d '{"text_content": "你的测试文本内容"}'
```

## 数据结构

处理完成后，session文件中的 `essay_outlines` 数组会包含：

```json
{
  "text_content": "用户原始书写内容",
  "structured_content": {
    "title": "提纲标题",
    "subject": "作文主旨", 
    "parts": [
      {
        "part_title": "部分标题",
        "content": "主要内容",
        "examples": ["例子1", "例子2"],
        "quotes": ["名言1", "名言2"],
        "example_content": "【空】"
      }
    ]
  },
  "ai_judgement": {
    "overall_score": 85,
    "detailed_scores": {
      "structure": 22,
      "theme_relevance": 20, 
      "language": 23,
      "creativity": 20
    },
    "strengths": ["优点1", "优点2"],
    "improvements": ["改进建议1", "改进建议2"],
    "comments": "总体评价"
  }
}
```

## 自定义Prompt

### 修改提纲生成prompt

编辑 `prompts/gen_user_outline.txt` 文件来自定义AI如何生成提纲。

### 修改评价prompt  

编辑 `prompts/ai_judge_outline.txt` 文件来自定义AI如何评价提纲。

## 错误处理

- 如果LLM API调用失败，OCR结果仍会保存
- 错误信息会记录在服务器日志中
- 系统会继续运行，不会因AI处理失败而崩溃
- 可以通过测试接口验证AI功能是否正常

## 常见问题

### Q: AI处理很慢怎么办？
A: AI处理需要时间，请耐心等待。可以在prompt中要求更简洁的输出。

### Q: 如何更换AI模型？
A: 修改 `app.py` 中的 `LLM_MODEL` 配置即可。

### Q: 支持哪些AI API？
A: 支持所有兼容OpenAI格式的API，包括OpenAI、Azure OpenAI、Claude等。

### Q: 如何查看处理日志？
A: 查看服务器控制台输出，或配置日志文件。