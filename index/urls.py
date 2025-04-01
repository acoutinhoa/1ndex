from django.urls import path, include
from . import views

app_name = 'index'

# responsabilidade
responsa_patterns = [
    path('transferir/', views.responsa_transferir, name='edit-filhos-transferir'),
    path('aceitar/', views.responsa_aceitar, name='edit-filhos-aceitar'),
    path('recusar/', views.responsa_recusar, name='edit-filhos-recusar'),
    path('inativar/', views.responsa_inativar, name='edit-filhos-inativar'),
    # search
    path('search/', views.search_mae, name='search-mae'),
]

# edit htmx
edit_htmx_patterns = [
    path('info/', views.edit_info, name='edit-info'),
    path('url/', views.edit_url, name='edit-url'),
    path('filhos/', views.edit_filhos, name='edit-filhos'),
    path('filhos/<str:pk>/', include(responsa_patterns)),
    path('adms/', views.edit_adms, name='edit-adms'),
    path('grupos/', views.edit_grupos, name='edit-grupos'),
    path('projetos/', views.edit_projetos, name='edit-projetos'),
    path('trabalhos/', views.edit_trabalhos, name='edit-trabalhos'),
]

# edit
edit_patterns = [
    path('', views.edit, name='edit'),
    path('<str:ativo>/', views.edit, name='edit-ativo'),
    #htmx
    path('htmx/', include(edit_htmx_patterns)),
]

# add
add_patterns = [
    # path('', views.add, name='add-index'),
    #htmx
    path('grupo/', views.add_grupo, name='add-grupo'),
    path('adm/', views.add_adm, name='add-adm'),
    path('convite/', views.add_convite, name='add-convite'),
]

# delete
delete_patterns = [
    path('grupo/', views.delete_grupo, name='delete-grupo'),
    path('adm/<str:pk>/', views.delete_adm,  name='delete-adm'),
]

# perfil
perfil_patterns = [
    path('', views.index, name='perfil'),
    path('edit/', include(edit_patterns)),
    path('add/', include(add_patterns)),
    path('delete/', include(delete_patterns)),
    # search
    path('search/adm/', views.search_adm, name='search-adm'),
    # visibilidade
    path('visibilidade/grupo/', views.grupo_visibilidade, name='grupo-visibilidade'),
]

# invite
invite_patterns = [
    path('', views.convite,  name='convite'),
    path('register/', views.cadastro,  name='cadastro'),
    path('reativar/', views.reativar,  name='reativar'),
    path('transferir/', views.trans_convite,  name='trans-convite'),
    path('delete/', views.delete_convite,  name='delete-convite'),
]

# htmx
htmx_patterns = [
    path('clear/', views.clear, name='clear'),
    # check
    path('check/codinome/', views.check_codinome, name='check-codinome'),
    path('check/codinome/<str:url>/', views.check_codinome, name='check-url'),
    path('check/nome/<str:url>/', views.check_nome, name='check-nome'),
    path('check/email/<str:pk>/', views.check_email, name='check-email'),
]

# geral
urlpatterns = [
    path('', views.index, name='index'),
    path('invite/<str:pk>/', include(invite_patterns)),
    path('htmx/', include(htmx_patterns)),
    path('<str:url>/', include(perfil_patterns)),
]
