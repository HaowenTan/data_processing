# 中文维基数据提取，清洗，质量评估流程






##  项目说明：中文文本质量评估工具

本项目旨在从维基百科中文网站原始语料中提取文本片段，进行清洗过滤，并基于 Qwen3 模型对其质量进行五个维度的打分。

---

## 依赖安装

首先请确保你使用的是 Python 3.8+。安装依赖项如下：

```bash
pip install -r requirements.txt
```




##  文件说明

### 1. `extract_data.ipynb`

用于从 Wikipedia 或其他数据源中提取文本。主要功能包括：

* 加载 Wiki dump 数据或原始文本集合；
* 使用 `wikiextractor` 进行文本结构清洗；
* 手动加入额外的清洗规则
* 输出为 `.jsonl` 文件格式，每行一个包含 `text` 字段的 JSON。

根据你提供的 `clean_and_convert.py` 中的逻辑和注释，我为你整理并扩展了**清洗策略说明部分**，用于补充到 `README.md` 中的 “数据预处理与清洗策略”章节，结构清晰、内容全面，适合放入项目文档中。

清洗策略见


---


### 2. `score.py`

用于调用阿里云 DashScope 的 Qwen3 模型，对文本质量进行评估。

####  评估维度：

每条文本将被评估以下五个维度（得分范围为 0～10）：

1. 格式规范
2. 句法完整性
3. 语言通顺度
4. 上下文逻辑性
5. 信息量

####  模型调用流程：

* 构造 API 请求（支持批量并发调用）；
* 提取模型返回中的五项打分；
* 输出格式为带有 `text + meta + scores` 的 JSON.
  
#### 结果说明

在3213条数据中，有14条数据，触发模型内容安全机制，传入的 text 被模型后台判定为包含不合规内容（如敏感词、色情、暴力、政治等），导致拒绝响应

在给出评分的3199条数据中，可以根据模型评分进一步过滤高质量数据，用于训练

#### 使用说明：

```bash
python score.py \
    --input data/input.jsonl \
    --output results/scored.jsonl \
    --batch_size 10 \
    --max_workers 5
```

---

##  快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行评估脚本
python score.py --input your_data.jsonl --output scored_data.jsonl
```


