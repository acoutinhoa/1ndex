from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from string import ascii_letters, digits, ascii_lowercase
from django.conf import settings
from django.utils.text import slugify

from .models import *
from .forms import *


url_proibidas = ['htmx', 'admin', 'accounts', 'invite', 'edit', 'add', 'delete',] 

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
        ['texto',reverse_lazy('index:projeto-edit-texto', kwargs={'url': url, 'purl': purl})],
        ['imagens',reverse_lazy('index:projeto-edit-imagens', kwargs={'url': url, 'purl': purl})],
        ['equipe',reverse_lazy('index:projeto-edit-equipe', kwargs={'url': url, 'purl': purl})],
        ['deletar',reverse_lazy('index:delete-projeto', kwargs={'url': url, 'purl': purl})],     
    ]
    return menu


#########################################################################################################################
# home
#########################################################################################################################

def get_perfil(url, get_tipo=False):
    if url.user:
        perfil = url.user
        tipo = 'user'
    elif url.grupo:
        perfil = url.grupo
        tipo = 'grupo'

    if get_tipo:
        return perfil, tipo
    return perfil

#----------------------------------------------------------

# home
def index(request, url=None):
    user = request.user
    editor = False
    
    if url:
        url = get_object_or_404(Url, nome=url)
        perfil, tipo = get_perfil(url, get_tipo=True)
        
        if tipo == 'user':
            if not perfil.is_active:
                raise Http404("conta desativada")
            if user == perfil:
                editor = True
            grupos = perfil.grupos.all()
            pessoas = perfil.filhos.all()
        
        elif tipo == 'grupo':
            if not perfil.publico and user not in perfil.u0.all():
                raise Http404("grupo privado")
            if user in perfil.u0.all():
                editor = True
            grupos = None
            pessoas = perfil.u0.all()
           
        links = perfil.links.all()
        projetos = url.projetos.all()        
        if not editor:
            pessoas = pessoas.filter(is_active=True)
            projetos = projetos.filter(publico=True)
            if grupos:
                grupos = grupos.filter(publico=True)

    else:
        perfil = None
        url = None
        tipo = None
        links = None
        pessoas = User.objects.filter(is_active=True)
        grupos = Grupo.objects.filter(publico=True)
        projetos = Projeto.objects.filter(publico=True)
    
    context = {
        'url': url,
        'item': perfil,
        'tipo': tipo,
        'editor': editor,
        'pessoas': pessoas,
        'grupos': grupos,
        'projetos': projetos,
        'links': links,
    }
    return render(request, 'index/base/_home.html', context)

# edit home
@login_required
def edit(request, url, ativo='perfil'):
    url = get_object_or_404(Url, nome=url)
    content= reverse(f'index:edit-{ativo}', kwargs={'url': url})

    # user
    if url.user:
        perfil = url.user
        
        if request.user != perfil:
            raise PermissionDenied
        
        tipo = 'user'
        menu = menu_edit_user(url)

    # grupo
    elif url.grupo:
        perfil = url.grupo
        
        if request.user not in perfil.u0.all():
            raise PermissionDenied

        tipo = 'grupo'
        menu = menu_edit_grupo(url)

    context = {
        'url': url,
        'item': perfil,
        'tipo': tipo,
        'menu': menu,
        'ativo': ativo,
        'content': content,
        'extra': 'edit',
    }
    return render(request, 'index/base/_edit.html', context)


#########################################################################################################################
# info
#########################################################################################################################

