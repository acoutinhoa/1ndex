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
from django.db.models import Count, Q

from index.models import *
from index.forms import *
from index.utils import *
from index.templatetags import index_tags


#########################################################################################################################
# home
#########################################################################################################################

# home
def index(request, url=None, filtros=None):
    user = request.user
    editor = False
    
    if url:
        url = get_object_or_404(Url, nome=url)
        perfil, tipo = get_perfil(url)
        
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
        'filtros': filtros,
    }
    return render(request, 'index/base/_home.html', context)


def tags(request, filtros, url=None):
    user = request.user
    editor = False
    tags = Tag.objects.all()
    projetos = Projeto.objects.all()

    if filtros == 'None':
        filtros = None
    else:
        filtros = filtros.split('/')
        filtros = tags.filter(id__in=filtros)
        tags = tags.exclude(id__in=filtros)
        for tag in filtros:
            projetos = projetos.filter(tags=tag)

    if url:
        url = get_object_or_404(Url, nome=url)
        projetos = projetos.filter(perfil=url)
        
        perfil, tipo = get_perfil(url)
        if (tipo == 'user' and user == perfil) or (tipo == 'grupo' and user in perfil.u0.all()):
            editor = True
    else:
        url = None
        
    if not editor:
        projetos = projetos.filter(publico=True)
        tags = tags.filter(publico=True)
    
    tags = tags.filter(projetos__id__in=projetos).annotate(Count("projetos")).order_by('-projetos__count', 'nome')

    context = {
        'url': url,
        'editor': editor,
        'projetos': projetos,
        'tags': tags,
        'filtros': filtros,
    }
    return render(request, 'index/base/_main.html', context)


# edit home
@login_required
def edit(request, url, ativo='perfil'):
    url = get_object_or_404(Url, nome=url)
    perfil, tipo = get_perfil(url)
    content= reverse(f'index:edit-{ativo}', kwargs={'url': url})

    # user
    if tipo == 'user':
        if request.user != perfil:
            raise PermissionDenied
        menu = menu_edit_user(url)

    # grupo
    elif tipo == 'grupo':
        if request.user not in perfil.u0.all():
            raise PermissionDenied
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
    perfil, tipo = get_perfil(url)
    template = 'index/edit/info.html'
    msg = None

    # user
    if tipo == 'user':
        if request.method == "POST":
            form = UserForm(request.POST, instance=perfil, label_suffix='', prefix='info')
            template = 'index/edit/info_form.html'

            if form.has_changed() and form.is_valid() and request.user==perfil:
                form.save()
                msg = f'dados atualizados <b>{ form.changed_data }</b>'
        else:
            form = UserForm(instance=perfil, label_suffix='', prefix='info')
    
    # grupo
    elif tipo == 'grupo':
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
    user = request.user
    url = get_object_or_404(Url, nome=url)
    perfil, tipo = get_perfil(url)

    # verifica user
    if (tipo=='user' and user != perfil) or (tipo=='grupo' and user not in perfil.u0.all()):
        raise PermissionDenied

    nova_url = request.POST.get('novo-url')
    url.nome = nova_url
    url.save()
    
    if tipo == 'user':
        perfil.username = url.nome
    perfil.save()
            
    context = {
        'msg': 'redirecionando para a nova url...',
        'redirect': reverse('index:edit', kwargs={'url': url}),
        'tipo': 'body',
    }
    return render(request, 'index/base/msg.html', context)

