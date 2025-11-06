# InspireMatch

名人经历向量数据库构建与检索系统

## 项目简介

InspireMatch 是一个基于 RAG（检索增强生成）技术的名人经历知识库系统。系统通过搜索、提取、结构化存储名人的经历故事，构建向量数据库，支持高效的语义检索和关键词检索，为用户提供灵感与指导。

## 核心功能

- 🔍 **智能搜索**: 使用 sonar-pro-search 搜索9个职业领域的名人经历
- 📊 **结构化提取**: 使用 LLM 从搜索结果中提取结构化数据（事件摘要、挑战类型、应对策略、最终结果等）
- 🏷️ **标签匹配**: 自动为经历匹配10种类型的标签，便于分类检索
- 📚 **向量数据库**: 基于 ElasticSearch 构建向量数据库，支持语义相似度搜索
- 🎯 **多种检索方式**: 支持向量搜索、关键词搜索和标签过滤

## 项目结构

```
InspireMatch/
├── data_construct/                  # 数据构建相关
│   ├── celebrity_deeds/            # 名人列表（9个职业）
│   │   ├── entrepreneurs.txt
│   │   ├── politicians.txt
│   │   ├── scientists.txt
│   │   └── ...
│   └── flags/                      # 经历标签（10种类型）
│       ├── career_development_and_challenges.txt
│       ├── enterpreneurship_and_innovation.txt
│       └── ...
│
├── vector_db_builder/              # 向量数据库构建工具
│   ├── search_celebrity_experiences.py  # 搜索模块
│   ├── extract_structured_data.py      # 数据提取模块
│   ├── tag_matching.py                 # 标签匹配模块
│   ├── text_processing.py              # 文本处理模块
│   ├── elasticsearch_setup.py          # ES配置模块
│   ├── build_vector_database.py        # 主流程脚本
│   ├── vector_search_example.py        # 搜索示例
│   └── README.md                       # 详细文档
│
├── docker-compose.yml              # ElasticSearch部署配置
├── requirements.txt                # Python依赖
├── test_openrouter.py             # OpenRouter API测试
└── README.md                       # 本文件
```

## 数据格式

### 名人数据格式
```
英文名--中文名
例如: Jack Ma--马云
```

### 标签数据格式
```
英文标签--中文标签
例如: Entrepreneurial Challenges--创业困难
```

### 经历数据格式（JSON）
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
  "embedding": [0.123, 0.456, ...],  // 1024维向量
  "chunk_id": "Jack Ma_0",
  "full_text": "完整文本内容"
}
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
export OPENROUTER_API_KEY=your_openrouter_api_key_here
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export ELASTICSEARCH_INDEX=celebrity_experiences

# Embedding模型配置
如果使用自定义embedding API端点，设置以下变量：
export EMBEDDING_API_BASE_URL=https://your-api-endpoint.com/v1
export EMBEDDING_API_KEY=your_api_key
export EMBEDDING_MODEL=your_model_name  # 例如: Qwen/Qwen3-Embedding-0.6B
默认使用OpenRouter的openai/text-embedding-3-small模型，只需设置OPENROUTER_API_KEY即可
```

### 3. 启动 ElasticSearch

```bash
docker-compose up -d
```

等待 ElasticSearch 启动完成（约30秒），验证：

```bash
curl http://localhost:9200
```

**注意**: ElasticSearch 数据将存储在 `/home/linweiquan/elasticresearch/data` 目录中。

**常用命令**：
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker logs inspirematch_elasticsearch

# 停止服务
docker-compose stop    # 停止但保留容器和数据
docker-compose down    # 停止并删除容器（数据保留在卷中）

# 重启服务
docker-compose restart
```

### 4. 构建向量数据库

```bash
cd vector_db_builder
python build_vector_database.py
```

这个过程包括：
1. 搜索所有名人的经历（使用 sonar-pro-search）
2. 提取结构化数据（使用 LLM）
3. 匹配标签
4. 文本切块和向量嵌入
5. 存储到 ElasticSearch

**注意**: 整个过程可能需要较长时间，建议在后台运行或使用断点续传。

### 5. 搜索示例

```bash
# 向量搜索
python vector_search_example.py "如何应对创业困难" --size 5

# 带标签过滤
python vector_search_example.py "如何应对创业困难" --tags "Entrepreneurial Challenges" --size 5

# 关键词搜索
python vector_search_example.py "创业" --keyword --size 5
```

## 详细文档

更详细的使用说明请参考：
- [向量数据库构建工具文档](./vector_db_builder/README.md)
- [快速启动指南](./vector_db_builder/QUICKSTART.md)
- [实现总结](./vector_db_builder/IMPLEMENTATION_SUMMARY.md)

## 技术栈

- **搜索**: sonar-pro-search (via OpenRouter)
- **数据提取**: GPT-4o-mini (via OpenRouter)
- **向量嵌入**: 支持多种模型（可通过环境变量配置）
  - 默认（OpenRouter）: openai/text-embedding-3-small (1024维)
  - 自定义端点: Qwen/Qwen3-Embedding-0.6B (1024维)
  - 可通过 `EMBEDDING_MODEL` 环境变量自定义模型
- **向量数据库**: ElasticSearch 8.x
- **文本处理**: tiktoken

## 数据来源

