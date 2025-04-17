from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from .models import *
import datetime

# user info edit
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nome','pronome','info',]
        widgets = { 
            'info': forms.Textarea(attrs={'rows': 5, 'placeholder': 'breve descrição', }),
            'pronome': forms.RadioSelect(attrs={'class': 'choices'}),
            }

# grupo info edit
class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nome','info']
        widgets = { 
            'info': forms.Textarea(attrs={'rows': 5, 'placeholder': 'breve descrição do grupo', }),
            }

# url
class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = ['nome',]

# convite
class ConviteForm(forms.ModelForm):
    class Meta:
        model = Convite
        fields = ['pronome','email',]
        widgets = { 
            'pronome': forms.RadioSelect(attrs={'class': 'choices'}),
            }

# cadastro
class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',]

# reativar
class ReativarForm(forms.Form):
    username = forms.CharField(label='codinome')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

# projetos 
class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['nome', 'url', 'ano', 'etapa', 'info']
        widgets = { 
            'info': forms.Textarea(attrs={'rows': 5, 'placeholder': 'breve descrição do projeto', }),
            }

# projetos texto
class ProjetoTextoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['texto']
        widgets = { 
            'texto': forms.Textarea(attrs={'rows': 19, 'placeholder': 'texto do projeto', }),
            }

# projetos imagem
ImagemForm = forms.inlineformset_factory(
    Projeto,
    Imagem,
    fields = ['imagem',],
    extra = 1,
    widgets = {
        # 'imagem': forms.FileInput(attrs={'placeholder': 'selecione uma imagem',}),
        },
)

# projeto imagens
ImagensFormSet = forms.inlineformset_factory(
    Projeto,
    Imagem,
    fields = ["nome", "imagem", "capa", "carrossel"],
    can_delete = False,
    extra = 1,
    widgets = { 
        'nome': forms.TextInput(attrs={'placeholder': 'nova imagem', }),
        'imagem': forms.FileInput(attrs={'placeholder': 'selecione uma imagem',}),
    },
   # can_order = True,
)

# class ImagemForm(forms.ModelForm):
#     class Meta:
#         model = Imagem
#         fields = ["imagem", "projeto"]
#         widgets = { 
#             }
        
# # projeto imagens
# ImagensFormSet = modelformset_factory(
#     Imagem,
#     fields = ["nome", "imagem", "capa", "carrossel"],
#     extra = 1,
#     widgets = { 
#         'nome': forms.TextInput(attrs={'placeholder': 'nova imagem', }),
#         'imagem': forms.FileInput(attrs={'placeholder': 'selecione uma imagem',}),
#     },
# # can_order = True,
# )

# links
LinksFormSet = modelformset_factory(
    Link,
    fields = ["nome", "url"],
    extra = 1,
    max_num = 10,
    widgets = { 
        'url': forms.Textarea(attrs={'rows': 1, 'placeholder': 'http://', }),
        'nome': forms.Textarea(attrs={'rows': 1, 'placeholder': 'novo link', }),
    },
   # can_order = True,
)

# ##########################################################
# # pacientes

# class NomeForm(forms.ModelForm):
#     class Meta:
#         model = Paciente
#         fields = ['nome',]

# class PacienteForm(forms.ModelForm):
#     class Meta:
#         model = Paciente
#         fields = ['nome','cpf', 'nascimento', 'obs',]
#         widgets = {
#             'obs': forms.Textarea(attrs={'rows': 1}),
#             'nome': forms.Textarea(attrs={'rows': 1}),
#             # 'tags' : forms.CheckboxSelectMultiple(attrs={'class': 'form_tags'}),
#             }

# ContatoFormSet = forms.inlineformset_factory(
#     Paciente,
#     Contato,
#     exclude = ['paciente'],
#     extra = 0,
#     can_delete = False,
#     widgets = {
#         'obs': forms.Textarea(attrs={'rows': 1}),
#         # 'tipo' : forms.RadioSelect(attrs={'class': 'form_tags'}),
#         },
#     )

# EnderecoFormSet = forms.inlineformset_factory(
#     Paciente,
#     Endereco,
#     exclude = ['paciente'],
#     max_num= 1,
#     can_delete = False,
#     widgets = {
#         'rua': forms.Textarea(attrs={'rows': 1}),
#         },
#     )

# ##########################################################
# # fichas

# def current_year():
#     return datetime.date.today().year

# # def year_choices():
# #     return [(r,r) for r in range(1980, current_year()+1)]

# def proxima_ficha():
#     ultimo = Ficha.objects.filter(data__year=current_year()).order_by('-ordem').first()
#     if ultimo:
#         proximo = ultimo.ordem + 1
#     else:
#         proximo = 1
#     return proximo

# class FichaForm(forms.ModelForm):
#     # ano= forms.TypedChoiceField(choices=year_choices, initial=current_year,required=False)
#     ordem= forms.IntegerField(initial=proxima_ficha,required=False, label='número')
#     class Meta:
#         model = Ficha
#         fields = ['data','ordem']
#         widgets = {}

# ##########################################################
# # orcamentos

# class OrcamentoForm(forms.ModelForm):
#     class Meta:
#         model = Orcamento
#         fields = ['dentista','valor','data',]
#         widgets = {}
#         localized_fields = ['valor',]

# class ValorForm(forms.ModelForm):
#     class Meta:
#         model = Orcamento
#         fields = ['valor',]
#         widgets = {}
#         localized_fields = ['valor',]

# class PagamentoForm(forms.ModelForm):
#     class Meta:
#         model = Pagamento
#         fields = ['tipo','parcelas','valor','data',]
#         widgets = {}
#         localized_fields = ['valor',]













