import polars as pl
import os
import logging

logging.basicConfig(level=logging.INFO)

# read data from csv
RECIPE_TYPES = ["ayam", "ikan", "kambing", "sapi", "tahu", "telur", "tempe", "udang"]
LIKE_THRESHOLD = 5
SEED = 42

logging.info("loading datasets")
dfs = [pl.read_csv(f"datasets/dataset-{recipe}.csv") for recipe in RECIPE_TYPES]
df = pl.concat(dfs)
df = df.rename(
    {
        "Title": "title",
        "Ingredients": "ingredients",
        "Steps": "steps",
        "Loves": "likes",
        "URL": "url",
    }
)

logging.info(f"filtering dataset based on like count >{LIKE_THRESHOLD}")
df = df.filter(pl.col("likes").gt(LIKE_THRESHOLD))
logging.info(f"count: {df.height}")

logging.info("saving dataset to parquet")
os.makedirs("tmp", exist_ok=True)
df.write_parquet("tmp/recipes.parquet")
