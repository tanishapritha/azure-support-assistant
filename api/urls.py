from django.urls import path
from .views import ChatView, ConversationHistoryView, FeedbackView, HealthCheckView

urlpatterns = [
    path('chat', ChatView.as_view(), name='chat'),
    path('conversations/<str:conversation_id>', ConversationHistoryView.as_view(), name='conversation-history'),
    path('feedback', FeedbackView.as_view(), name='feedback'),
    path('health', HealthCheckView.as_view(), name='health'),
]
