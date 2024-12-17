from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import ChatbotService
from django.views.decorators.http import require_http_methods
import json

@login_required
def chatbot_view(request):
    chatbot = ChatbotService(user=request.user)
    recent_messages = chatbot.get_recent_messages(request.user)
    current_document = chatbot.get_current_document()
    return render(request, 'chatbot/chat.html', {
        'recent_messages': recent_messages,
        'current_document': current_document
    })

@login_required
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'error': 'El mensaje no puede estar vacío'
            }, status=400)
        
        chatbot = ChatbotService(user=request.user)
        response = chatbot.send_message(request.user, message)
        
        return JsonResponse({
            'response': response
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
