from pymilvus import MilvusClient

DB_PATH = "../../milvus.db"


def get_client() -> MilvusClient:
    return MilvusClient(DB_PATH)
