from app.db.client import get_client
from app.db.collections import encode_documents

def get_subtititle_by_query(query: str):
    client = get_client()

    query_vectors = encode_documents(query)

    result = client.search(collection_name="game_of_thrones", data=query_vectors, limit=5, output_fields=["season", "episode", "quote"])

    return result
