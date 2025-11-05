"""
向量搜索示例：演示如何使用构建好的向量数据库进行检索
"""
import os
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

sys.path.insert(0, str(Path(__file__).parent))

from text_processing import TextProcessor
from elasticsearch_setup import ElasticsearchSetup


def search_experiences(query_text: str, size: int = 10, filter_tags: list = None):
    """
    搜索名人经历
    
    Args:
        query_text: 查询文本（例如："如何应对创业困难"）
        size: 返回结果数量
        filter_tags: 标签过滤条件（例如：["Entrepreneurial Challenges"]）
    
    Returns:
        搜索结果
    """
    # 环境变量已在文件开头加载
    
    # 初始化 TextProcessor，使用 Qwen 模型（如果未设置环境变量）
    # 优先使用环境变量 EMBEDDING_MODEL，否则使用 Qwen 模型
    embedding_model = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")
    text_processor = TextProcessor(model=embedding_model)
    es_setup = ElasticsearchSetup()
    index_name = os.getenv("ELASTICSEARCH_INDEX", "celebrity_experiences")
    
    # 生成查询向量
    print(f"生成查询向量: {query_text}")
    embedding = text_processor.get_embedding(query_text)
    if not embedding:
        print("生成向量失败")
        return None
    
    # 构建过滤条件
    filter_query = None
    if filter_tags:
        filter_query = {
            "terms": {
                "tags": filter_tags
            }
        }
        print(f"应用标签过滤: {filter_tags}")
    
    # 向量搜索
    print(f"执行向量搜索...")
    results = es_setup.vector_search(
        index_name, 
        embedding, 
        size=size,
        filter_query=filter_query
    )
    
    if results and "hits" in results:
        print(f"\n找到 {results['hits']['total']['value']} 条相关经历\n")
        
        for i, hit in enumerate(results['hits']['hits'], 1):
            source = hit['_source']
            score = hit['_score']
            
            print(f"{'='*60}")
            print(f"结果 {i} (相似度分数: {score:.4f})")
            print(f"{'='*60}")
            print(f"名人: {source.get('celebrity_name_cn', '')} ({source.get('celebrity_name_en', '')})")
            print(f"职业: {source.get('profession', '')}")
            print(f"事件摘要: {source.get('event_summary', '')}")
            print(f"挑战类型: {source.get('challenge_type', '')}")
            print(f"应对策略: {source.get('coping_strategy', '')}")
            print(f"最终结果: {source.get('final_result', '')}")
            print(f"标签: {', '.join(source.get('tags', []))}")
            print()
    
    return results


def keyword_search(query_text: str, size: int = 10):
    """
    关键词搜索（非向量搜索）
    
    Args:
        query_text: 查询文本
        size: 返回结果数量
    
    Returns:
        搜索结果
    """
    # 环境变量已在文件开头加载
    
    es_setup = ElasticsearchSetup()
    index_name = os.getenv("ELASTICSEARCH_INDEX", "celebrity_experiences")
    
    query = {
        "query": {
            "multi_match": {
                "query": query_text,
                "fields": ["event_summary", "coping_strategy", "final_result", "full_text"],
                "type": "best_fields"
            }
        }
    }
    
    results = es_setup.search(index_name, query, size=size)
    
    if results and "hits" in results:
        print(f"\n找到 {results['hits']['total']['value']} 条相关经历\n")
        
        for i, hit in enumerate(results['hits']['hits'], 1):
            source = hit['_source']
            score = hit['_score']
            
            print(f"{'='*60}")
            print(f"结果 {i} (相关性分数: {score:.4f})")
            print(f"{'='*60}")
            print(f"名人: {source.get('celebrity_name_cn', '')} ({source.get('celebrity_name_en', '')})")
            print(f"事件摘要: {source.get('event_summary', '')}")
            print(f"应对策略: {source.get('coping_strategy', '')}")
            print()
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="搜索名人经历")
    parser.add_argument("query", type=str, help="搜索查询文本")
    parser.add_argument("--size", type=int, default=10, help="返回结果数量")
    parser.add_argument("--tags", type=str, nargs="+", help="标签过滤条件")
    parser.add_argument("--keyword", action="store_true", help="使用关键词搜索而非向量搜索")
    
    args = parser.parse_args()
    
    if args.keyword:
        keyword_search(args.query, args.size)
    else:
        search_experiences(args.query, args.size, args.tags)



