"""
WhiteFlag Explorer URL Configuration
Public, read-only endpoints for exploring WhiteFlag messages
"""
from django.urls import path
from . import views

app_name = 'explorer'

urlpatterns = [
    # Message endpoints
    path('messages/', views.messages_list, name='messages-list'),
    path('messages/<int:message_id>/', views.message_detail, name='message-detail'),
    
    # Account endpoints
    path('accounts/<str:username>/', views.account_profile, name='account-profile'),
    
    # Network statistics
    path('stats/', views.network_stats, name='network-stats'),
    
    # Search
    path('search/', views.search_messages, name='search'),
    
    # Reference graph
    path('reference-graph/<int:message_id>/', views.reference_graph, name='reference-graph'),
]
