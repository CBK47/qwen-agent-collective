import psycopg2
from psycopg2 import extras
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

class Brain:
    def __init__(self, pg_host, pg_port, pg_user, pg_password, pg_db, qdrant_host, qdrant_port, collection_name="memories"):
        self.pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            database=pg_db
        )
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name

    def ingest(self, content: str, embedding: list[float], metadata: dict):
        point_id = str(uuid.uuid4())
        points = [PointStruct(id=point_id, vector=embedding, payload=metadata)]
        self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
        
        cursor = self.pg_conn.cursor()
        cursor.execute(
            "INSERT INTO memories (id, content, metadata) VALUES (%s, %s, %s)",
            (point_id, content, extras.Json(metadata))
        )
        self.pg_conn.commit()
        cursor.close()

    def retrieve(self, query_embedding: list[float], top_k: int = 5):
        hits = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        results = []
        cursor = self.pg_conn.cursor()
        for hit in hits:
            cursor.execute(
                "SELECT content, metadata FROM memories WHERE id = %s",
                (hit.id,)
            )
            row = cursor.fetchone()
            if row:
                results.append({
                    'content': row[0],
                    'metadata': row[1],
                    'score': hit.score
                })
        cursor.close()
        return results