# edit info
def edit_info(request, url):
    url = get_object_or_404(Url, nome=url)
    template = 'index/edit/info.html'
    msg = None

    # user
    if url.user:
        perfil = url.user
        if request.method == "POST":
            form = UserForm(request.POST, instance=perfil, label_suffix='', prefix='info')
            template = 'index/edit/info_form.html'

            if form.has_changed() and form.is_valid() and request.user==perfil:
                form.save()
                msg = f'dados atualizados <b>{ form.changed_data }</b>'
        else:
            form = UserForm(instance=perfil, label_suffix='', prefix='info')
    
    # grupo
    elif url.grupo:
        perfil = url.grupo
        if request.method == "POST":
            form = GrupoForm(request.POST, instance=perfil, label_suffix='', prefix='info')
            template = 'index/edit/info_form.html'
            
            if form.has_changed() and form.is_valid() and request.user in perfil.u0.all():
                form.save()
                msg = f'dados atualizados <b>{ form.changed_data }</b>'
        else:
            form = GrupoForm(instance=perfil, label_suffix='', prefix='info')

    context = {
        'url': url,
        'form': form,
        'msg': msg,
    }
    return render(request, template, context)

# edit url
def edit_url(request, url):
    url = get_object_or_404(Url, nome=url)
    nova_url = request.POST.get('novo-url')

    # verifica user
    if not ( request.user == url.user or request.user in url.grupo.u0.all() ):
        raise PermissionDenied

    url.nome = nova_url
    url.save()
    
    if url.grupo:
        url.grupo.save()
    elif url.user:
        url.user.username = url.nome
        url.user.save()
            
    context = {
        'msg': 'redirecionando para a nova url...',
        'redirect': reverse('index:edit', kwargs={'url': url}),
        'tipo': 'body',
    }
    return render(request, 'index/base/msg.html', context)

# edit links
def edit_links(request, url):
    url = get_object_or_404(Url, nome=url)
    perfil = get_perfil(url)
    links = perfil.links.all()
    novo = ''
    atualizado = []

    if request.method == "POST":
        formset = LinksFormSet(request.POST, queryset=links, prefix='link')
        if formset.is_valid():
            novos_links = formset.save()
            # verifica os links e adiciona os novos
            for link in novos_links:
                if link not in links:
                    perfil.links.add(link)
                    novo = link.id
                atualizado.append(link.id)

            # atualiza o formset
            links = perfil.links.all()
            formset = LinksFormSet(queryset=links, prefix='link')
    else:
        formset = LinksFormSet(queryset=links, prefix='link')
    
    context = {
        'formset': formset,
        'links': links,
        'novo': novo,
        'atualizado': atualizado,
        'redirect': reverse('index:edit-links', kwargs={'url': url}),
    }
    return render(request, 'index/edit/links_form.html', context)

#---------------------------------------------------------
# check codinome
def check_codinome(request, url=None):
    results = None
    if url:
        codinome = request.POST.get('novo-url')
        template = 'index/add/results_url.html'    
    else:
        codinome = request.POST.get('username')
        template = 'index/convite/results_codinome.html'

    def car_proibido(nome):
        caracteres = digits + ascii_letters + '_@+.-'
        for car in nome:
            if car not in caracteres:
                return car
        return None

    if url != codinome:
        if len(codinome) < 2:
            results = 'size'
        elif car_proibido(codinome):
            results = car_proibido(codinome)
        elif Url.objects.filter(nome=codinome).exists() or codinome in url_proibidas:
            results = 'no'
        else:
            results = 'ok'
    
    context = {
        'url': url,
        'results': results,
    }
    return render(request, template, context)


#########################################################################################################################
# filhos
#########################################################################################################################

# edit filhos
def edit_filhos(request, url):
    user = get_object_or_404(User, url__nome=url)

    # verifica user
    if request.user != user:
        raise PermissionDenied
    
    template = request.GET.get('template')
    if not template:
        template = 'index/edit/filhos.html'

    context = {
        'url': user.url,
        'filhos': user.filhos.filter(is_active=True),
        'trans': user.filhos.filter(is_active=False),
        'convites': user.convites.all(),
    }
    return render(request, template, context)

# add convite
def add_convite(request, url):
    user = get_object_or_404(User, url__nome=url)

    # verifica user
    if request.user != user:
        raise PermissionDenied
    
    nome = request.POST.get('novo-convite')
    novo = Convite.objects.create(nome=nome, u0=user)

    return redirect('index:convite', pk=novo.pk)


#########################################################################################################################
# adms
#########################################################################################################################

