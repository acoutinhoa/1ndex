from django.urls import reverse_lazy


#########################################################################################################################
# menu
#########################################################################################################################

# menu user edit
def menu_edit_user(url):
    menu = [
        ['perfil',reverse_lazy('index:edit-perfil', kwargs={'url': url})],
        ['filhos',reverse_lazy('index:edit-filhos', kwargs={'url': url})],
        ['grupos',reverse_lazy('index:edit-grupos', kwargs={'url': url})],
        ['projetos',reverse_lazy('index:edit-projetos', kwargs={'url': url})],        
    ]
    return menu

# menu grupo edit
def menu_edit_grupo(url):
    menu = [
        ['perfil',reverse_lazy('index:edit-perfil', kwargs={'url': url})],
        ['adms',reverse_lazy('index:edit-adms', kwargs={'url': url})],
        ['projetos',reverse_lazy('index:edit-projetos', kwargs={'url': url})],
        ['deletar',reverse_lazy('index:delete-grupo', kwargs={'url': url})],     
    ]
    return menu

# menu projeto edit
def menu_edit_projeto(url, purl):
    menu = [
        ['perfil',reverse_lazy('index:projeto-edit-perfil', kwargs={'url': url, 'purl': purl})],
        ['tags',reverse_lazy('index:projeto-edit-tags', kwargs={'url': url, 'purl': purl})],
        ['textos',reverse_lazy('index:projeto-edit-textos', kwargs={'url': url, 'purl': purl})],
        ['imagens',reverse_lazy('index:projeto-edit-imagens', kwargs={'url': url, 'purl': purl})],
        ['equipe',reverse_lazy('index:projeto-edit-equipe', kwargs={'url': url, 'purl': purl})],
        ['deletar',reverse_lazy('index:delete-projeto', kwargs={'url': url, 'purl': purl})],     
    ]
    return menu


#########################################################################################################################
# defs
#########################################################################################################################

def get_perfil(url):
    if url.user:
        perfil = url.user
        tipo = 'user'
    else:
        perfil = url.grupo
        tipo = 'grupo'
    return perfil, tipo

def remove_espacos(nome):
    nome = list(nome)
    for i in range(2):
        while nome[0] == ' ':
            nome.pop(0)
        nome.reverse()    
    return ''.join(nome)

