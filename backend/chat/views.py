from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import ChatMessage, ChatSession
from django.conf import settings
import requests

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)
    user = User.objects.create_user(username=username, password=password, email=email)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'username': user.username
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username
        })
    return Response({'error': 'Invalid credentials'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_session(request):
    session = ChatSession.objects.create(user=request.user, title="New Chat")
    return Response({'session_id': session.id, 'title': session.title})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user)
    data = [{'id': s.id, 'title': s.title, 'created_at': s.created_at} for s in sessions]
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    user_message = request.data.get('message', '')
    session_id = request.data.get('session_id')
    if not user_message:
        return Response({'error': 'No message'}, status=400)

    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            if session.title == "New Chat":
                session.title = user_message[:40]
                session.save()
        except ChatSession.DoesNotExist:
            pass

    ChatMessage.objects.create(user=request.user, session=session, role='user', message=user_message)

    headers = {
        'Authorization': f'Bearer {settings.GROQ_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'llama-3.3-70b-versatile',
        'messages': [
            {'role': 'system', 'content': 'You are MindBot, a helpful AI assistant built by StackMind.'},
            {'role': 'user', 'content': user_message}
        ]
    }
    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers=headers,
        json=payload
    )
    reply = response.json()['choices'][0]['message']['content']
    ChatMessage.objects.create(user=request.user, session=session, role='bot', message=reply)
    return Response({'reply': reply})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    session_id = request.GET.get('session_id')
    if session_id:
        messages = ChatMessage.objects.filter(user=request.user, session_id=session_id)
    else:
        messages = ChatMessage.objects.filter(user=request.user)
    data = [{'role': m.role, 'message': m.message} for m in messages]
    return Response(data)