# edit adms
def edit_adms(request, url):
    grupo = get_object_or_404(Grupo, url__nome=url)
    adms = grupo.u0.all()
    template = request.GET.get('template')
    if not template:
        template = 'index/edit/adms.html'

    context = {
        'url': grupo.url,
        'adms': adms,
    }
    return render(request, template, context)

# add adm
def add_adm(request, url):
    user = request.user
    grupo = get_object_or_404(Grupo, url__nome=url)

    # verifica user
    if user not in grupo.u0.all():
        raise PermissionDenied

    novo_adm = request.POST.get('novo-adm')
    novo_adm = User.objects.get(id=novo_adm)
    grupo.u0.add(novo_adm)

    context = {
        'msg': f'adm <b>{ novo_adm }</b> adicionado ao grupo <b>{ grupo.nome }</b>',
        'redirect': reverse('index:edit-adms', kwargs={'url': url}),
        'class': 'mt legenda',
    }
    return render(request, 'index/base/msg.html', context)

# delete adm
@login_required
@require_http_methods(['DELETE'])
def delete_adm(request, url, pk):
    user = request.user
    grupo = get_object_or_404(Grupo, url__nome=url)
    
    # verifica se o user tem autorizacao pra deletar  
    # um grupo não pode ficar sem adms
    if not (user in grupo.u0.all() and grupo.u0.all().count() > 1):
        raise PermissionDenied

    adm = get_object_or_404(User, pk=pk)
    grupo.u0.remove(adm)
    
    if user == adm:
        return redirect('index:index')
    
    context = {
        'msg': f'adm <b>{ adm }</b> removido do grupo <b>{ grupo.nome }</b>',
        'class': 'legenda mt1',
        'tipo': 'clear',
    }
    return render(request, 'index/base/msg.html', context)

#---------------------------------------------------------
# search adm
def search_adm(request, url):
    grupo = Grupo.objects.get(url__nome=url)
    busca = request.POST.get('novo-adm')
    results = User.objects.filter(nome__icontains=busca) | User.objects.filter(username__icontains=busca)
    results = results.exclude(grupos=grupo).exclude(is_active=False)
    
    context = {
        'results': results,
        'busca': busca,
        'url': grupo.url,
    }
    return render(request, 'index/add/results_adm.html', context)


#########################################################################################################################
# grupos
#########################################################################################################################

# edit grupos
def edit_grupos(request, url):
    url = get_object_or_404(Url, nome=url)
    grupos = url.user.grupos.all()
    
    template = request.GET.get('template')
    if not template:
        template = 'index/edit/grupos.html'

    context = {
        'url': url,
        'grupos': grupos,
    }
    return render(request, template, context)

# add grupo
def add_grupo(request, url):
    url = get_object_or_404(Url, nome=url)

    # verifica user - só user pode criar grupo
    if not url.user or url.user != request.user:
        raise PermissionDenied
    
    nome = request.POST.get('novo-grupo')
    novo = Grupo.objects.create(nome=nome)
    novo.u0.add(url.user)

    context = {
        'msg': f'redirecionando para a página de edições do novo grupo <b>{ novo.nome }</b>',
        'redirect': reverse('index:edit', kwargs={'url': novo.url}),
        'tipo': 'body',
    }
    return render(request, 'index/base/msg.html', context)

# delete grupo
@login_required
@require_http_methods(['DELETE'])
def delete_grupo(request, url):
    user = request.user
    grupo = get_object_or_404(Grupo, url__nome=url)
        
    # verifica se o user tem autorizacao pra deletar
    if user not in grupo.u0.all():
        raise PermissionDenied
    
    grupo.delete()
    
    if request.GET.get('redireciona'):
        return redirect('index:edit-ativo', url=user.url, ativo='grupos')

    context = {
        'msg': f'grupo <b>{ grupo.nome }</b> deletado',
        'class': 'legenda mt1',
        'tipo': 'clear',
    }
    return render(request, 'index/base/msg.html', context)

