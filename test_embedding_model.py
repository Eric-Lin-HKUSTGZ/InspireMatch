"""
测试代码：测试embeeding模型的调用
"""
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1/chat/completions",
  api_key="sk-OUklCXtmOyGEpre35ls9QFp3xKDlFB3VTLEOgFJlQVAkMhzd",
)

embedding = client.embeddings.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  model="Qwen/Qwen3-Embedding-8B",
  input="Your text string goes here",
  # input: ["text1", "text2", "text3"] # batch embeddings also supported!
  encoding_format="float"
)
print(embedding.data[0].embedding)