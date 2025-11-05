"""
主流程脚本：构建名人经历向量数据库
"""
import os
import json
import sys
import re
from pathlib import Path

# 尝试加载python-dotenv，如果不存在则使用自定义加载函数
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

def load_env_file(env_path: Path):
    """
    加载.env文件，支持两种格式：
    1. KEY=value (标准格式)
    2. export KEY=value (shell格式)
    """
    if not env_path.exists():
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 移除export关键字（如果存在）
            line = re.sub(r'^export\s+', '', line)
            
            # 解析KEY=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 移除引号（如果存在）
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # 设置环境变量
                os.environ[key] = value
    
    return True

# 加载环境变量（必须在导入其他模块之前）
# 首先尝试从项目根目录的env/.env加载
env_path = Path(__file__).parent.parent / "env" / ".env"
if env_path.exists():
    if HAS_DOTENV:
        load_dotenv(env_path)
    else:
        load_env_file(env_path)
else:
    # 如果不存在，尝试从项目根目录的.env加载
    root_env = Path(__file__).parent.parent / ".env"
    if root_env.exists():
        if HAS_DOTENV:
            load_dotenv(root_env)
        else:
            load_env_file(root_env)
    else:
        # 最后尝试默认位置（如果使用dotenv）
        if HAS_DOTENV:
            load_dotenv()

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from search_celebrity_experiences import CelebrityExperienceSearcher
from extract_structured_data import StructuredDataExtractor
from tag_matching import TagMatcher
from text_processing import TextProcessor
from elasticsearch_setup import ElasticsearchSetup


