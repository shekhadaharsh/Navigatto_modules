from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(":memory:")

collection_name = "test_col"
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=3, distance=Distance.COSINE)
)

client.upsert(
    collection_name="test_col",
    points=[
        PointStruct(id=1, vector=[0.1, 0.2, 0.3], payload={"name": "Alice"}),
        PointStruct(id=2, vector=[0.9, 0.1, 0.1], payload={"name": "Bob"})
    ]
)

res = client.query_points(
    collection_name="test_col",
    query=[0.1, 0.2, 0.3],
    limit=1
)
print("Query points returned:", res.points)