# edit links
def edit_links(request, url):
    url = get_object_or_404(Url, nome=url)
    perfil, tipo = get_perfil(url)
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
        'post': reverse('index:edit-links', kwargs={'url': url}),
    }
    return render(request, 'index/edit/links_form.html', context)

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

    context = {
        'url': grupo.url,
        'adms': adms,
    }
    return render(request, 'index/edit/adms.html', context)

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
    }
    if len(grupo.u0.all()) == 1:
        context['redirect'] = reverse('index:edit-adms', kwargs={'url': url})
    else:
        context['tipo'] = 'clear'
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
    perfil, perfil_tipo = get_perfil(url)

    # verifica user - só user pode criar grupo
    if perfil_tipo != 'user' or perfil != request.user:
        raise PermissionDenied
    
    nome = request.POST.get('novo-grupo')
    novo = Grupo.objects.create(nome=nome)
    novo.u0.add(perfil)

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

    grupo.mudar_visibilidade()

    # atualiza o d1 dos adms
    if grupo.publico:
        for user in grupo.u0.all():
            user.save()
    
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
    url = get_object_or_404(Url, nome=url)
    perfil, perfil_tipo = get_perfil(url)

    # grupos e pessoas podem criar projetos
    if (perfil_tipo == 'user' and user != perfil) or (perfil_tipo == 'grupo' and user not in perfil.u0.all()):
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
    perfil, perfil_tipo = get_perfil(url)

    # grupos e pessoas podem criar projetos
    if (perfil_tipo == 'user' and user != perfil) or (perfil_tipo == 'grupo' and user not in perfil.u0.all()):
        raise PermissionDenied
    
    # deleta imagens do projeto
    if projeto.imagens.exists():
        for imagem in projeto.imagens.all():
            imagem.imagem.delete()
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
    perfil, perfil_tipo = get_perfil(url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    tags = projeto.tags.all()
    links = projeto.links.all()
    editor = True

    if (perfil_tipo=='user' and user != perfil) or (perfil_tipo=='grupo' and user not in perfil.u0.all()):
        if not projeto.publico:
            raise Http404("projeto privado")
        editor = False
        tags = tags.exclude(publico=False)
    
    context = {
        'item': projeto,
        'url': url,
        'perfil': perfil,
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
    perfil, perfil_tipo = get_perfil(url)

    if (perfil_tipo == 'user' and user != perfil) or (perfil_tipo == 'grupo' and user not in perfil.u0.all()):
        raise PermissionDenied

    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    menu = menu_edit_projeto(url, purl)
    content = reverse(f'index:projeto-edit-{ativo}', kwargs={'url': url, 'purl': purl})

    context = {
        'url': url,
        'perfil': perfil,
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
                    projeto.save()
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
        'post': reverse('index:projeto-edit-links', kwargs={'url': url, 'purl':purl,}),
    }
    return render(request, 'index/edit/links_form.html', context)

# edit tags
def projeto_edit_tags(request, url, purl, publico=True,):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    tags = projeto.tags.all()

    # tags_all = Tag.objects.all().exclude(projetos=projeto)
    tags_index = Tag.objects.exclude(id__in=tags)
    tags_perfil = tags_index.filter(projetos__perfil=url).distinct().annotate(Count("projetos")).order_by('-projetos__count', 'nome')
    tags_index = tags_index.exclude(id__in=tags_perfil).exclude(publico=False).annotate(Count("projetos")).order_by('-projetos__count', 'nome')

    context = {
        'url': url,
        'projeto': projeto,
        'tags': tags,
        'tags_perfil': tags_perfil,
        'tags_index': tags_index,
        'publico': publico,
    }
    return render(request, 'index/projeto/edit/tags.html', context)

# search tags
def projeto_search_tags(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    results = ''
    
    publico = int(request.POST.get('publico'))
    busca = request.POST.get('novo-tag')
    if busca:
        busca = remove_espacos(busca)

    if publico:
        if busca:
            tags = Tag.objects.filter(nome__icontains=busca)
        else:
            tags = Tag.objects.all()
    
        tags = tags.exclude(projetos=projeto)
        tags_perfil = tags.filter(projetos__perfil=url).distinct()
        tags_index = tags.exclude(id__in=tags_perfil).exclude(publico=False)
    else:
        tags_perfil = None
        tags_index = None

    if busca and (not publico or not Tag.objects.filter(nome=busca).exists()):
        results = 'criar'

    context = {
        'url': url,
        'projeto': projeto,
        'tags_perfil': tags_perfil,
        'tags_index': tags_index,
        'results': results,
        'publico': publico,
    }
    return render(request, 'index/add/results_tags.html', context)

# add tags
def projeto_add_tag(request, url, purl, tag=None):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    
    if tag:
        nova_tag = get_object_or_404(Tag, id=tag)
    else:
        nova_tag = request.POST.get('novo-tag')
        publico = int(request.POST.get('publico'))
        nova_tag = remove_espacos(nova_tag)
        nova_tag = Tag.objects.create(nome=nova_tag, publico=publico)
    
    projeto.tags.add(nova_tag)

    return redirect('index:projeto-edit-tags', url=url, purl=purl)

# remove tags
@require_http_methods(['DELETE'])
def projeto_remove_tag(request, url, purl, tag):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    tag = get_object_or_404(Tag, id=tag)

    projeto.tags.remove(tag)

    if not tag.projetos.all():
        tag.delete()

    return redirect('index:projeto-edit-tags', url=url, purl=purl)

# edit texto
def projeto_edit_texto(request, url, purl, pk=None):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    textos = projeto.textos.filter(superior=None)

    # novo texto
    if request.method == "POST":
        form = TituloForm(request.POST, projeto=projeto, label_suffix='', prefix='novo')
        template = 'index/projeto/edit/titulo_form.html'
        if form.is_valid():
            texto = form.save(commit=False)
            print(texto)
            texto.projeto = projeto
            texto.save()

            context = {
                'msg': f'nova texto <b>{texto.titulo}</b> adicionado ao projeto <b>{projeto.nome}</b>',
                'class': 'legenda mt',
                'redirect': reverse('index:projeto-edit-textos', kwargs={'url': url, 'purl': projeto.url, 'pk': texto.pk}),
            }
            return render(request, 'index/base/msg.html', context)
    else:
        form = TituloForm(projeto=projeto, label_suffix='', prefix='novo')
        template = 'index/projeto/edit/texto.html'

    context = {
        'projeto': projeto,
        'url': url,
        'textos': textos,
        'form': form,
        'post' : reverse('index:projeto-edit-textos', kwargs={'url': url, 'purl': purl,}),
        'pk': pk,
    }
    return render(request, template, context)

# edit texto
def projeto_texto_form(request, pk):
    texto = get_object_or_404(Texto, pk=pk)
    projeto = texto.projeto

    if request.method == "POST":
        template = 'index/projeto/edit/texto_form.html'
        form = TextoForm(request.POST, instance=texto, label_suffix='', prefix='texto')
        if form.has_changed() and form.is_valid():
            form.save()
    else:
        template = 'index/projeto/edit/texto_info.html'
        form = TextoForm(instance=texto, label_suffix='', prefix='texto')
 
    context = {
        'texto': texto,
        'form': form,
        'post' : reverse('index:edit-texto', kwargs={'pk': pk}),
    }
    return render(request, template, context)

# edit titulo
def projeto_titulo_form(request, pk):
    texto = get_object_or_404(Texto, pk=pk)
    projeto = texto.projeto

    if request.method == "POST":
        form = TituloForm(request.POST, instance=texto, projeto=projeto, pk=texto.pk, label_suffix='', prefix='titulo')
        if form.is_valid():
            form.save()

            context = {
                'msg': f'texto <b>{texto}</b> atualizado',
                'class': 'legenda w80',
                'redirect': reverse('index:projeto-edit-textos', kwargs={'url': projeto.perfil, 'purl': projeto.url, 'pk': texto.pk}),
            }
            return render(request, 'index/base/msg.html', context)
    else:
        form = TituloForm(instance=texto, projeto=projeto, pk=texto.pk, label_suffix='', prefix='titulo')

    context = {
        'form': form,
        'texto': texto,
        'post' : reverse('index:edit-titulo', kwargs={'pk': pk}),
        'target': '#titulo',
    }
    return render(request, 'index/projeto/edit/titulo_form.html', context)

# mudar visibilidade
def projeto_texto_visibilidade(request, pk):
    def sub_visibilidade(lista, visibilidade):
        for item in lista:
            item.publico = visibilidade
            item.save()
            if item.subtextos.exists():
                sub_visibilidade(item.subtextos.all(), visibilidade)

    texto = get_object_or_404(Texto, pk=pk)
    projeto = texto.projeto
    texto.mudar_visibilidade()
    if texto.subtextos.exists():
        sub_visibilidade(texto.subtextos.all(), texto.publico)

    context = {
        'projeto': projeto,
        'lista': projeto.textos.filter(superior=None),
        'url': projeto.perfil,
    }
    return render(request, 'index/base/titulos_lista.html', context)

# deletar visibilidade
@require_http_methods(['DELETE'])
def delete_texto(request, pk):
    def sub_delete(lista):
        for item in lista:
            if item.subtextos.exists():
                sub_delete(item.subtextos.all())
            item.delete()

    texto = get_object_or_404(Texto, pk=pk)
    if texto.subtextos.exists():
        sub_delete(texto.subtextos.all())
    texto.delete()
    projeto = texto.projeto

    context = {
        'msg': f'texto <b>{texto.titulo}</b> removido do projeto <b>{projeto.nome}</b>',
        'redirect': reverse('index:projeto-edit-textos', kwargs={'url': projeto.perfil, 'purl': projeto.url,}),
    }
    return render(request, 'index/base/msg.html', context)

def projeto_edit_imagens(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)
    atualizado = []

    if request.method == "POST":
        formset = ImagensFormSet(request.POST, request.FILES, instance=projeto, prefix='imagem')
        if formset.is_valid():
            atualizado = formset.save()
            formset = ImagensFormSet(instance=projeto, prefix='imagem')
        template = 'index/projeto/edit/imagens_form.html'
        form = None
    
    else:
        formset = ImagensFormSet(instance=projeto, prefix='imagem')
        form = ImagemForm(prefix='nova_imagem')
        template = 'index/projeto/edit/imagens.html'
    
    context = {
        'formset': formset,
        'form': form,
        'imagens': projeto.imagens.all(),
        'atualizado': atualizado,
        'post': reverse('index:projeto-edit-imagens', kwargs={'url': url, 'purl':purl,}),
        'add': reverse('index:projeto-add-imagem', kwargs={'url': url, 'purl':purl}),
    }
    return render(request, template, context)

# edit imagens add
def projeto_add_imagem(request, url, purl):
    url = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=url, url=purl)

    form = ImagemForm(request.POST, request.FILES, prefix='nova_imagem')
    if form.is_valid():
        novo = form.save(commit=False)
        novo.projeto = projeto
        novo.save()
        projeto.save()

        context = {
            'msg': f'nova imagem adicionada ao projeto <b>{ projeto.nome }</b>',
            'class': 'legenda mt',
            'redirect': reverse('index:projeto-edit-imagens', kwargs={'url': url, 'purl': projeto.url}),
        }
        return render(request, 'index/base/msg.html', context)
    
    context = {
        'add': reverse('index:projeto-add-imagem', kwargs={'url': url, 'purl':purl}),
        'form': form,
    }
    return render(request, 'index/projeto/edit/imagens_novo_form.html', context)

# delte imagem
@require_http_methods(['DELETE'])
def delete_imagem(request, pk):
    imagem = get_object_or_404(Imagem, pk=pk)
    imagem.imagem.delete()
    imagem.delete()

    context = {
        'msg': f'imagem <b>{ imagem.nome }</b> excluida',
        'redirect': request.GET.get('redirect'),
        'class': 'legenda mt mb2',
    }
    return render(request, 'index/base/msg.html', context)


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
    perfil, perfil_tipo = get_perfil(url)

    template = request.POST.get('template')

    projeto.mudar_visibilidade()
    
    # atualiza o d1 dos adms
    if projeto.publico:
        perfil.save()
    
    context = {
        'tipo': 'projeto',
        'item': projeto,
        'url': url,
        'perfil': perfil,
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

# pronome
def pronome(request):
    pronome = request.GET.get('pronome')
    return HttpResponse(index_tags.pronome(pronome))
