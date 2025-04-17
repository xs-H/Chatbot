import os
import json
import hashlib
import logging
import chardet
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# from langchain.document_loaders import TextLoader

# Configuration
class Config:
    # TEXT_PATH = r'D:\HJG\500.Projects\chat-deepseek-8B\role-resource'
    JSON_PATH = "../../resource/database/NeZha.json"
    SAVE_PATH = "../../resource/database"
    LOG_PATH = os.path.join('../../logs')
    # embedding_model = 'nomic-ai/nomic-embed-text-v1'
    MODEL_NAME = "./text2vec-large-chinese"

    # 检索参数
    min_similarity = 0.8  # 相似度阈值
    default_k = 5  # 默认返回结果数
    search_multiplier = 10  # 搜索扩展倍数

    # 对话参数
    max_history = 20  # 保留的历史消息数
    max_context_len = 1000  # 上下文最大长度（字符）


# Logging Configuration
logging.basicConfig(
    filename=os.path.join(Config.LOG_PATH, 'chat_api.log'),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding='utf-8'  # 显式指定编码
)


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)  # 读取前 10000 字节提高检测效率
        result = chardet.detect(raw_data)

        # 置信度阈值判断
        if result['confidence'] < 0.85:
            return _try_common_encodings(raw_data)

        encoding = result['encoding'].lower()

        # 编码映射修正
        encoding_map = {
            'gb2312': 'gb18030',  # 扩展中文编码支持
            'ascii': 'utf-8',  # 兼容ASCII子集
            'windows-1252': 'utf-8'
        }
        return encoding_map.get(encoding, encoding)


def _try_common_encodings(data):
    """备选编码验证"""
    for encoding in ['utf-8-sig', 'gb18030', 'utf-16', 'big5']:
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return 'utf-8'  # 默认回退


def process_value(value):
    # 处理值，将字典、列表转换为拼接字符串
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            processed_v = process_value(v)
            parts.append(f"{k}：{processed_v}")
        return "；".join(parts)
    elif isinstance(value, list):
        return "、".join(map(str, value))
    else:
        return str(value)


def extract_text(data):
    result = []
    data=data.get("数据库")
    # 遍历顶层结构：角色经历、角色关系、角色台词
    for top_key in data:
        top_data = data[top_key]
        if not isinstance(top_data, dict):
            continue

        # 遍历角色名
        for role_name in top_data:
            role_data = top_data[role_name]
            if not isinstance(role_data, dict):
                continue

            # 遍历第三层键（如魔童降世、和敖丙等）
            for third_key in role_data:
                third_value = role_data[third_key]
                content = process_value(third_value)
                # 构建条目字符串
                entry = f"{top_key}-{role_name}-{third_key}：{content}"
                result.append(entry)

    return result


class TextEmbedding:
    def __init__(self):
        self.model = HuggingFaceEmbeddings(model_name=Config.MODEL_NAME)
        self.db = self._load_or_create_embeddings()

    def _calculate_hash(self, file_path):
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _load_or_create_embeddings(self):
        hash_file = f"{Config.SAVE_PATH}/db_hash.txt"
        current_hash = self._calculate_hash(Config.JSON_PATH)

        if os.path.exists(Config.SAVE_PATH) and os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                saved_hash = f.read().strip()
            if saved_hash == current_hash:
                logging.info("知识库已存在且未改变，直接加载...")
                return FAISS.load_local(Config.SAVE_PATH, self.model,  allow_dangerous_deserialization=True)
            else:
                logging.warning("知识库已改变，重新初始化...")

        logging.info("初始化知识库...")
        encoding = detect_encoding(Config.JSON_PATH)
        try:
            with open(Config.JSON_PATH, "r", encoding=encoding) as f:
                data = json.load(f)
        except UnicodeDecodeError as e:
            logging.error(f"编码检测失败 ({encoding})，尝试强制解码")
            with open(Config.JSON_PATH, "r", encoding=encoding, errors='replace') as f:
                data = json.load(f)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        documents = []

        all_texts = extract_text(data)
        for text in all_texts:
            documents.extend(text_splitter.create_documents([text]))

        db = FAISS.from_documents(documents, self.model)
        db.save_local(Config.SAVE_PATH)
        with open(hash_file, "w") as f:
            f.write(current_hash)
        print("---知识库初始化完成并已保存---")
        logging.info("知识库初始化完成并已保存。")
        return db

    def _retrieve_context(self, query):
        logging.info(f"Query: {query}")
        results = self.db.similarity_search(query, Config.default_k)
        for i, result in enumerate(results):
            logging.info(f"结果 {i+1}: {result.page_content}")
        return results

