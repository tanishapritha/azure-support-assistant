import os
import re
import logging
import pandas as pd
import psycopg2
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
        self.db_conn = psycopg2.connect(os.getenv("DATABASE_URL"))

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text.strip()

    def generate_embeddings(self, text: str):
        try:
            response = self.openai_client.embeddings.create(
                input=[text],
                model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

    def store_in_postgres(self, df: pd.DataFrame):
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    timestamp TIMESTAMP,
                    category TEXT,
                    question TEXT,
                    resolution TEXT
                )
            """)
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO tickets (ticket_id, customer_name, timestamp, category, question, resolution)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticket_id) DO NOTHING
                """, (row['ticket_id'], row['customer_name'], row['timestamp'], row['category'], row['question'], row['resolution']))
            self.db_conn.commit()
            logger.info("Successfully stored tickets in PostgreSQL")
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"PostgreSQL Error: {e}")
        finally:
            cursor.close()

    def store_in_search(self, df: pd.DataFrame):
        documents = []
        for _, row in df.iterrows():
            combined_text = f"{row['category']} {row['question']} {row['resolution']}"
            embedding = self.generate_embeddings(combined_text)
            if embedding:
                documents.append({
                    "id": row['ticket_id'].replace("-", "_"),
                    "ticket_id": row['ticket_id'],
                    "category": row['category'],
                    "question": row['question'],
                    "resolution": row['resolution'],
                    "content_vector": embedding
                })
        
        if documents:
            try:
                self.search_client.upload_documents(documents)
                logger.info(f"Successfully uploaded {len(documents)} documents to Azure AI Search")
            except Exception as e:
                logger.error(f"Azure Search Error: {e}")

    def run(self, csv_path: str):
        try:
            logger.info(f"Starting ETL from {csv_path}")
            df = pd.read_csv(csv_path)
            
            df['question'] = df['question'].apply(self.clean_text)
            df['resolution'] = df['resolution'].apply(self.clean_text)
            
            self.store_in_postgres(df)
            self.store_in_search(df)
            
            logger.info("ETL Pipeline completed successfully")
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")

if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run('data/support_tickets.csv')
