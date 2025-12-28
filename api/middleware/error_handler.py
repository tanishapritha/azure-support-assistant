from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class AzureAPIError(Exception):
    pass

class RateLimitError(Exception):
    pass

class ValidationError(Exception):
    pass

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, AzureAPIError):
            return Response({'error': 'Azure service integration failed'}, status=status.HTTP_502_BAD_GATEWAY)
        if isinstance(exc, RateLimitError):
            return Response({'error': 'Rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
