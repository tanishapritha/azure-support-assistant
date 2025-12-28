import os
import logging
from typing import List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RAGEngine:
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

    def get_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=[text],
            model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        )
        return response.data[0].embedding

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            vector_query = self.get_embedding(query)
            results = self.search_client.search(
                search_text=query,
                vector_queries=[{"value": vector_query, "fields": "content_vector", "k": top_k}],
                select=["ticket_id", "category", "question", "resolution"]
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def generate_response(self, query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        context_text = "\n\n".join([
            f"Ticket: {c['ticket_id']}\nCategory: {c['category']}\n"
            f"Question: {c['question']}\nResolution: {c['resolution']}"
            for c in contexts
        ])

        system_prompt = (
            "You are a professional AI customer support assistant. "
            "Use the provided context from previous support tickets to answer the user's question. "
            "If the answer isn't in the context, state that you don't know and suggest human support. "
            "Always include the Ticket IDs used in your response as sources."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
                ],
                temperature=0.2
            )
            
            answer = response.choices[0].message.content
            
            # Simple hallucination check
            sources = [c['ticket_id'] for c in contexts]
            validated_sources = [s for s in sources if s in answer] if contexts else []

            return {
                "answer": answer,
                "sources": validated_sources,
                "confidence_score": 0.95 if validated_sources else 0.5
            }
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {"answer": "I'm having trouble connecting to my knowledge base.", "sources": []}
