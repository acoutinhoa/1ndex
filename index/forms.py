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
class TextoForm(forms.ModelForm):
    class Meta:
        model = Texto
        fields = ['texto']
        widgets = { 
            'texto': forms.Textarea(attrs={'rows': 19, }),
            }

# projetos texto titulo
class TituloForm(forms.ModelForm):
    class Meta:
        model = Texto
        fields = ['titulo', 'superior', 'ordem' ]
        widgets = { 
            'titulo': forms.Textarea(attrs={'rows': 1, 'placeholder': 'título', }),
            'ordem': forms.Select(choices=[(0,'último')]+[(i, i) for i in range(1, 11)]),
            }
        
    def __init__(self, *args, **kwargs):
        projeto = kwargs.pop('projeto', None)
        pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)
        if pk:
            self.fields['superior'].queryset = Texto.objects.filter(projeto=projeto).exclude(pk=pk)
        else:
            self.fields['superior'].queryset = Texto.objects.filter(projeto=projeto)
        # self.fields['ordem'].choices = [(i,i) for i in range(1, Texto.objects.filter(projeto=projeto).count() + 1)]

# # projetos texto add
# class TextoForm(forms.ModelForm):
#     class Meta:
#         model = Texto
#         fields = ['superior', 'titulo', 'texto']
#         widgets = { 
#             'titulo': forms.Textarea(attrs={'rows': 2, }),
#             'texto': forms.Textarea(attrs={'rows': 19, }),
#             }

# projeto imagens
ImagensFormSet = forms.inlineformset_factory(
    Projeto,
    Imagem,
    fields = ["nome", "capa", "carrossel"],
    can_delete = False,
    extra = 0,
    widgets = { 
        'nome': forms.TextInput(attrs={'placeholder': 'nova imagem', }),
    },
   # can_order = True,
)

# projeto nova imagem
class ImagemForm(forms.ModelForm):
    class Meta:
        model = Imagem
        fields = ["imagem",]
        widgets = { 
            'imagem': forms.FileInput(attrs={'placeholder': 'selecione uma imagem',}),
        }
        
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













