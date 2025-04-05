from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from string import ascii_letters, digits
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


#########################################################################################################################
# home
#########################################################################################################################

def index(request, url=None):
    user = request.user
    if url:
        url = get_object_or_404(Url, nome=url)
        
        if url.user:
            tipo = 'user'
            perfil = url.user
            
            if not perfil.is_active:
                raise Http404("conta desativada")
            
            pessoas = perfil.filhos.all()
            grupos = perfil.grupos.all()
            projetos = perfil.url.projetos.all()
            
            if perfil != user:
                pessoas = pessoas.filter(is_active=True)
                grupos = grupos.filter(publico=True)
                projetos = projetos.filter(publico=True)
        
        elif url.grupo:
            tipo = 'grupo'
            perfil = url.grupo

            # confere se o grupo é publico
            if not perfil.publico and user not in perfil.u0.all():
                raise Http404("grupo privado")
            
            pessoas = perfil.u0.all()
            grupos = None
            projetos = perfil.url.projetos.all()
            
            if user not in perfil.u0.all():
                pessoas = pessoas.filter(is_active=True)
                projetos = projetos.filter(publico=True)

    else:
        perfil = None
        url = None
        tipo = None
        pessoas = User.objects.filter(is_active=True)
        grupos = Grupo.objects.filter(publico=True)
        projetos = Projeto.objects.filter(publico=True)
    
    context = {
        'url': url,
        'perfil': perfil,
        'tipo': tipo,
        'pessoas': pessoas,
        'grupos': grupos,
        'projetos': projetos,
    }
    return render(request, 'index/home/_home.html', context)

# edit home
@login_required
def edit(request, url, ativo='perfil'):
    url = get_object_or_404(Url, nome=url)
    content= reverse(f'index:edit-{ativo}', kwargs={'url': url})

    # user
    if url.user:
        perfil = url.user
        
        # confere se o user é o dono do perfil
        if request.user != perfil:
            raise PermissionDenied
        
        # define variaveis
        tipo = 'user'
        grupos = perfil.grupos.all()
        menu = menu_edit_user(url)

    # grupo
    elif url.grupo:
        perfil = url.grupo
        
        # confere se o user pode editar o grupo
        if request.user not in perfil.u0.all():
            raise PermissionDenied

        # define variaveis
        tipo = 'grupo'
        grupos = None
        menu = menu_edit_grupo(url)

    context = {
        'url': url,
        'perfil': perfil,
        'tipo': tipo,
        'grupos': grupos,
        'menu': menu,
        'ativo': ativo,
        'content': content,
    }
    return render(request, 'index/edit/_home.html', context)


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
            form = UserForm(request.POST, instance=perfil, label_suffix='')
            template = 'index/edit/info_form.html'

            if form.has_changed() and form.is_valid() and request.user==perfil:
                form.save()
                msg = f'dados atualizados <b>{ form.changed_data }</b>'
        else:
            form = UserForm(instance=perfil, label_suffix='')
    
    # grupo
    elif url.grupo:
        perfil = url.grupo
        if request.method == "POST":
            form = GrupoForm(request.POST, instance=perfil, label_suffix='')
            template = 'index/edit/info_form.html'
            
            if form.has_changed() and form.is_valid() and request.user in perfil.u0.all():
                form.save()
                msg = f'dados atualizados <b>{ form.changed_data }</b>'
        else:
            form = GrupoForm(instance=perfil, label_suffix='')

    context = {
        'url': url,
        'form': form,
        'msg': msg,
    }
    return render(request, template, context)

# edit url
def edit_url(request, url):
    url = get_object_or_404(Url, nome=url)
    nova_url = request.POST.get('nova-url')

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
    }
    return render(request, 'index/base/msg_body.html', context)

#---------------------------------------------------------
# check url
def check_codinome(request, url=None):
    results = None
    if url:
        codinome = request.POST.get('nova-url')
        template = 'index/edit/url_results.html'    
    else:
        codinome = request.POST.get('username')
        template = 'index/convite/codinome_results.html'

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

    # context = {
    #     'msg': f'redirecinando para a página do convite...',
    #     'redirect': reverse('index:convite', kwargs={'pk': novo.pk}),
    # }
    # return render(request, 'index/base/msg_body.html', context)


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
    }
    return render(request, 'index/base/msg_clear.html', context)