#---------------------------------------------------------
# mudar visibilidade
def grupo_visibilidade(request, url):
    grupo = get_object_or_404(Grupo, url__nome=url)
    template = request.POST.get('template')
    # var = request.POST.get('var')

    grupo.mudar_visibilidade()
    
    context = {
        'item': grupo,
        'url': grupo.url, 
        'tipo': 'grupo',

        'n': request.POST.get('n'),
        'extra': 'edit',
    }
    return render(request, template, context)

#---------------------------------------------------------
# check nome grupo+convite
def check_nome(request, url):
    if request.POST.get('novo-grupo'):
        nome = request.POST.get('novo-grupo')
        template = 'index/add/results_grupo.html'
    
    elif request.POST.get('novo-convite'):
        nome = request.POST.get('novo-convite')
        template = 'index/add/results_convite.html'

    if len(nome.replace(" ", "")) >= 2:
        results = 'yes'
    else:
        results = 'no'
            
    context = {
        'url': url,
        'results': results,
    }
    return render(request, template, context)


#########################################################################################################################
# projetos
#########################################################################################################################

#---------------------------------------------------------
# edit projetos do perfil
def edit_projetos(request, url):
    url = get_object_or_404(Url, nome=url)
    projetos = Projeto.objects.filter(perfil=url)

    context = {
        'url': url,
        'projetos': projetos,
    }
    return render(request, 'index/edit/projetos.html', context)

# add projeto
def add_projeto(request, url):
    user = request.user
    url= get_object_or_404(Url, nome=url)

    # grupos e pessoas podem criar projetos
    if (url.user and user != url.user) or (url.grupo and user not in url.grupo.u0.all()):
        raise PermissionDenied

    nome = request.POST.get('novo-projeto')
    novo = Projeto(nome=nome, perfil=url, u0=user)
    novo.save()

    context = {
        'msg': f'redirecionando para a página de edições do novo projeto <b>{ novo.nome }</b>',
        'redirect': reverse('index:projeto-edit', kwargs={'url': url, 'purl': novo.url}),
        'tipo': 'body',
    }
    return render(request, 'index/base/msg.html', context)

# delete projeto
@login_required
@require_http_methods(['DELETE'])
def delete_projeto(request, url, purl):
    user = request.user
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
        
    if (url.user and user != url.user) or (url.grupo and user not in url.grupo.u0.all()):
        raise PermissionDenied
    
    projeto.delete()
    
    if request.GET.get('redireciona'):
        return redirect('index:edit-ativo', url=url, ativo='projetos')

    context = {
        'msg': f'projeto <b>{ projeto.nome }</b> deletado',
        'class': 'legenda mt1',
        'tipo': 'clear',
    }
    return render(request, 'index/base/msg.html', context)

#---------------------------------------------------------
# check projeto
def check_projeto(request, url):
    nome = request.POST.get('novo-projeto')
    
    if len(nome.replace(" ", "")) < 2:
        results = 'size'
    elif slugify(nome) in url_proibidas:
        results = 'no'
    else:
        results = 'ok'
            
    context = {
        'url': url,
        'results': results,
    }
    return render(request, 'index/add/results_projeto.html', context)

#---------------------------------------------------------
# projeto
#---------------------------------------------------------

# projeto home
def projeto(request, url, purl):
    user = request.user
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    tags = projeto.tags.all()
    links = projeto.links.all()
    editor = True
    
    if (url.user and user != url.user) or (url.grupo and user not in url.grupo.u0.all()):
        if not projeto.publico:
            raise Http404("projeto privado")
        editor = False
        tags = tags.exclude(publico=False)

    context = {
        'item': projeto,
        'url': url,
        'perfil': get_perfil(url),
        'tags': tags,
        'links': links,
        'editor': editor,
        'tipo': 'projeto',
    }
    return render(request, 'index/base/_home.html', context)

