from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('chat/', views.chat_view, name='chat'), 
    path('index/', views.chat_view, name='index'), 


    #path('agents/', views.agent_manager, name='agent_manager'),
    path('add/', views.save_agent, name='add_agent'),
    #path('edit/<int:pk>/', views.edit_agent, name='edit_agent'),
    path('edit/<int:agent_id>/', views.edit_agent, name='edit_agent'), # Pour la modification
    path('agent/create/', views.edit_agent, name='create_agent'),
    path('activer/<int:agent_id>/', views.active_agent_ai, name='active_agent_ai'),
    path('delete/<int:pk>/', views.delete_agent, name='delete_agent'),
    path('activate/<int:pk>/', views.toggle_agent, name='toggle_agent'),
    path('activate/<int:pk>/', views.toggle_db_source, name='toggle_db_source'),


    path('agent_ia/', views.agent_ia_view, name='agent_ia'),
    #path('get_agent_api_response/', views.get_agent_api_response, name='get_agent_api_response'),
    #path('get_response/', views.get_response, name='get_response'),

    path('parametre/', views.parametre, name='parametre'),

    #path('get_response/', views.get_response, name='get_response'),
    path('get_response/', views.recherche_naturelle, name='get_response'),
    path("messages/clear/", views.clear_messages, name="clear_messages"),


    #path('select/', views.select_source, name='select_source'),  # Route manquante
    #path('activ_source/', views.activ_source, name='activ_source'),  # Route manquante
    path('activerDb/<int:db_source_id>/', views.activ_source, name='activ_source'),
    path('add_source/', views.add_source, name='add_source'),
    #path('edit/<int:agent_id>/', views.edit_agent, name='edit_agent'), # Pour la modification
    path('edit_source/<int:pk>/', views.edit_source, name='edit_source'),
    path('delete_source/<int:pk>/', views.delete_source, name='delete_source'),
    #path('test_connect_bdd/<int:pk>/', views.test_connect_bdd, name='test_connect_bdd'),
    path('chat/test_connect_bdd/', views.test_connect_bdd, name='test_connect_bdd'),
    path('de_connect_bdd/<int:pk>/', views.de_connect_bdd, name='de_connect_bdd'),
    #path('execute_query/', views.execute_query, name='execute_query'),
    #path('sources/', views.sources_list, name='sources'), """
]
