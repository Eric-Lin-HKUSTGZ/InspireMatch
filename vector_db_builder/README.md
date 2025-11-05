# 名人经历向量数据库构建工具

本工具用于构建名人经历的向量数据库，支持基于sonar-pro-search的搜索、结构化数据提取、标签匹配和ElasticSearch向量存储。

## 功能模块

1. **搜索模块** (`search_celebrity_experiences.py`): 使用sonar-pro-search搜索名人经历
2. **数据提取模块** (`extract_structured_data.py`): 从搜索结果中提取结构化JSON数据
3. **标签匹配模块** (`tag_matching.py`): 将经历与flags标签进行关联
4. **ElasticSearch配置** (`elasticsearch_setup.py`): 创建索引和映射
5. **文本处理模块** (`text_processing.py`): 文本切块和向量嵌入
6. **主流程脚本** (`build_vector_database.py`): 整合所有模块完成端到端流程

## 安装依赖

```bash
pip install -r ../requirements.txt
```

## 环境配置

1. 设置环境变量（或创建`.env`文件）:
```bash
export OPENROUTER_API_KEY=your_openrouter_api_key
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export ELASTICSEARCH_INDEX=celebrity_experiences
```

2. 启动ElasticSearch（使用Docker）:
```bash
cd ..
docker-compose up -d
```

等待ElasticSearch启动完成（约30秒），可以通过以下命令检查：
```bash
curl http://localhost:9200
```

## 使用方法

### 1. 构建向量数据库

运行主流程脚本：

```bash
python build_vector_database.py
```

该脚本会执行以下步骤：
1. 搜索所有名人的经历
2. 提取结构化数据
3. 匹配标签
4. 文本切块和向量嵌入
5. 存储到ElasticSearch

### 2. 断点续传

如果某个步骤失败，可以使用以下参数跳过已完成的步骤：

```bash
# 跳过搜索步骤（使用缓存）
python build_vector_database.py --skip-search

# 跳过搜索和提取步骤
python build_vector_database.py --skip-search --skip-extract

# 跳过搜索、提取和标签匹配
python build_vector_database.py --skip-search --skip-extract --skip-tags
```

### 3. 搜索示例

#### 向量搜索

```bash
python vector_search_example.py "如何应对创业困难" --size 5
```

#### 带标签过滤的向量搜索

```bash
python vector_search_example.py "如何应对创业困难" --tags "Entrepreneurial Challenges" --size 5
```

#### 关键词搜索

```bash
python vector_search_example.py "创业" --keyword --size 5
```

### 4. 在代码中使用

```python
from vector_search_example import search_experiences

# 向量搜索
results = search_experiences("如何应对职业挑战", size=10)

# 带标签过滤
results = search_experiences(
    "如何应对创业困难", 
    size=10, 
    filter_tags=["Entrepreneurial Challenges", "Lack of Startup Funds"]
)
```

## 数据格式

每条经历包含以下字段：

```json
{
  "celebrity_name_en": "Jack Ma",
  "celebrity_name_cn": "马云",
  "profession": "entrepreneurs",
  "event_summary": "事件摘要",
  "challenge_type": "挑战类型",
  "coping_strategy": "应对策略",
  "final_result": "最终结果",
  "tags": ["标签1", "标签2"],
  "embedding": [0.123, 0.456, ...],  // 1536维向量
  "chunk_id": "Jack Ma_0",
  "full_text": "完整文本内容"
}
```

## 缓存文件

构建过程中会在`cache/`目录下生成以下缓存文件：
- `search_results.json`: 搜索结果
- `experiences.json`: 提取的结构化数据
- `experiences_with_tags.json`: 带标签的经历数据
- `chunks_with_embeddings.json`: 处理后的chunks和向量

这些缓存文件可以用于断点续传或调试。

## 注意事项

1. **API限流**: 搜索和提取过程会调用OpenRouter API，请注意API限流。代码中已添加延迟以避免过快请求。

2. **ElasticSearch内存**: 默认配置使用512MB内存，如果数据量大可能需要调整`docker-compose.yml`中的内存设置。

3. **向量维度**: 使用`text-embedding-3-small`模型，向量维度为1536。

4. **文本切块**: 默认每个chunk最大500 tokens，可以根据需要调整。

## 故障排除

### ElasticSearch连接失败

检查ElasticSearch是否正在运行：
```bash
docker ps
curl http://localhost:9200
```

### API调用失败

检查环境变量是否正确设置：
```bash
echo $OPENROUTER_API_KEY
```

### 索引创建失败

如果索引已存在，可以删除后重新创建：
```python
from elasticsearch_setup import ElasticsearchSetup
es = ElasticsearchSetup()
es.es.indices.delete(index="celebrity_experiences")
es.create_index("celebrity_experiences")
```



