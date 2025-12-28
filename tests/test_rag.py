import pytest
from unittest.mock import MagicMock
from api.rag import RAGEngine

@pytest.fixture
def mock_rag():
    engine = RAGEngine()
    engine.openai_client = MagicMock()
    engine.search_client = MagicMock()
    return engine

def test_retrieve_context(mock_rag):
    mock_rag.openai_client.embeddings.create.return_value.data = [MagicMock(embedding=[0.1]*1536)]
    mock_rag.search_client.search.return_value = [{"ticket_id": "T-1", "category": "Bill", "question": "Q", "resolution": "R"}]
    
    results = mock_rag.retrieve_context("billing issue")
    assert len(results) == 1
    assert results[0]['ticket_id'] == "T-1"

def test_generate_response(mock_rag):
    mock_rag.openai_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Here is the answer based on T-1"))
    ]
    
    context = [{"ticket_id": "T-1", "category": "Bill", "question": "Q", "resolution": "R"}]
    result = mock_rag.generate_response("query", context)
    
    assert "T-1" in result["sources"]
    assert "answer" in result
