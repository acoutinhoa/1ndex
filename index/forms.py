from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
import datetime

# user info edit
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nome','info',]
        widgets = { 
            'info': forms.Textarea(attrs={'rows': 9}),
            }

# grupo info edit
class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nome','info']
        widgets = { 
            'info': forms.Textarea(attrs={'rows': 9}),
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
        fields = ['email',]

# cadastro
class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',]

# reativar
class ReativarForm(forms.Form):
    username = forms.CharField(label='codinome')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)



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













