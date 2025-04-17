from django.urls import path, include
from . import views

app_name = 'index'

#########################################################################################################################
# projeto
#########################################################################################################################

# projeto edit htmx
projeto_edit_htmx_patterns = [
    path('perfil/', views.projeto_edit_info, name='projeto-edit-perfil'),
    path('links/', views.projeto_edit_links, name='projeto-edit-links'),
    path('tags/privada/', views.projeto_edit_tags, {"publico": False}, name='projeto-edit-tags-privada'),
    path('tags/', views.projeto_edit_tags, name='projeto-edit-tags'),
    path('texto/', views.projeto_edit_texto, name='projeto-edit-texto'),
    path('imagens/', views.projeto_edit_imagens, name='projeto-edit-imagens'),
    path('equipe/', views.projeto_edit_equipe, name='projeto-edit-equipe'),
]

# projetos
projeto_patterns = [
    path('', views.projeto, name='projeto'),
    # edit
    path('edit/', views.projeto_edit, name='projeto-edit'),
    path('edit/<str:ativo>/', views.projeto_edit, name='projeto-edit-ativo'),
    path('edit/htmx/', include(projeto_edit_htmx_patterns)),
    # delete
    path('delete/', views.delete_projeto,  name='delete-projeto'),
    # htmx
    path('search/tags/', views.projeto_search_tags, name='projeto-search-tags'),
    path('remove/tag/<int:tag>/', views.projeto_remove_tag, name='projeto-remove-tag'),
    path('add/tag/<int:tag>/', views.projeto_add_tag, name='projeto-add-tag'),
    path('add/tag/', views.projeto_add_tag, name='projeto-add-tag'),
    path('add/imagem/', views.projeto_add_imagem, name='projeto-add-imagem'),
    path('visibilidade/', views.projeto_visibilidade, name='projeto-visibilidade'),
]

#########################################################################################################################
# responsabilidade
#########################################################################################################################

responsa_patterns = [
    path('transferir/', views.responsa_transferir, name='edit-filhos-transferir'),
    path('aceitar/', views.responsa_aceitar, name='edit-filhos-aceitar'),
    path('recusar/', views.responsa_recusar, name='edit-filhos-recusar'),
    path('inativar/', views.responsa_inativar, name='edit-filhos-inativar'),
    # search
    path('search/', views.search_mae, name='search-mae'),
]

#########################################################################################################################
# add / delete
#########################################################################################################################

# add
add_patterns = [
    # path('', views.add, name='add-index'),
    path('grupo/', views.add_grupo, name='add-grupo'),
    path('adm/', views.add_adm, name='add-adm'),
    path('convite/', views.add_convite, name='add-convite'),
    path('projeto/', views.add_projeto, name='add-projeto'),
]

# delete
delete_patterns = [
    path('grupo/', views.delete_grupo, name='delete-grupo'),
    path('adm/<str:pk>/', views.delete_adm,  name='delete-adm'),
]

#########################################################################################################################
# perfil
#########################################################################################################################

# edit htmx
edit_htmx_patterns = [
    path('perfil/', views.edit_info, name='edit-perfil'),
    path('url/', views.edit_url, name='edit-url'),
    path('links/', views.edit_links, name='edit-links'),
    path('filhos/', views.edit_filhos, name='edit-filhos'),
    path('filhos/<str:pk>/', include(responsa_patterns)),
    path('adms/', views.edit_adms, name='edit-adms'),
    path('grupos/', views.edit_grupos, name='edit-grupos'),
    path('projetos/', views.edit_projetos, name='edit-projetos'),
    path('trabalhos/', views.edit_trabalhos, name='edit-trabalhos'),
]

# perfil
perfil_patterns = [
    path('', views.index, name='perfil'),
    path('tags/<str:filtros>/', views.index, name='perfil-tags'),
    # edit
    path('edit/', views.edit, name='edit'),
    path('edit/<str:ativo>/', views.edit, name='edit-ativo'),
    path('edit/htmx/', include(edit_htmx_patterns)),
    # add / delete
    path('add/', include(add_patterns)),
    path('delete/', include(delete_patterns)),
    # htmx
    path('htmx/search/adm/', views.search_adm, name='search-adm'),
    path('htmx/visibilidade/grupo/', views.grupo_visibilidade, name='grupo-visibilidade'),
    path('htmx/tags/<str:filtros>/', views.tags, name='tags-perfil'),
    # projetos
    path('<str:purl>/', include(projeto_patterns)),
]

#########################################################################################################################
# convite
#########################################################################################################################

invite_patterns = [
    path('', views.convite,  name='convite'),
    path('register/', views.cadastro,  name='cadastro'),
    path('reativar/', views.reativar,  name='reativar'),
    path('transferir/', views.trans_convite,  name='trans-convite'),
    path('delete/', views.delete_convite,  name='delete-convite'),
]

#########################################################################################################################
# htmx
#########################################################################################################################

htmx_patterns = [
    path('clear/', views.clear, name='clear'),
    path('tags/<str:filtros>/', views.tags, name='tags-index'),
    # delete
    path('delete/link/<str:pk>/', views.delete_link, name='delete-link'),
    path('delete/imagem/<str:pk>/', views.delete_imagem, name='delete-imagem'),
    # check
    path('check/codinome/', views.check_codinome, name='check-codinome'),
    path('check/codinome/<str:url>/', views.check_codinome, name='check-url'),
    path('check/nome/<str:url>/', views.check_nome, name='check-nome'),
    path('check/email/<str:pk>/', views.check_email, name='check-email'),
    path('check/projeto/<str:url>/', views.check_projeto, name='check-projeto'),
]

#########################################################################################################################
# urls
#########################################################################################################################

urlpatterns = [
    path('', views.index, name='index'),
    path('tags/<str:filtros>/', views.index, name='index-tags'),
    path('invite/<str:pk>/', include(invite_patterns)),
    path('htmx/', include(htmx_patterns)),
    path('<str:url>/', include(perfil_patterns)),
]
