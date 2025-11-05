"""
文本处理模块：文本切块和向量嵌入
"""
from openai import OpenAI
import os
from typing import List, Dict, Any, Optional
import tiktoken
import time


class TextProcessor:
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        """
        初始化文本处理器
        
        Args:
            api_key: API密钥（优先从环境变量EMBEDDING_API_KEY读取，否则从OPENROUTER_API_KEY读取）
            model: 嵌入模型名称（优先从环境变量EMBEDDING_MODEL读取）
            base_url: API基础URL（优先从环境变量EMBEDDING_API_BASE_URL读取）
        """
        # 优先从环境变量读取自定义embedding配置
        self.base_url = base_url or os.getenv("EMBEDDING_API_BASE_URL")
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ValueError("API密钥未找到，请设置 EMBEDDING_API_KEY 或 OPENROUTER_API_KEY 环境变量")
        
        # 如果没有设置自定义端点，使用OpenRouter
        if not self.base_url:
            self.base_url = "https://openrouter.ai/api/v1"
        
        # 确保base_url以/v1结尾（OpenAI客户端会自动添加/embeddings）
        if not self.base_url.endswith("/v1"):
            if self.base_url.endswith("/v1/embeddings"):
                self.base_url = self.base_url.replace("/v1/embeddings", "/v1")
            elif self.base_url.endswith("/"):
                self.base_url = self.base_url.rstrip("/") + "/v1"
            else:
                self.base_url = self.base_url.rstrip("/") + "/v1"
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        # 模型名称：优先使用环境变量，否则使用传入参数，最后使用默认值
        if model:
            self.model = model
        elif os.getenv("EMBEDDING_MODEL"):
            self.model = os.getenv("EMBEDDING_MODEL")
        elif self.base_url != "https://openrouter.ai/api/v1":
            # 自定义端点，使用默认模型
            self.model = "Qwen/Qwen3-Embedding-0.6B"
        else:
            # OpenRouter，使用OpenAI模型
            self.model = "openai/text-embedding-3-small"
        
        # 从环境变量读取 OpenRouter headers（仅在使用OpenRouter时有效）
        self.extra_headers = {}
        if self.base_url == "https://openrouter.ai/api/v1":
            http_referer = os.getenv("OPENROUTER_HTTP_REFERER")
            x_title = os.getenv("OPENROUTER_X_TITLE")
            if http_referer:
                self.extra_headers["HTTP-Referer"] = http_referer
            if x_title:
                self.extra_headers["X-Title"] = x_title
        
        self.encoding = tiktoken.get_encoding("cl100k_base")  # text-embedding-3-small使用的编码
        
        # 打印配置信息（用于调试）
        print(f"[TextProcessor] 初始化完成:")
        print(f"  API端点: {self.base_url}")
        print(f"  模型: {self.model}")
        print(f"  API密钥: {'已设置' if self.api_key else '未设置'}")
    
    def chunk_text(self, text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
        """
        将文本切分为chunks
        
        Args:
            text: 输入文本
            max_tokens: 每个chunk的最大token数
            overlap: chunk之间的重叠token数
        
        Returns:
            chunk列表
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # 将文本编码为tokens
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # 获取当前chunk的tokens
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # 解码为文本
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # 移动到下一个chunk，考虑重叠
            start = end - overlap
            if start >= len(tokens):
                break
        
        return chunks
    
    def chunk_experience(self, experience: Dict[str, Any], 
                        max_tokens: int = 500) -> List[Dict[str, Any]]:
        """
        将单条经历切分为chunks
        
        Args:
            experience: 经历字典
            max_tokens: 每个chunk的最大token数
        
        Returns:
            chunk列表，每个chunk包含原始字段和chunk_id
        """
        # 构建完整文本用于切块
        full_text_parts = [
            f"事件摘要：{experience.get('event_summary', '')}",
            f"挑战类型：{experience.get('challenge_type', '')}",
            f"应对策略：{experience.get('coping_strategy', '')}",
            f"最终结果：{experience.get('final_result', '')}"
        ]
        full_text = "\n".join(full_text_parts)
        
        # 切块
        text_chunks = self.chunk_text(full_text, max_tokens=max_tokens)
        
        # 为每个chunk创建文档
        chunk_docs = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_doc = experience.copy()
            chunk_doc["full_text"] = chunk_text
            chunk_doc["chunk_id"] = f"{experience.get('celebrity_name_en', 'unknown')}_{i}"
            chunk_docs.append(chunk_doc)
        
        return chunk_docs
    
    def get_embedding(self, text: str, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒），会指数增长
        
        Returns:
            向量列表，失败时返回None
        """
        # 输入验证：检查空文本
        if not text or not text.strip():
            print(f"警告: 输入文本为空，跳过嵌入向量生成")
            return None
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                # 使用OpenRouter调用OpenAI的嵌入API
                # 根据OpenRouter官方文档格式调用
                create_params = {
                    "model": self.model,
                    "input": text,
                    "encoding_format": "float"
                }
                
                # 如果有额外的headers，添加到调用中
                if self.extra_headers:
                    create_params["extra_headers"] = self.extra_headers
                
                response = self.client.embeddings.create(**create_params)
                
                # 首先检查响应中是否有错误
                if hasattr(response, 'error') and response.error:
                    error_info = response.error
                    if isinstance(error_info, dict):
                        error_msg = error_info.get('message', 'Unknown error')
                        error_code = error_info.get('code', 'Unknown')
                    else:
                        error_msg = str(error_info)
                        error_code = 'Unknown'
                    print(f"获取嵌入向量失败: API返回错误 (code: {error_code}): {error_msg}")
                    print(f"使用的模型: {self.model}")
                    print(f"API端点: {self.base_url}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                # 验证响应结构
                if not hasattr(response, 'data'):
                    print(f"获取嵌入向量失败: 响应中没有 'data' 字段")
                    print(f"响应类型: {type(response)}")
                    print(f"响应属性: {dir(response)}")
                    if hasattr(response, 'error'):
                        print(f"响应错误: {response.error}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                if not response.data:
                    print(f"获取嵌入向量失败: 'data' 字段为空")
                    print(f"响应内容: {response}")
                    if hasattr(response, 'error') and response.error:
                        print(f"API错误信息: {response.error}")
                    print(f"使用的模型: {self.model}")
                    print(f"API端点: {self.base_url}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                if len(response.data) == 0:
                    print(f"获取嵌入向量失败: 'data' 数组为空")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                # 获取第一个嵌入向量
                embedding_obj = response.data[0]
                
                if not hasattr(embedding_obj, 'embedding'):
                    print(f"获取嵌入向量失败: 响应对象中没有 'embedding' 字段")
                    print(f"响应对象类型: {type(embedding_obj)}")
                    print(f"响应对象属性: {dir(embedding_obj)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                embedding = embedding_obj.embedding
                
                # 验证嵌入向量是否有效
                if not embedding:
                    print(f"获取嵌入向量失败: embedding 字段为空")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                if not isinstance(embedding, list) or len(embedding) == 0:
                    print(f"获取嵌入向量失败: embedding 不是有效的列表或为空列表")
                    print(f"embedding 类型: {type(embedding)}, 长度: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return None
                
                # 成功获取嵌入向量
                return embedding
                
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                # 详细错误日志
                print(f"获取嵌入向量失败 (尝试 {attempt + 1}/{max_retries}): {error_type}: {error_msg}")
                
                # 如果是最后一次尝试，打印更多调试信息
                if attempt == max_retries - 1:
                    print(f"文本内容 (前100字符): {text[:100] if len(text) > 100 else text}")
                    print(f"模型: {self.model}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    def process_experience(self, experience: Dict[str, Any], 
                          max_tokens: int = 500) -> List[Dict[str, Any]]:
        """
        处理单条经历：切块并生成嵌入
        
        Args:
            experience: 经历字典
            max_tokens: 每个chunk的最大token数
        
        Returns:
            处理后的chunk列表，每个chunk包含embedding字段
        """
        # 切块
        chunks = self.chunk_experience(experience, max_tokens=max_tokens)
        
        # 为每个chunk生成嵌入
        for chunk in chunks:
            # 使用full_text生成嵌入
            embedding = self.get_embedding(chunk["full_text"])
            if embedding:
                chunk["embedding"] = embedding
            else:
                # 如果失败，使用event_summary作为备选
                fallback_text = chunk.get("event_summary", "")
                if fallback_text:
                    embedding = self.get_embedding(fallback_text)
                    if embedding:
                        chunk["embedding"] = embedding
                    else:
                        print(f"警告: chunk {chunk.get('chunk_id', 'unknown')} 的嵌入向量生成失败（包括备选方案）")
                        chunk["embedding"] = []
                else:
                    print(f"警告: chunk {chunk.get('chunk_id', 'unknown')} 的嵌入向量生成失败，且没有可用的备选文本")
                    chunk["embedding"] = []
        
        return chunks
    
    def process_all_experiences(self, experiences: List[Dict[str, Any]], 
                               max_tokens: int = 500) -> List[Dict[str, Any]]:
        """
        批量处理所有经历
        
        Args:
            experiences: 经历列表
            max_tokens: 每个chunk的最大token数
        
        Returns:
            所有处理后的chunks
        """
        all_chunks = []
        
        print(f"\n开始处理 {len(experiences)} 条经历...")
        
        for i, exp in enumerate(experiences):
            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{len(experiences)} 条经历")
            
            chunks = self.process_experience(exp, max_tokens=max_tokens)
            all_chunks.extend(chunks)
            
            # 添加延迟以避免API限流
            if (i + 1) % 5 == 0:
                import time
                time.sleep(0.5)
        
        print(f"处理完成，共生成 {len(all_chunks)} 个chunks")
        return all_chunks


if __name__ == "__main__":
    processor = TextProcessor()
    
    # 测试
    test_text = "这是一段测试文本。" * 100
    chunks = processor.chunk_text(test_text, max_tokens=50)
    print(f"切分为 {len(chunks)} 个chunks")
    
    # 测试嵌入
    embedding = processor.get_embedding("测试文本")
    print(f"嵌入向量维度: {len(embedding) if embedding else 0}")


