"""
ElasticSearch配置模块：创建索引和映射
"""
from elasticsearch import Elasticsearch
import os
import re
from typing import Optional


class ElasticsearchSetup:
    def __init__(self, host: str = None, port: int = None):
        """
        初始化ElasticSearch连接
        
        Args:
            host: ElasticSearch主机地址
            port: ElasticSearch端口
        """
        self.host = host or os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.port = port or int(os.getenv("ELASTICSEARCH_PORT", "9200"))
        
        # 构建完整的URL（必须包含scheme）
        # Elasticsearch客户端需要完整的URL格式：http://host:port
        if self.host.startswith(("http://", "https://")):
            # host已经包含协议
            # 检查是否已经包含端口号（使用正则表达式匹配端口格式）
            port_pattern = r':\d+/?$'  # 匹配 :端口号 或 :端口号/
            if re.search(port_pattern, self.host):
                # 已经包含端口，直接使用
                es_url = self.host.rstrip('/')
            else:
                # 只有协议和host，需要添加端口
                es_url = f"{self.host.rstrip('/')}:{self.port}"
        else:
            # host不包含协议，添加http://和端口
            es_url = f"http://{self.host}:{self.port}"
        
        print(f"正在连接到ElasticSearch: {es_url}")
        
        # 检查客户端版本兼容性（ElasticSearch 8.x服务器只接受version 7或8的兼容头）
        try:
            import elasticsearch as es_module
            major_version = int(es_module.__version__.split('.')[0])
            if major_version >= 9:
                raise ValueError(
                    f"Elasticsearch客户端版本不兼容！\n"
                    f"当前版本: {es_module.__version__} (需要 < 9.0.0)\n"
                    f"ElasticSearch服务器版本: 8.11.0\n"
                    f"解决方案: pip install 'elasticsearch>=8.0.0,<9.0.0'"
                )
        except (ImportError, AttributeError):
            pass  # 版本检查失败不影响连接尝试
        
        # 创建Elasticsearch客户端
        self.es = Elasticsearch(
            hosts=[es_url],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        
        # 测试连接
        print("正在测试连接...")
        try:
            # 尝试ping，如果失败则尝试info()
            if not self.es.ping():
                info = self.es.info()
                print(f"警告: ping()返回False，但info()成功，集群: {info.get('cluster_name')}")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # 生成错误提示
            help_msg = (
                f"无法连接到ElasticSearch ({es_url})。\n"
                f"错误类型: {error_type}\n"
                f"错误信息: {error_msg}\n\n"
                f"请检查：\n"
                f"  1) ElasticSearch容器是否运行: docker-compose ps\n"
                f"  2) 测试连接: curl {es_url}\n"
                f"  3) 如果容器未运行，启动: docker-compose up -d"
            )
            
            # 如果是版本兼容性问题，提供额外提示
            if "media_type_header_exception" in error_msg or "compatible-with" in error_msg:
                help_msg += (
                    f"\n\n注意: 这可能是版本兼容性问题。\n"
                    f"请确保使用: pip install 'elasticsearch>=8.0.0,<9.0.0'"
                )
            
            raise ConnectionError(help_msg) from e
        
        print(f"✓ 成功连接到ElasticSearch: {es_url}")
    
    def create_index(self, index_name: str = None, delete_existing: bool = False) -> bool:
        """
        创建索引
        
        Args:
            index_name: 索引名称
            delete_existing: 如果索引已存在是否删除
        
        Returns:
            是否创建成功
        """
        if index_name is None:
            index_name = os.getenv("ELASTICSEARCH_INDEX", "celebrity_experiences")
        
        # 检查索引是否存在
        if self.es.indices.exists(index=index_name):
            if delete_existing:
                print(f"删除已存在的索引: {index_name}")
                self.es.indices.delete(index=index_name)
            else:
                print(f"索引 {index_name} 已存在")
                return True
        
        # 定义索引映射
        mapping = {
            "mappings": {
                "properties": {
                    "celebrity_name_en": {
                        "type": "keyword"
                    },
                    "celebrity_name_cn": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "profession": {
                        "type": "keyword"
                    },
                    "event_summary": {
                        "type": "text",
                        # "analyzer": "ik_max_word",  # 如果安装了IK分词器，可以取消注释
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "challenge_type": {
                        "type": "keyword"
                    },
                    "coping_strategy": {
                        "type": "text"
                    },
                    "final_result": {
                        "type": "text"
                    },
                    "tags": {
                        "type": "keyword"
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1024,  # text-embedding-3-small的维度（实际使用1024维）
                        "index": True,
                        "similarity": "cosine"
                    },
                    "chunk_id": {
                        "type": "keyword"
                    },
                    "full_text": {
                        "type": "text"
                    },
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "standard"
                        }
                    }
                }
            }
        }
        
        try:
            # 创建索引（兼容新旧版本API）
            try:
                # 新版本API
                self.es.indices.create(
                    index=index_name,
                    mappings=mapping["mappings"],
                    settings=mapping["settings"]
                )
            except TypeError:
                # 旧版本API使用body参数
                self.es.indices.create(index=index_name, body=mapping)
            print(f"成功创建索引: {index_name}")
            return True
        except Exception as e:
            print(f"创建索引失败: {str(e)}")
            return False
    
    def index_document(self, index_name: str, document: dict, doc_id: Optional[str] = None) -> bool:
        """
        索引单个文档
        
        Args:
            index_name: 索引名称
            document: 文档字典
            doc_id: 文档ID，如果为None则自动生成
        
        Returns:
            是否成功
        """
        try:
            if doc_id:
                self.es.index(index=index_name, id=doc_id, document=document)
            else:
                self.es.index(index=index_name, document=document)
            return True
        except Exception as e:
            print(f"索引文档失败: {str(e)}")
            return False
    
    def bulk_index(self, index_name: str, documents: list) -> int:
        """
        批量索引文档
        
        Args:
            index_name: 索引名称
            documents: 文档列表
        
        Returns:
            成功索引的文档数量
        """
        from elasticsearch.helpers import bulk
        
        actions = [
            {
                "_index": index_name,
                "_source": doc
            }
            for doc in documents
        ]
        
        try:
            success, failed = bulk(self.es, actions, raise_on_error=False)
            print(f"批量索引完成: 成功 {success}, 失败 {len(failed)}")
            
            # 打印详细的错误信息
            if failed:
                print(f"\n错误详情 (显示前10个):")
                for i, error_item in enumerate(failed[:10]):
                    error_info = error_item.get('index', {})
                    error_type = error_info.get('error', {}).get('type', 'unknown')
                    error_reason = error_info.get('error', {}).get('reason', 'unknown')
                    error_cause = error_info.get('error', {}).get('caused_by', {})
                    cause_type = error_cause.get('type', '') if error_cause else ''
                    cause_reason = error_cause.get('reason', '') if error_cause else ''
                    
                    print(f"\n错误 #{i+1}:")
                    print(f"  类型: {error_type}")
                    print(f"  原因: {error_reason}")
                    if cause_type:
                        print(f"  根因类型: {cause_type}")
                        print(f"  根因: {cause_reason}")
                
                if len(failed) > 10:
                    print(f"\n... 还有 {len(failed) - 10} 个错误未显示")
            
            return success
        except Exception as e:
            print(f"批量索引失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def search(self, index_name: str, query: dict, size: int = 10):
        """
        搜索文档
        
        Args:
            index_name: 索引名称
            query: 查询字典（包含query字段）
            size: 返回结果数量
        
        Returns:
            搜索结果
        """
        try:
            # 新版本API（8.x）
            result = self.es.search(index=index_name, query=query.get("query", {}), size=size)
            return result
        except TypeError:
            # 旧版本API（7.x）使用body参数
            result = self.es.search(index=index_name, body=query, size=size)
            return result
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return None
    
    def vector_search(self, index_name: str, embedding: list, size: int = 10, 
                     filter_query: dict = None) -> dict:
        """
        向量相似度搜索
        
        Args:
            index_name: 索引名称
            embedding: 查询向量
            size: 返回结果数量
            filter_query: 过滤条件
        
        Returns:
            搜索结果
        """
        # ElasticSearch 8.x 使用 knn 查询
        search_body = {
            "knn": {
                "field": "embedding",
                "query_vector": embedding,
                "k": size,
                "num_candidates": size * 10
            },
            "size": size
        }
        
        # 如果有过滤条件，添加到knn查询中
        if filter_query:
            search_body["knn"]["filter"] = filter_query
        
        try:
            # 新版本API
            result = self.es.search(index=index_name, **search_body)
            return result
        except Exception as e:
            # 如果knn不支持，回退到script_score
            try:
                query = {
                    "script_score": {
                        "query": {
                            "match_all": {}
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {
                                "query_vector": embedding
                            }
                        }
                    }
                }
                
                if filter_query:
                    query = {
                        "bool": {
                            "must": [query],
                            "filter": filter_query
                        }
                    }
                
                search_body_old = {
                    "query": query,
                    "size": size
                }
                
                return self.search(index_name, search_body_old, size)
            except Exception as e2:
                print(f"向量搜索失败: {str(e2)}")
                return None


if __name__ == "__main__":
    # 测试
    es_setup = ElasticsearchSetup()
    es_setup.create_index("celebrity_experiences", delete_existing=False)
    print("ElasticSearch设置完成")

