from mcp.server.fastmcp import FastMCP
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import json

DB_PATH = "../../milvus.db"
# Carga del modelo liviano en GPU (o 'cpu' si no hay GPU)
model_st = SentenceTransformer("paraphrase-MiniLM-L6-v2", device="cuda")


DATA_PATH = "./data/season1.json"

EPISODES_NAMES = [
    "Game Of Thrones S01E01 Winter Is Coming.srt",
    "Game Of Thrones S01E02 The Kingsroad.srt",
    "Game Of Thrones S01E03 Lord Snow.srt",
    "Game Of Thrones S01E04 Cripples, Bastards, And Broken Things.srt",
    "Game Of Thrones S01E05 The Wolf And The Lion.srt",
    "Game Of Thrones S01E06 A Golden Crown.srt",
    "Game Of Thrones S01E07 You Win Or You Die.srt",
    "Game Of Thrones S01E08 The Pointy End.srt",
    "Game Of Thrones S01E09 Baelor.srt",
    "Game Of Thrones S01E10 Fire And Blood.srt",
]

DIMENSION = 384


def encode_documents(documents):
    return model_st.encode(documents)


def init_collections():
    client = get_client()
    if "game_of_thrones" in client.list_collections():
        print("La colección ya existe.")
        return

    client.create_collection(
        collection_name="game_of_thrones", auto_id=True, dimension=DIMENSION
    )

    with open(DATA_PATH, "r") as file:
        file_data = json.load(file)
        data = []

        for ep_index, episode in enumerate(EPISODES_NAMES):
            episode_content = file_data.get(episode)
            if not episode_content:
                continue

            documents = []

            for _, text in episode_content.items():
                documents.append(text)

            vectors = encode_documents(documents)

            for doc_index, document in enumerate(documents):
                data.append(
                    {
                        "season": 1,
                        "episode": ep_index,
                        "quote": document,
                        "vector": vectors[doc_index],
                    }
                )

        client.insert(collection_name="game_of_thrones", data=data)


def get_client() -> MilvusClient:
    return MilvusClient(DB_PATH)


def get_subtitle_by_query(query: str):
    client = get_client()

    query_vectors = encode_documents([query])

    result = client.search(
        collection_name="game_of_thrones",
        data=query_vectors,
        limit=5,
        output_fields=["season", "episode", "quote"],
    )

    return result


# Initialize FastMCP server
mcp = FastMCP("gotquery")


@mcp.tool()
def get_subtitles(query: str):
    """Get Game of Thrones season 1 subtitles related to a query.

    Args:
        query: User text.
    """
    return get_subtitle_by_query(query)


if __name__ == "__main__":
    # Initialize and run the server
    print("Ejecutando...")
    mcp.run(transport="stdio")
