"""
数据提取模块：从搜索结果中提取结构化JSON数据
"""
from openai import OpenAI
import os
import json
from typing import List, Dict, Any
import re


class StructuredDataExtractor:
    def __init__(self, api_key: str = None, model: str = "openai/gpt-4o-mini"):
        """
        初始化提取器
        
        Args:
            api_key: OpenRouter API密钥
            model: 用于提取的模型，默认使用gpt-4o-mini
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        self.model = model
    
    def extract_experiences(self, celebrity_name_en: str, celebrity_name_cn: str, 
                           search_result: str) -> List[Dict[str, Any]]:
        """
        从搜索结果中提取结构化经历数据
        
        Args:
            celebrity_name_en: 名人英文名
            celebrity_name_cn: 名人中文名
            search_result: 搜索结果文本
        
        Returns:
            经历列表，每个经历是一个字典
        """
        if not search_result or len(search_result.strip()) < 50:
            return []
        
        prompt = f"""请从以下关于{celebrity_name_cn}({celebrity_name_en})的搜索结果中，提取出具体的经历事件。

要求：
1. 每条经历应该是一个独立的事件或挑战
2. 提取尽可能多的经历（至少3-5条，如果内容足够多可以提取更多）
3. 每条经历必须包含以下字段：
   - event_summary: 事件摘要（简要描述发生了什么）
   - challenge_type: 挑战类型（如：职业挑战、创业困难、个人成长等）
   - coping_strategy: 应对策略（描述如何应对挑战）
   - final_result: 最终结果（描述最终取得了什么成果）

请以JSON数组格式返回，格式如下：
[
  {{
    "event_summary": "事件摘要",
    "challenge_type": "挑战类型",
    "coping_strategy": "应对策略",
    "final_result": "最终结果"
  }},
  ...
]

搜索结果：
{search_result[:8000]}  # 限制长度避免token过多

请直接返回JSON数组，不要添加任何其他文字说明。"""

        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/InspireMatch",
                    "X-Title": "InspireMatch",
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # 尝试提取JSON
            json_data = self._parse_json_response(response_text)
            
            # 验证和清理数据
            experiences = []
            for exp in json_data:
                if isinstance(exp, dict):
                    # 添加名人姓名
                    exp["celebrity_name_en"] = celebrity_name_en
                    exp["celebrity_name_cn"] = celebrity_name_cn
                    
                    # 验证必需字段
                    required_fields = ["event_summary", "challenge_type", "coping_strategy", "final_result"]
                    if all(field in exp and exp[field] for field in required_fields):
                        # 清理文本
                        for field in required_fields:
                            if isinstance(exp[field], str):
                                exp[field] = exp[field].strip()
                        experiences.append(exp)
            
            return experiences
            
        except Exception as e:
            print(f"提取 {celebrity_name_cn} 的经历时出错: {str(e)}")
            return []
    
    def _parse_json_response(self, text: str) -> List[Dict]:
        """
        从响应文本中解析JSON
        
        Args:
            text: 响应文本
        
        Returns:
            JSON对象列表
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试查找第一个 [ 到最后一个 ] 之间的内容
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
        
        # 如果都失败了，返回空列表
        print(f"无法解析JSON响应: {text[:200]}...")
        return []
    
    def extract_all(self, search_results: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        批量提取所有名人的经历
        
        Args:
            search_results: 搜索结果字典，格式为 {职业: {名人英文名: {chinese_name, search_result}}}
        
        Returns:
            所有经历的列表
        """
        all_experiences = []
        
        for profession, celebrities in search_results.items():
            print(f"\n提取 {profession} 职业的经历...")
            for en_name, data in celebrities.items():
                cn_name = data.get("chinese_name", "")
                search_result = data.get("search_result", "")
                
                print(f"  提取: {cn_name} ({en_name})")
                experiences = self.extract_experiences(en_name, cn_name, search_result)
                
                # 添加职业信息
                for exp in experiences:
                    exp["profession"] = profession
                
                all_experiences.extend(experiences)
                print(f"    提取到 {len(experiences)} 条经历")
                
                # 添加延迟
                import time
                time.sleep(0.5)
        
        return all_experiences


if __name__ == "__main__":
    extractor = StructuredDataExtractor()
    # 示例用法
    test_result = "这里是搜索结果..."
    experiences = extractor.extract_experiences("Jack Ma", "马云", test_result)
    print(json.dumps(experiences, ensure_ascii=False, indent=2))

