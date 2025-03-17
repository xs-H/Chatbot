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
    JSON_PATH = "./resource/NeZha.json"
    SAVE_PATH = "./resource"
    LOG_PATH = os.path.join('./log')
    # embedding_model = 'nomic-ai/nomic-embed-text-v1'
    MODEL_NAME = "GanymedeNil/text2vec-large-chinese"

    # 检索参数
    min_similarity = 0.3  # 相似度阈值
    default_k = 10  # 默认返回结果数
    search_multiplier = 3  # 搜索扩展倍数

    # 对话参数
    max_history = 20  # 保留的历史消息数
    max_context_len = 1000  # 上下文最大长度（字符）


# Logging Configuration
logging.basicConfig(
    filename=os.path.join(Config.LOG_PATH, 'chat.log'),
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s")


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

def extract_text(d):
    if isinstance(d, str):
        return [d]
    elif isinstance(d, list):
        # 如果列表所有元素都不是容器，则视为最底层，直接拼接
        if all(not isinstance(item, (list, dict)) for item in d):
            return [" ".join(str(item) for item in d)]
        else:
            texts = []
            for item in d:
                texts.extend(extract_text(item))
            return texts
    elif isinstance(d, dict):
        # 如果字典所有值都不是容器，则视为最底层，直接拼接键值对
        if all(not isinstance(value, (list, dict)) for value in d.values()):
            return [" ".join(f"{k}: {v}" for k, v in d.items())]
        else:
            texts = []
            for key, value in d.items():
                texts.extend(extract_text(value))
            return texts
    return []

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

        logging.info("知识库初始化完成并已保存。")
        return db

    def _retrieve_context(self, query):
        logging.info(f"查询: {query}")
        results = self.db.similarity_search(query, Config.default_k)
        for i, result in enumerate(results):
            logging.info(f"结果 {i+1}: {result.page_content}")
        return results

