"""
标签匹配模块：将经历与flags标签进行关联
"""
from openai import OpenAI
import os
from typing import List, Dict, Any
from pathlib import Path
import json


class TagMatcher:
    def __init__(self, api_key: str = None, flags_dir: str = None):
        """
        初始化标签匹配器
        
        Args:
            api_key: OpenRouter API密钥
            flags_dir: flags目录路径
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # 加载所有标签
        if flags_dir is None:
            current_dir = Path(__file__).parent.parent
            flags_dir = current_dir / "data_construct" / "flags"
        else:
            flags_dir = Path(flags_dir)
        
        self.tags = self._load_tags(flags_dir)
    
    def _load_tags(self, flags_dir: Path) -> Dict[str, List[Dict[str, str]]]:
        """
        加载所有标签文件
        
        Args:
            flags_dir: flags目录路径
        
        Returns:
            字典，键为标签类别名，值为标签列表（每个标签包含en和cn）
        """
        tags = {}
        
        flag_files = {
            "career_development_and_challenges": "career_development_and_challenges.txt",
            "mental_health_emotional_challenges": "mental_health_emotional_challenges.txt",
            "personal_growth_and_self-improvement": "personal_growth_and_self-improvement.txt",
            "relationships_interpersonal_communication": "relationships_interpersonal_communication.txt",
            "financial_life_challenges": "financial_life_challenges.txt",
            "physical_health_fitness": "physical_health_fitness.txt",
            "enterpreneurship_and_innovation": "enterpreneurship_and_innovation.txt",
            "education_and_learning": "education_and_learning.txt",
            "social_responsibility_and_impact": "social_responsibility_and_impact.txt",
            "resilience_and_comebacks": "resilience_and_comebacks.txt",
        }
        
        for category, filename in flag_files.items():
            file_path = flags_dir / filename
            if file_path.exists():
                tags[category] = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '--' in line:
                            parts = line.split('--')
                            if len(parts) == 2:
                                tags[category].append({
                                    "en": parts[0].strip(),
                                    "cn": parts[1].strip()
                                })
        
        return tags
    
    def match_tags(self, experience: Dict[str, Any], use_llm: bool = True) -> List[str]:
        """
        为单条经历匹配标签
        
        Args:
            experience: 经历字典
            use_llm: 是否使用LLM进行匹配，False则仅使用关键词匹配
        
        Returns:
            标签列表（英文标签名）
        """
        # 先进行关键词匹配
        keyword_tags = self._keyword_match(experience)
        
        if not use_llm:
            return keyword_tags[:3]  # 最多返回3个标签
        
        # 使用LLM进行更精确的匹配
        llm_tags = self._llm_match(experience, keyword_tags)
        
        # 合并结果，去重，最多返回3个
        all_tags = list(set(keyword_tags + llm_tags))
        return all_tags[:3]
    
    def _keyword_match(self, experience: Dict[str, Any]) -> List[str]:
        """
        基于关键词的标签匹配
        
        Args:
            experience: 经历字典
        
        Returns:
            匹配到的标签列表
        """
        matched_tags = []
        
        # 构建搜索文本
        search_text = " ".join([
            experience.get("event_summary", ""),
            experience.get("challenge_type", ""),
            experience.get("coping_strategy", ""),
            experience.get("final_result", "")
        ]).lower()
        
        # 遍历所有标签进行匹配
        for category, tag_list in self.tags.items():
            for tag in tag_list:
                tag_en = tag["en"].lower()
                tag_cn = tag["cn"]
                
                # 检查英文标签关键词
                if any(keyword in search_text for keyword in tag_en.split() if len(keyword) > 3):
                    matched_tags.append(tag["en"])
                    continue
                
                # 检查中文标签
                if tag_cn in search_text or any(char in search_text for char in tag_cn):
                    matched_tags.append(tag["en"])
        
        return matched_tags
    
    def _llm_match(self, experience: Dict[str, Any], keyword_tags: List[str]) -> List[str]:
        """
        使用LLM进行标签匹配
        
        Args:
            experience: 经历字典
            keyword_tags: 关键词匹配的结果
        
        Returns:
            匹配到的标签列表
        """
        # 构建所有可用标签的列表
        all_tags_list = []
        for category, tag_list in self.tags.items():
            for tag in tag_list:
                all_tags_list.append(f"{tag['en']} ({tag['cn']})")
        
        tags_text = "\n".join([f"- {tag}" for tag in all_tags_list])
        
        prompt = f"""请为以下名人经历匹配最相关的标签（1-3个）。

经历信息：
- 事件摘要：{experience.get('event_summary', '')}
- 挑战类型：{experience.get('challenge_type', '')}
- 应对策略：{experience.get('coping_strategy', '')}
- 最终结果：{experience.get('final_result', '')}

可用标签列表：
{tags_text}

关键词匹配结果（仅供参考）：{', '.join(keyword_tags) if keyword_tags else '无'}

请选择1-3个最相关的标签，只返回标签的英文名，用逗号分隔。如果关键词匹配结果合理，可以优先使用。只返回标签名，不要其他说明。"""

        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/InspireMatch",
                    "X-Title": "InspireMatch",
                },
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            
            response = completion.choices[0].message.content.strip()
            
            # 解析响应
            matched_tags = []
            for tag_name in response.split(','):
                tag_name = tag_name.strip()
                # 验证标签是否存在
                for category, tag_list in self.tags.items():
                    for tag in tag_list:
                        if tag["en"] == tag_name or tag_name in tag["en"]:
                            matched_tags.append(tag["en"])
                            break
            
            return matched_tags[:3]
            
        except Exception as e:
            print(f"LLM标签匹配出错: {str(e)}")
            return keyword_tags[:3]  # 失败时返回关键词匹配结果
    
    def match_all_experiences(self, experiences: List[Dict[str, Any]], 
                             use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        为所有经历匹配标签
        
        Args:
            experiences: 经历列表
            use_llm: 是否使用LLM
        
        Returns:
            添加了tags字段的经历列表
        """
        print(f"\n开始为 {len(experiences)} 条经历匹配标签...")
        
        for i, exp in enumerate(experiences):
            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{len(experiences)} 条经历")
            
            tags = self.match_tags(exp, use_llm=use_llm)
            exp["tags"] = tags
            
            # 添加延迟
            if use_llm and (i + 1) % 5 == 0:
                import time
                time.sleep(0.5)
        
        print(f"标签匹配完成")
        return experiences


if __name__ == "__main__":
    matcher = TagMatcher()
    
    # 测试
    test_experience = {
        "celebrity_name_en": "Jack Ma",
        "celebrity_name_cn": "马云",
        "event_summary": "阿里巴巴创业初期面临资金短缺问题",
        "challenge_type": "创业困难",
        "coping_strategy": "通过寻找投资人和合作伙伴解决资金问题",
        "final_result": "成功获得投资，公司得以发展"
    }
    
    tags = matcher.match_tags(test_experience)
    print(f"匹配到的标签: {tags}")



