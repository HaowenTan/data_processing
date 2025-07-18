import json
import re
import os
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# === 配置 ===
SYSTEM_PROMPT = (
    "你是一位中文文本数据审核专家。请你从以下五个维度对所给文本内容进行质量评估，每个维度打一个 0 到 10 的整数分数，越高表示质量越好：\n\n"
    "1. 格式规范：是否使用了正确的中文标点符号，排版是否清晰；\n"
    "2. 句法完整性：句子结构是否完整，例如是否具备主谓宾结构；\n"
    "3. 语言通顺度：句子是否通顺自然，有无语病或重复；\n"
    "4. 上下文逻辑性：句子之间是否衔接自然、有逻辑；\n"
    "5. 信息量：是否包含具体、有意义的信息，而不是空泛、无效内容。\n\n"
    "请按照以下格式输出五个评分（每行一个维度）：\n"
    "格式规范: X\n句法完整性: X\n语言通顺度: X\n上下文逻辑性: X\n信息量: X"
)

# 请确保你已设置好 client
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# === 核心函数 ===

def load_jsonl_with_meta(file_path: str) -> List[Dict]:
    """从 jsonl 文件加载数据，返回包含 text 和 meta 的字典列表"""
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                items.append({
                    "text": data.get("text", ""),
                    "meta": data.get("meta", {})
                })
    return items

def extract_five_scores(text: str) -> Dict[str, int]:
    """从返回文本中提取五个维度的打分"""
    pattern = r"(格式规范|句法完整性|语言通顺度|上下文逻辑性|信息量)\s*[:：]?\s*(\d+)"
    matches = re.findall(pattern, text)
    scores = {}
    for dim, score in matches:
        try:
            scores[dim] = int(score)
        except:
            scores[dim] = -1
    for key in ["格式规范", "句法完整性", "语言通顺度", "上下文逻辑性", "信息量"]:
        scores.setdefault(key, -1)
    return scores

def call_api(text: str) -> Dict:
    """构造 prompt 并调用 API，返回评分结果"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    try:
        response = client.chat.completions.create(
            model="qwen3-32b",
            messages=messages,
            extra_body={"enable_thinking": False},
        )
        scores = extract_five_scores(response.choices[0].message.content)
        return scores
    except Exception as e:
        print(f"出错: {e}, text: ")
        return {dim: -1 for dim in ["格式规范", "句法完整性", "语言通顺度", "上下文逻辑性", "信息量"]}

def get_batch_scores_with_meta(data: List[Dict], batch_size: int = 5, max_workers: int = 5) -> List[Dict]:
    """批量打分，保留原始 meta 信息"""
    results = []

    def worker(item):
        text, meta = item["text"], item["meta"]
        score = call_api(text)
        return {"text": text, "meta": meta, "score": score}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, item) for item in data]
        for future in as_completed(futures):
            results.append(future.result())

    # 保持顺序一致（可选）
    results.sort(key=lambda r: data.index(next(d for d in data if d["text"] == r["text"])))
    return results

# === 示例调用 ===

if __name__ == "__main__":
    input_path = "cleaned_samples_10000.jsonl"
    output_path = "scored_output.jsonl"

    data = load_jsonl_with_meta(input_path)
    results = get_batch_scores_with_meta(data, batch_size=5, max_workers=5)

    with open(output_path, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