# edit projeto
@login_required
def projeto_edit(request, url, purl, ativo='perfil'):
    user = request.user
    url = get_object_or_404(Url, nome=url)
    if (url.user and user != url.user) or (url.grupo and user not in url.grupo.u0.all()):
        raise PermissionDenied

    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    menu = menu_edit_projeto(url, purl)
    content = reverse(f'index:projeto-edit-{ativo}', kwargs={'url': url, 'purl': purl})

    context = {
        'url': url,
        'perfil': get_perfil(url),
        'item': projeto,
        'ativo': ativo,
        'menu': menu,
        'content': content,
        'tipo': 'projeto',
        'extra': 'edit',
    }
    return render(request, 'index/base/_edit.html', context)

# edit info
def projeto_edit_info(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    template = 'index/projeto/edit/info.html'
    msg = None
    redirect = None

    if request.method == "POST":
        form = ProjetoForm(request.POST, instance=projeto, label_suffix='', prefix='info')

        if form.has_changed() and form.is_valid():
            projeto = form.save(commit=False)
            if 'nome' in form.changed_data:
                projeto.url = projeto.define_url()
                redirect = reverse('index:projeto-edit', kwargs={'url': url, 'purl': projeto.url })
            projeto.save()
            msg = f'dados atualizados <b>{ form.changed_data }</b>'
            template = 'index/projeto/edit/info_form.html'
    else:
        form = ProjetoForm(instance=projeto, label_suffix='', prefix='info')
    
    context = {
        'url': url,
        'projeto': projeto,
        'form': form,
        'msg': msg,
        'redirect': redirect,
    }
    return render(request, template, context)

# edit links
def projeto_edit_links(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    links = projeto.links.all()
    novo = ''
    atualizado = []

    if request.method == "POST":
        formset = LinksFormSet(request.POST, queryset=links, prefix='link')
        if formset.is_valid():
            novos_links = formset.save()
            # verifica os links e adiciona os novos
            for link in novos_links:
                if link not in links:
                    projeto.links.add(link)
                    novo = link.id
                atualizado.append(link.id)

            # atualiza o formset
            links = projeto.links.all()
            formset = LinksFormSet(queryset=links, prefix='link')
    else:
        formset = LinksFormSet(queryset=links, prefix='link')
    
    context = {
        'formset': formset,
        'links': links,
        'novo': novo,
        'atualizado': atualizado,
        'redirect': reverse('index:projeto-edit-links', kwargs={'url': url, 'purl':purl,}),
    }
    return render(request, 'index/edit/links_form.html', context)

# edit tags
def projeto_edit_tags(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)

    context = {
        'url': url,
        'projeto': projeto,
    }
    return render(request, 'index/projeto/edit/tags.html', context)


# edit texto
def projeto_edit_texto(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    msg = None
    template = 'index/projeto/edit/texto.html'

    if request.method == "POST":
        form = ProjetoTextoForm(request.POST, instance=projeto, label_suffix='')

        if form.has_changed() and form.is_valid():
            form.save()
            msg = f'texto de <b>{ projeto.nome }</b> atualizado'
            template = 'index/projeto/edit/texto_form.html'
    else:
        form = ProjetoTextoForm(instance=projeto, label_suffix='')
    
    context = {
        'url': url,
        'projeto': projeto,
        'form': form,
        'msg': msg,
    }
    return render(request, template, context)

# edit imagens
def projeto_edit_imagens(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)

    context = {
        'url': url,
        'projeto': projeto,
    }
    return render(request, 'index/projeto/edit/imagens.html', context)

# edit equipe
def projeto_edit_equipe(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)

    context = {
        'url': url,
        'projeto': projeto,
    }
    return render(request, 'index/projeto/edit/equipe.html', context)


#---------------------------------------------------------
# mudar visibilidade
def projeto_visibilidade(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    template = request.POST.get('template')

    projeto.mudar_visibilidade()
    
    context = {
        'tipo': 'projeto',
        'item': projeto,
        'url': url,
        'perfil': get_perfil(url),
        'n': request.POST.get('n'),
        'extra': 'edit',
    }
    return render(request, template, context)

#########################################################################################################################
# trabalhos
#########################################################################################################################

# edit trabalhos
def edit_trabalhos(request, url):
    url = get_object_or_404(Url, nome=url)

    context = {
        'url': url,
    }
    return render(request, 'index/edit/trabalhos.html', context)


#########################################################################################################################
# responsabilidade
#########################################################################################################################

# funcao para alterar o status dos descendentes
def status_descendentes(user, status):
    user.is_active = status
    user.save()
    if user.filhos.exists():
        for filho in user.filhos.all():
            status_descendentes(filho, status)

# transferir
def responsa_transferir(request, url, pk):
    filho = get_object_or_404(User, id=pk)

    if request.method == "POST":
        mae = get_object_or_404(User, url__nome=url)
        nova_mae = get_object_or_404(User, id=request.POST.get('nova-mae'))
        
        if request.user == mae:
            filho.u0 = nova_mae
            status_descendentes(filho, False)

            context = {
                'msg': f'tranferência de responsabilidade de <b>{ filho }</b> enviada para <b>{ nova_mae }</b>',
                'redirect': reverse('index:edit-filhos', kwargs={'url': url}),
                'cor': '1',
            }
            return render(request, 'index/base/msg.html', context)

    context = {
        'url': url,
        'filho': filho,
    }
    return render(request, 'index/edit/filhos_trans.html', context)

# aceitar
def responsa_aceitar(request, url, pk):
    user = get_object_or_404(User, url__nome=url)
    filho = get_object_or_404(User, id=pk)
    
    # verifica se o user tem autorizacao 
    if request.user==user and user==filho.u0:
        status_descendentes(filho, True)
    
    context = {
        'msg': f'user <b>{ filho }</b> adicionado aos filhos',
        'redirect': reverse('index:edit-filhos', kwargs={'url': url}),
    }
    return render(request, 'index/base/msg.html', context)

# recusar
def responsa_recusar(request, url, pk):
    user = get_object_or_404(User, url__nome=url)
    filho = get_object_or_404(User, id=pk)
    
    # verifica se o user tem autorizacao 
    if request.user==user and user==filho.u0:
        filho.u0 = None
        filho.save()
    
    context = {
        'msg': f'user <b>{ filho }</b> recusado',
        'redirect': reverse('index:edit-filhos', kwargs={'url': url}),
    }
    return render(request, 'index/base/msg.html', context)

# inativar
@login_required
@require_http_methods(['DELETE'])
def responsa_inativar(request, url, pk):
    user = get_object_or_404(User, url__nome=url)
    filho = get_object_or_404(User, id=pk)
    
    # verifica se o user tem autorizacao 
    if request.user==user and user==filho.u0:
        filho.u0 = None
        status_descendentes(filho, False)
    
    context = {
        'msg': f'user <b>{ filho }</b> e descendentes inativos',
        'redirect': reverse('index:edit-filhos', kwargs={'url': url}),
    }
    return render(request, 'index/base/msg.html', context)

#---------------------------------------------------------
# search mae
def search_mae(request, url, pk):
    def exclui_descendentes(results, user):
        results = results.exclude(id=user.id)
        if user.filhos.exists():
            for filho in user.filhos.all():
                results = exclui_descendentes(results, filho)
        return results
    
    filho = User.objects.get(id=pk)
    busca = request.POST.get('novo-mae')
    results = User.objects.filter(nome__icontains=busca) | User.objects.filter(username__icontains=busca)
    results = results.exclude(is_active=False).exclude(url__nome=url) # exclui a mae e users inativos
    results = exclui_descendentes(results, filho)

    context = {
        'results': results,
        'busca': busca,
        'url': url,
        'filho': filho,
    }
    return render(request, 'index/add/results_trans.html', context)


#########################################################################################################################
# convite
#########################################################################################################################

def convite(request,  pk):
    convite = get_object_or_404(Convite, pk=pk)

    if request.method == 'POST':
        form = ConviteForm(request.POST, instance=convite, label_suffix="")
        if form.is_valid():
            convite = form.save()
            if request.POST["reativar"]:
                return redirect('index:reativar', pk=convite.pk)
            else:
                return redirect('index:cadastro', pk=convite.pk)
    else:
        form = ConviteForm(instance=convite, label_suffix="")

    context = {
        'convite': convite,
        'form': form,
    }
    return render(request, 'index/convite/convite.html', context)

def cadastro(request,  pk):
    convite = get_object_or_404(Convite, pk=pk)

    if request.method == 'POST':
        form = RegistrationForm(request.POST, label_suffix="")
        if form.is_valid():
            user = form.save(commit=False)
            user.email = convite.email
            user.nome = convite.nome
            user.u0 = convite.u0
            user.pronome = convite.pronome
            user.save()
            convite.delete()
            login(request,user)

            return redirect('index:edit', url=user.url)
    else:
        form = RegistrationForm(label_suffix="")

    context = {
        'convite': convite,
        'form': form,
    }
    return render(request, 'index/convite/cadastro_form.html', context)

def trans_convite(request,  pk):
    convite = get_object_or_404(Convite, pk=pk)
    user = request.user
    user.u0 = convite.u0
    if not user.is_active:
        status_descendentes(user, True)
    convite.delete()

    context = {
        'msg': f'conta de <b>{ user }</b> transferida para a responsabilidade de <b>{ convite.u0 }</b>',
        'redirect': reverse('index:edit', kwargs={'url': user.url}),
        'class': 'legenda mt mb1',
        'tipo': 'body',
    }
    return render(request, 'index/base/msg.html', context)

@login_required
@require_http_methods(['DELETE'])
def delete_convite(request,  pk):
    convite = get_object_or_404(Convite, id=pk)

    if request.user == convite.u0:
        convite.delete()

    context = {
        'msg': f'convite <b>{ convite.nome }</b> deletado',
        'redirect': reverse('index:edit-filhos', kwargs={'url': convite.u0.url}), # retorna pra pagina do user de edicao de filhos
        'target': '#content',
        'template': 'index/edit/filhos.html',
    }
    return render(request, 'index/base/msg.html', context)

def reativar(request, pk):
    convite = get_object_or_404(Convite, pk=pk)

    if request.method == 'POST':
        form = ReativarForm(request.POST, label_suffix="")
        username = form.data["username"]
        password = form.data["password"]
        User.objects.filter(email=convite.email).update(is_active=True) # ativa o user
        user = authenticate(request, username=username, password=password) # tenta autenticar

        # verifica se o user é o mesmo do email
        if user is not None and user.email == convite.email:
            user.u0 = convite.u0 
            user.save()
            convite.delete()
            login(request, user) 
            
            return redirect('index:perfil', url=user.url)

        else:
            User.objects.filter(email=convite.email).update(is_active=False) # desativa o user
            if user is None:
                form.add_error(None, 'codinome ou senha inválidos')
            elif user.email != convite.email:
                form.add_error(None, f'este codinome não está vinculado ao email {convite.email}')
    else:
        form = ReativarForm(label_suffix="")

    context = {
        'convite': convite,
        'form': form,
    }
    return render(request, 'index/convite/reativar.html', context)


#---------------------------------------------------------
# check email
def check_email(request, pk):
    convite = get_object_or_404(Convite, pk=pk)
    email = request.POST.get('email')

    if User.objects.filter(email=email).exists():
        perfil = User.objects.get(email=email)
    else:
        perfil = None
            
    context = {
        'perfil': perfil,
        'convite': convite,
    }
    return render(request, 'index/convite/results_email.html', context)


#########################################################################################################################
# htmx
#########################################################################################################################

# clear
def clear(request):
    return HttpResponse('')

# delte link
@login_required
@require_http_methods(['DELETE'])
def delete_link(request, pk):
    link = get_object_or_404(Link, pk=pk)
    link.delete()

    context = {
        'msg': f'link <b>{ link.nome }</b> excluido',
        'redirect': request.GET.get('redirect'),
        'target': '#form-links',
        'class': 'legenda mt2 mb2',
    }
    return render(request, 'index/base/msg.html', context)

