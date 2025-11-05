"""
搜索模块：使用sonar-pro-search搜索名人经历
"""
from openai import OpenAI
import os
from typing import List, Dict, Tuple
from pathlib import Path


class CelebrityExperienceSearcher:
    def __init__(self, api_key: str = None):
        """
        初始化搜索器
        
        Args:
            api_key: OpenRouter API密钥，如果为None则从环境变量读取
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
    
    def search_celebrity_experiences(self, celebrity_name_en: str, celebrity_name_cn: str) -> str:
        """
        搜索单个名人的经历
        
        Args:
            celebrity_name_en: 名人英文名
            celebrity_name_cn: 名人中文名
        
        Returns:
            搜索结果的文本内容
        """
        query = f"请详细介绍{celebrity_name_cn}({celebrity_name_en})的人生经历、面临的挑战、应对策略和最终结果。包括职业发展、创业历程、遇到的困难、如何克服困难以及取得的成就。"
        
        try:
            completion = self.client.chat.completions.create(
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
        except Exception as e:
            print(f"搜索 {celebrity_name_cn} 时出错: {str(e)}")
            return ""
    
    def load_celebrities(self, data_dir: str = None) -> Dict[str, List[Tuple[str, str]]]:
        """
        从文件加载所有名人列表
        
        Args:
            data_dir: 数据目录路径，默认为项目根目录下的data_construct/celebrity_deeds
        
        Returns:
            字典，键为职业名称，值为(英文名, 中文名)元组列表
        """
        if data_dir is None:
            # 获取当前文件所在目录的父目录的父目录
            current_dir = Path(__file__).parent.parent
            data_dir = current_dir / "data_construct" / "celebrity_deeds"
        else:
            data_dir = Path(data_dir)
        
        celebrities = {}
        
        # 职业文件映射
        profession_files = {
            "politicians": "politicians.txt",
            "scientists": "scientists.txt",
            "entrepreneurs": "entrepreneurs.txt",
            "artists": "artists.txt",
            "athletes": "athletes.txt",
            "actors_entertainers": "actors_entertainers.txt",
            "writers_philosophers": "writers_philosophers.txt",
            "activists": "activists.txt",
            "educators": "educators.txt",
        }
        
        for profession, filename in profession_files.items():
            file_path = data_dir / filename
            if file_path.exists():
                celebrities[profession] = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '--' in line:
                            parts = line.split('--')
                            if len(parts) == 2:
                                celebrities[profession].append((parts[0].strip(), parts[1].strip()))
        
        return celebrities
    
    def search_all_celebrities(self, data_dir: str = None) -> Dict[str, Dict[str, str]]:
        """
        搜索所有名人的经历
        
        Args:
            data_dir: 数据目录路径
        
        Returns:
            嵌套字典：{职业: {名人英文名: 搜索结果文本}}
        """
        celebrities = self.load_celebrities(data_dir)
        results = {}
        
        for profession, celeb_list in celebrities.items():
            print(f"\n开始搜索 {profession} 职业的名人...")
            results[profession] = {}
            
            for en_name, cn_name in celeb_list:
                print(f"  搜索: {cn_name} ({en_name})")
                search_result = self.search_celebrity_experiences(en_name, cn_name)
                results[profession][en_name] = {
                    "chinese_name": cn_name,
                    "search_result": search_result
                }
                # 添加延迟以避免API限流
                import time
                time.sleep(1)
        
        return results


if __name__ == "__main__":
    searcher = CelebrityExperienceSearcher()
    results = searcher.search_all_celebrities()
    print(f"\n搜索完成，共搜索 {sum(len(v) for v in results.values())} 位名人")

