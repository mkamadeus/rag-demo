import polars as pl
import os
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import textwrap
from dotenv import load_dotenv

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "true"

encoder = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient("http://localhost:6333")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PROMPT = input("Enter a query: ")
encoded = encoder.encode(PROMPT).tolist()
hits = qdrant.search(
    collection_name="recipes",
    query_vector=models.NamedVector(name="title", vector=encoded),
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="likes",
                range=models.Range(gte=10),
            )
        ]
    ),
    limit=5,
)

df = pl.DataFrame(
    [
        {
            "title": hit.payload["title"],
            "ingredients": hit.payload["ingredients"],
            "steps": hit.payload["steps"],
            "score": hit.score,
        }
        for hit in hits
    ]
)
print(df)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": textwrap.dedent("""
            You are a chef chatbot.
            Your top priority is to help users into picking one recipe that suits the user request the best.
            If no recipe suits the user request perfectly, pick the one that is the closest.
            Recipes are in Indonesian, automatically translate the recipe to English.
            Just give the name of the dish, the ingredients, and the steps to make the dish in English.
            """),
        },
        {
            "role": "user",
            "content": PROMPT,
        },
        {
            "role": "assistant",
            "content": str(df.to_dicts()),
        },
    ],
    stream=True,
)
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()