class VectorDatabaseBuilder:
    def __init__(self):
        """初始化构建器"""
        # 环境变量已在文件开头加载，这里直接初始化各个模块
        self.searcher = CelebrityExperienceSearcher()
        self.extractor = StructuredDataExtractor()
        self.tag_matcher = TagMatcher()
        self.text_processor = TextProcessor()
        self.es_setup = ElasticsearchSetup()
        
        # 获取索引名称
        self.index_name = os.getenv("ELASTICSEARCH_INDEX", "celebrity_experiences")
    
    def build(self, skip_search: bool = False, skip_extract: bool = False, 
              skip_tags: bool = False, skip_processing: bool = False,
              cache_dir: str = None):
        """
        构建向量数据库
        
        Args:
            skip_search: 是否跳过搜索步骤（使用缓存）
            skip_extract: 是否跳过提取步骤（使用缓存）
            skip_tags: 是否跳过标签匹配步骤（使用缓存）
            skip_processing: 是否跳过文本处理步骤（使用缓存）
            cache_dir: 缓存目录路径
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / "cache"
        else:
            cache_dir = Path(cache_dir)
        cache_dir.mkdir(exist_ok=True)
        
        # 1. 搜索名人经历
        search_results = None
        if not skip_search:
            print("=" * 60)
            print("步骤 1/5: 搜索名人经历")
            print("=" * 60)
            search_results = self.searcher.search_all_celebrities()
            
            # 保存搜索结果
            cache_file = cache_dir / "search_results.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(search_results, f, ensure_ascii=False, indent=2)
            print(f"搜索结果已保存到: {cache_file}")
        else:
            # 加载缓存的搜索结果
            cache_file = cache_dir / "search_results.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    search_results = json.load(f)
                print(f"从缓存加载搜索结果: {cache_file}")
            else:
                raise FileNotFoundError(f"缓存文件不存在: {cache_file}")
        
        # 2. 提取结构化数据
        experiences = None
        if not skip_extract:
            print("\n" + "=" * 60)
            print("步骤 2/5: 提取结构化数据")
            print("=" * 60)
            experiences = self.extractor.extract_all(search_results)
            
            # 保存提取结果
            cache_file = cache_dir / "experiences.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(experiences, f, ensure_ascii=False, indent=2)
            print(f"提取结果已保存到: {cache_file}")
            print(f"共提取 {len(experiences)} 条经历")
        else:
            # 加载缓存的提取结果
            cache_file = cache_dir / "experiences.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    experiences = json.load(f)
                print(f"从缓存加载提取结果: {cache_file}")
                print(f"共 {len(experiences)} 条经历")
            else:
                raise FileNotFoundError(f"缓存文件不存在: {cache_file}")
        
        # 3. 标签匹配
        if not skip_tags:
            print("\n" + "=" * 60)
            print("步骤 3/5: 标签匹配")
            print("=" * 60)
            experiences = self.tag_matcher.match_all_experiences(experiences, use_llm=True)
            
            # 保存标签匹配结果
            cache_file = cache_dir / "experiences_with_tags.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(experiences, f, ensure_ascii=False, indent=2)
            print(f"标签匹配结果已保存到: {cache_file}")
        else:
            # 加载缓存的标签匹配结果
            cache_file = cache_dir / "experiences_with_tags.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    experiences = json.load(f)
                print(f"从缓存加载标签匹配结果: {cache_file}")
            else:
                # 如果没有标签匹配缓存，尝试加载普通经历并匹配标签
                cache_file = cache_dir / "experiences.json"
                if cache_file.exists():
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        experiences = json.load(f)
                    experiences = self.tag_matcher.match_all_experiences(experiences, use_llm=True)
        
        # 4. 文本处理和向量嵌入
        chunks = None
        if not skip_processing:
            print("\n" + "=" * 60)
            print("步骤 4/5: 文本切块和向量嵌入")
            print("=" * 60)
            chunks = self.text_processor.process_all_experiences(experiences, max_tokens=500)
            
            # 保存处理结果
            cache_file = cache_dir / "chunks_with_embeddings.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            print(f"处理结果已保存到: {cache_file}")
            print(f"共生成 {len(chunks)} 个chunks")
        else:
            # 加载缓存的处理结果
            cache_file = cache_dir / "chunks_with_embeddings.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                print(f"从缓存加载处理结果: {cache_file}")
                print(f"共 {len(chunks)} 个chunks")
            else:
                raise FileNotFoundError(f"缓存文件不存在: {cache_file}")
        
        # 5. 存储到ElasticSearch
        print("\n" + "=" * 60)
        print("步骤 5/5: 存储到ElasticSearch")
        print("=" * 60)
        
        # 创建索引
        self.es_setup.create_index(self.index_name, delete_existing=False)
        
        # 批量索引
        success_count = self.es_setup.bulk_index(self.index_name, chunks)
        
        # 如果索引失败，尝试删除并重建索引（可能是映射不匹配）
        if success_count == 0 and len(chunks) > 0:
            print("\n检测到索引失败，尝试删除并重建索引（可能是映射不匹配）...")
            self.es_setup.create_index(self.index_name, delete_existing=True)
            success_count = self.es_setup.bulk_index(self.index_name, chunks)
        
        print(f"\n向量数据库构建完成！")
        print(f"成功索引 {success_count} 个文档到索引: {self.index_name}")
    
    def search_experiences(self, query_text: str, size: int = 10, 
                          filter_tags: list = None):
        """
        搜索经历（示例）
        
        Args:
            query_text: 查询文本
            size: 返回结果数量
            filter_tags: 标签过滤条件
        
        Returns:
            搜索结果
        """
        # 生成查询向量
        embedding = self.text_processor.get_embedding(query_text)
        if not embedding:
            return None
        
        # 构建过滤条件
        filter_query = None
        if filter_tags:
            filter_query = {
                "terms": {
                    "tags": filter_tags
                }
            }
        
        # 向量搜索
        results = self.es_setup.vector_search(
            self.index_name, 
            embedding, 
            size=size,
            filter_query=filter_query
        )
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="构建名人经历向量数据库")
    parser.add_argument("--skip-search", action="store_true", help="跳过搜索步骤")
    parser.add_argument("--skip-extract", action="store_true", help="跳过提取步骤")
    parser.add_argument("--skip-tags", action="store_true", help="跳过标签匹配步骤")
    parser.add_argument("--skip-processing", action="store_true", help="跳过文本处理步骤")
    parser.add_argument("--cache-dir", type=str, help="缓存目录路径")
    
    args = parser.parse_args()
    
    builder = VectorDatabaseBuilder()
    builder.build(
        skip_search=args.skip_search,
        skip_extract=args.skip_extract,
        skip_tags=args.skip_tags,
        skip_processing=args.skip_processing,
        cache_dir=args.cache_dir
    )


if __name__ == "__main__":
    main()

