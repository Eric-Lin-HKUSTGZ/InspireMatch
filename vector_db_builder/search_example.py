"""
使用sonar-pro-search进行搜索的示例代码
基于test_openrouter.py的实现
"""
from openai import OpenAI
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("请设置OPENROUTER_API_KEY环境变量")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

def search_celebrity(query: str):
    """
    使用sonar-pro-search搜索名人经历
    
    Args:
        query: 搜索查询文本
    
    Returns:
        搜索结果文本
    """
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://github.com/InspireMatch",
            "X-Title": "InspireMatch",
        },
        model="perplexity/sonar-pro-search",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            }
        ]
    )
    return completion.choices[0].message.content

if __name__ == "__main__":
    # 示例：搜索马化腾的创业经历
    query = "请介绍马化腾的创业经历"
    result = search_celebrity(query)
    print(result)



