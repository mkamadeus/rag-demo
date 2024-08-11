import polars as pl
from tqdm import tqdm
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import logging

COLLECTION_NAME = "recipes"

logging.basicConfig(level=logging.INFO)

logging.info("loading dataset")
df = pl.read_parquet("tmp/recipes.parquet")

logging.info("setup clients")
encoder = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient("http://localhost:6333")

if qdrant.collection_exists(COLLECTION_NAME):
    logging.info("deleting existing collection")
    qdrant.delete_collection(COLLECTION_NAME)

logging.info("creating collection")
qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={
        "title": models.VectorParams(
            size=encoder.get_sentence_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
        "ingredients": models.VectorParams(
            size=encoder.get_sentence_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
    },
)

logging.info("creating embeddings")
count = df.height
batch_titles = df.get_column("title").to_list()
batch_ingredients = df.get_column("ingredients").to_list()

title_embeddings = encoder.encode(batch_titles, batch_size=32, convert_to_tensor=True)
ingredient_embeddings = encoder.encode(
    batch_ingredients, batch_size=32, convert_to_tensor=True
)

logging.info("uploading points")
qdrant.upload_points(
    collection_name=COLLECTION_NAME,
    points=[
        models.PointStruct(
            id=idx,
            vector={
                "title": title_embeddings[idx].tolist(),
                "ingredients": ingredient_embeddings[idx].tolist(),
            },
            payload=df.row(idx, named=True),
        )
        for idx in tqdm(range(count))
    ],
)
