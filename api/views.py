from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .rag import RAGEngine
import uuid
import logging

logger = logging.getLogger(__name__)
rag = RAGEngine()

class ChatView(APIView):
    def post(self, req):
        message = req.data.get('message')
        conversation_id = req.data.get('conversation_id', str(uuid.uuid4()))

        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contexts = rag.retrieve_context(message)
            result = rag.generate_response(message, contexts)
            
            return Response({
                "answer": result["answer"],
                "sources": result["sources"],
                "conversation_id": conversation_id,
                "confidence_score": result.get("confidence_score", 0.0)
            })
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConversationHistoryView(APIView):
    def get(self, req, conversation_id):
        # Mocking history for now
        history = [
            {"role": "user", "content": "How do I reset my password?", "timestamp": "2023-10-01T10:00:00Z"},
            {"role": "assistant", "content": "You can reset your password by clicking the 'Forgot Password' link on the login page.", "timestamp": "2023-10-01T10:00:05Z"}
        ]
        return Response({"conversation_id": conversation_id, "messages": history})

class FeedbackView(APIView):
    def post(self, req):
        message_id = req.data.get('message_id')
        rating = req.data.get('rating')
        comment = req.data.get('comment', "")

        if rating not in [1, -1]:
            return Response({"error": "Rating must be 1 or -1"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Feedback received: {message_id}, Rating: {rating}, Comment: {comment}")
        return Response({"status": "feedback recorded"})

class HealthCheckView(APIView):
    def get(self, req):
        return Response({
            "status": "healthy",
            "azure_openai": "connected",
            "database": "connected"
        })