- **9个职业领域**: 政治家、科学家、企业家、艺术家、运动员、演员与娱乐圈人物、作家与哲学家、社会活动家、教育工作者
- **10种经历标签类型**: 
  - 职业发展与事业挑战
  - 心理健康与情感困境
  - 个人成长与自我提升
  - 关系与人际交往
  - 财务与生活困境
  - 身体健康与运动
  - 创业与创新
  - 教育与学习
  - 社会责任与影响力
  - 失败与恢复

## 使用场景

- 📖 **个人成长**: 从名人经历中学习应对挑战的策略
- 💼 **职业发展**: 了解不同职业领域的成功经验
- 🎯 **问题解决**: 通过相似经历找到解决问题的方法
- 📚 **知识检索**: 快速检索和匹配相关经历案例

## 断点续传

如果构建过程中断，可以使用以下参数跳过已完成的步骤：

```bash
# 跳过搜索步骤（使用缓存）
python build_vector_database.py --skip-search

# 跳过搜索和提取步骤
python build_vector_database.py --skip-search --skip-extract

# 跳过搜索、提取和标签匹配
python build_vector_database.py --skip-search --skip-extract --skip-tags
```

缓存文件保存在 `vector_db_builder/cache/` 目录中。

## 在代码中使用

```python
from vector_db_builder.vector_search_example import search_experiences

# 向量搜索
results = search_experiences("如何应对职业挑战", size=10)

# 带标签过滤
results = search_experiences(
    "如何应对创业困难",
    size=10,
    filter_tags=["Entrepreneurial Challenges", "Lack of Startup Funds"]
)
```

## 更新数据

### 更新人名和标签

**数据位置**：
- 人名：`data_construct/celebrity_deeds/` 目录下，按职业分类（9个文件）
- 标签：`data_construct/flags/` 目录下，按标签类型分类（10个文件）

**格式要求**：
- 每行一个条目，格式：`英文--中文`
- 例如：`Jack Ma--马云` 或 `Entrepreneurial Challenges--创业困难`
- **重要**：必须使用 `--`（两个短横线）分隔，格式错误会导致解析失败

**更新步骤**：
1. 编辑对应的 `.txt` 文件，添加、修改或删除条目
2. 保存文件
3. 重新构建数据库（见下文）

### 重新构建数据库

不同更新场景的推荐方法：

**场景 1：添加/修改/删除人名**
- 需要完全重建（不能使用缓存）
- 原因：新数据不在缓存中，且需要删除旧数据

**场景 2：添加/修改标签**
- 可以使用缓存跳过搜索和提取
- 只需重新匹配标签、向量化和索引

**场景 3：删除标签**
- 建议完全重建（确保数据一致性）

**完全重建命令**：
```bash
cd vector_db_builder

# 删除旧索引和缓存
python -c "
from elasticsearch_setup import ElasticsearchSetup
es = ElasticsearchSetup()
es.es.indices.delete(index='celebrity_experiences', ignore=[404])
print('索引已删除')
"
rm -rf cache/*.json

# 完全重新构建
python build_vector_database.py
```

**使用缓存重建（仅限场景2）**：
```bash
cd vector_db_builder

# 删除旧索引
python -c "
from elasticsearch_setup import ElasticsearchSetup
es = ElasticsearchSetup()
es.es.indices.delete(index='celebrity_experiences', ignore=[404])
print('索引已删除')
"

# 跳过搜索和提取，使用缓存数据
python build_vector_database.py --skip-search --skip-extract
```

**构建流程说明**：
1. 搜索名人经历 (`--skip-search`)
2. 提取结构化数据 (`--skip-extract`)
3. 标签匹配 (`--skip-tags`)
4. 文本切块和向量嵌入 (`--skip-processing`)
5. 存储到ElasticSearch

**提示**：跳过步骤会从缓存加载数据，如果缓存不存在会失败。新增人名时不能跳过任何步骤。

### 验证更新

更新完成后，可以通过以下方式验证：

```bash
# 1. 检查索引中的文档数量
curl "http://localhost:9200/celebrity_experiences/_count?pretty"

# 2. 搜索测试
cd vector_db_builder
python vector_search_example.py "测试查询" --size 5

# 3. 检查特定名人的数据
curl "http://localhost:9200/celebrity_experiences/_search?q=celebrity_name_cn:马云&pretty"
```

## 注意事项

1. **API 限流**: 搜索和提取过程会调用 OpenRouter API，代码中已添加延迟以避免过快请求。
2. **ElasticSearch 内存**: 默认 512MB，数据量大时可能需要调整 `docker-compose.yml`。
3. **数据持久化**: ElasticSearch 数据存储在 `/home/linweiquan/elasticresearch/data`，删除容器前请备份。
4. **向量嵌入**: 默认使用 OpenRouter 的 `openai/text-embedding-3-small`（1024维），可通过环境变量配置（见环境变量配置部分）。
5. **数据格式**: 人名和标签文件必须使用 `--`（两个短横线）分隔，格式错误会导致解析失败。
6. **缓存管理**: 更新数据后建议清理缓存，确保使用最新数据。
7. **索引重建**: 更新人名或大量标签后，建议删除旧索引并完全重建，确保数据一致性。

## 许可证

[添加许可证信息]

## 贡献
https://github.com/Eric-Lin-HKUSTGZ


## 联系方式

s-lwq25@bjzgca.edu.cn