#---------------------------------------------------------
# search adm
def search_adm(request, url):
    grupo = Grupo.objects.get(url__nome=url)
    busca = request.POST.get('search')
    results = User.objects.filter(nome__icontains=busca) | User.objects.filter(username__icontains=busca)
    results = results.exclude(grupos=grupo).exclude(is_active=False)
    
    context = {
        'results': results,
        'busca': busca,
        'url': grupo.url,
    }
    return render(request, 'index/add/adm_results.html', context)


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
    }
    return render(request, 'index/base/msg_body.html', context)

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
    }
    return render(request, 'index/base/msg_clear.html', context)

#---------------------------------------------------------
# mudar visibilidade
def grupo_visibilidade(request, url):
    grupo = get_object_or_404(Grupo, url__nome=url)
    template = request.POST.get('template')
    var = request.POST.get('var')
    n = request.POST.get('n')

    # confere se a url é diferente da id
    if str(grupo.url) != str(grupo.id):
        grupo.mudar_visibilidade()
    
    context = {
        var: grupo,
        'url': grupo.url, 
        'tipo': 'grupo',
        'n': n,
    }
    return render(request, template, context)

#---------------------------------------------------------
# check nome grupo+convite
def check_nome(request, url):
    if request.POST.get('novo-grupo'):
        nome = request.POST.get('novo-grupo')
        template = 'index/add/grupo_results.html'
    
    elif request.POST.get('novo-convite'):
        nome = request.POST.get('novo-convite')
        template = 'index/add/convite_results.html'

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
# perfil
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
    perfil = get_object_or_404(Url, nome=url)

    # grupos e pessoas podem criar projetos
    # verifica user
    if (perfil.user and user != perfil.user) or (perfil.grupo and user not in perfil.grupo.u0.all()):
        raise PermissionDenied

    nome = request.POST.get('novo-projeto')
    novo = Projeto(nome=nome, perfil=perfil, u0=user)
    novo.save()

    context = {
        'msg': f'redirecionando para a página de edições do novo projeto <b>{ novo.nome }</b>',
        'redirect': reverse('index:projeto-edit', kwargs={'url': perfil, 'purl': novo.url}),
    }
    return render(request, 'index/base/msg_body.html', context)

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
    return render(request, 'index/add/projeto_results.html', context)

#---------------------------------------------------------
# perfil projeto
#---------------------------------------------------------

# projeto index
def projeto(request, url, purl):
    editor = True
    perfil = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=perfil, url=purl)
    tags = projeto.tags.all()
    
    if (perfil.user and request.user != perfil.user) or (perfil.grupo and request.user not in perfil.grupo.u0.all()):
        if not projeto.publico: # verifica se o projeto é publico
            raise Http404("projeto privado")
        tags = tags.exclude(publico=False) # mostra apenas as tags publicas 
        editor = False

    context = {
        'projeto': projeto,
        'perfil': perfil,
        'tags': tags,
        'editor': editor,
    }
    return render(request, 'index/projeto/_home.html', context)

# edit projeto
@login_required
def projeto_edit(request, url, purl, ativo='info'):
    perfil = get_object_or_404(Url, nome=url)
    projeto = get_object_or_404(Projeto, perfil=perfil, url=purl)

    context = {
        'perfil': perfil,
        'projeto': projeto,
    }
    return render(request, 'index/projeto/edit/_home.html', context)



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
    busca = request.POST.get('search')
    results = User.objects.filter(nome__icontains=busca) | User.objects.filter(username__icontains=busca)
    results = results.exclude(is_active=False).exclude(url__nome=url) # exclui a mae e users inativos
    results = exclui_descendentes(results, filho)

    context = {
        'results': results,
        'busca': busca,
        'url': url,
        'filho': filho,
    }
    return render(request, 'index/edit/filhos_trans_results.html', context)


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
    }
    return render(request, 'index/base/msg_body.html', context)

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
    return render(request, 'index/convite/email_results.html', context)


#########################################################################################################################
# htmx
#########################################################################################################################

# clear
def clear(request):
    return HttpResponse('')


