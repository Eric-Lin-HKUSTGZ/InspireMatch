# 快速启动指南

## 1. 安装依赖

```bash
cd /home/linweiquan/InspireMatch
pip install -r requirements.txt
```

## 2. 配置环境变量

创建`.env`文件或设置环境变量：

```bash
export OPENROUTER_API_KEY=your_openrouter_api_key_here
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export ELASTICSEARCH_INDEX=celebrity_experiences
```

## 3. 启动ElasticSearch

```bash
docker-compose up -d
```

等待ElasticSearch启动（约30秒），然后验证：

```bash
curl http://localhost:9200
```

## 4. 构建向量数据库

```bash
cd vector_db_builder
python build_vector_database.py
```

这个过程会：
- 搜索所有名人的经历（使用sonar-pro-search）
- 提取结构化数据
- 匹配标签
- 生成向量嵌入
- 存储到ElasticSearch

**注意**: 整个过程可能需要较长时间，因为需要调用API搜索和提取数据。建议在后台运行或使用断点续传功能。

## 5. 搜索示例

### 向量搜索

```bash
python vector_search_example.py "如何应对创业困难" --size 5
```

### 带标签过滤

```bash
python vector_search_example.py "如何应对创业困难" --tags "Entrepreneurial Challenges" --size 5
```

### 关键词搜索

```bash
python vector_search_example.py "创业" --keyword --size 5
```

## 断点续传

如果构建过程中断，可以使用以下命令从断点继续：

```bash
# 跳过已完成的搜索步骤
python build_vector_database.py --skip-search

# 跳过搜索和提取
python build_vector_database.py --skip-search --skip-extract

# 跳过搜索、提取和标签匹配
python build_vector_database.py --skip-search --skip-extract --skip-tags
```

## 在Python代码中使用

```python
from vector_search_example import search_experiences

# 搜索相关经历
results = search_experiences("如何应对职业挑战", size=10)

# 带标签过滤
results = search_experiences(
    "如何应对创业困难",
    size=10,
    filter_tags=["Entrepreneurial Challenges"]
)
```

## 故障排除

### ElasticSearch连接失败

```bash
# 检查容器状态
docker ps

# 查看日志
docker logs inspirematch_elasticsearch

# 重启容器
docker-compose restart
```

### API调用失败

检查环境变量：
```bash
echo $OPENROUTER_API_KEY
```

### 索引问题

删除并重建索引：
```python
from elasticsearch_setup import ElasticsearchSetup
es = ElasticsearchSetup()
es.es.indices.delete(index="celebrity_experiences", ignore=[404])
es.create_index("celebrity_experiences")
```



