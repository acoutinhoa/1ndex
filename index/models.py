import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.urls import reverse
from django.utils.text import slugify
# from django.template.defaultfilters import slugify


class User(AbstractUser):
    # edita fields do djando
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=91, validators=[UnicodeUsernameValidator(),], unique=True, verbose_name='codinome',)
    email = models.EmailField(unique=True)
    
    # adiciona novos fields
    u0 = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='filhos')
    d0 = models.DateTimeField(auto_now_add=True)
    d1 = models.DateTimeField(auto_now=True)
    nome = models.CharField(max_length=119, blank=True, null=True)
    info = models.CharField(max_length=912, blank=True, null=True)

    def grupos_publicos(self):
        return self.grupos.filter(publico=True)

    def clean(self):
        super().clean()
        if Url.objects.filter(nome=self.username).exclude(user=self).exists():
            raise ValidationError("Este codinome não está disponível.")

    def save(self, *args, **kwargs):
        novo = self._state.adding
        if novo:
            self.full_clean()  # verifica se a Url existe
        super().save(*args, **kwargs)       
        if novo:
            Url.objects.create(user=self, nome=self.username, ) # define url do user

    class Meta:
        ordering = ['-d1']

    def get_absolute_url(self):
        return reverse('index:perfil', kwargs={'url': self.url})


class Base(models.Model):
    u0 = models.ForeignKey(User, on_delete=models.CASCADE) # >>>>>>>>>>>>> definir o on_delete
    d0 = models.DateTimeField(auto_now_add=True)
    d1 = models.DateTimeField(auto_now=True)
    nome = models.CharField(max_length=119, validators=[MinLengthValidator(2),])
    info = models.CharField(max_length=912, blank=True, null=True)

    def __str__(self):
        return str(self.nome)

    class Meta:
        abstract = True
        ordering = ['-d1']


class Grupo(Base):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    u0 = models.ManyToManyField(User, related_name='grupos') # adicionar o user aos u0 quando o grupo for criada
    publico = models.BooleanField(default=False, verbose_name='grupo público')

    def mudar_visibilidade(self):
        self.publico = not self.publico
        self.save()

    def save(self, *args, **kwargs):
        novo = self._state.adding
        super().save(*args, **kwargs)
        
        if novo:
            Url.objects.create(grupo=self, nome=self.id, ) # define url do user

    def get_absolute_url(self):
        return reverse('index:perfil', kwargs={'url': self.url})

            
class Url(models.Model):
    nome = models.CharField(max_length=91, validators=[UnicodeUsernameValidator()], unique=True, verbose_name='codinome')
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True,)
    grupo = models.OneToOneField(Grupo, on_delete=models.CASCADE, blank=True, null=True,)
    sistema = models.BooleanField(default=False)

    def __str__(self):
        return str(self.nome)

    class Meta:
        ordering = ['id']


class Convite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    u0 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='convites')
    d0 = models.DateTimeField(auto_now_add=True)
    nome = models.CharField(max_length=119, validators=[MinLengthValidator(2),])
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return str(self.nome)

    class Meta:
        ordering = ['-d0']

    def get_absolute_url(self):
        return reverse('index:convite', kwargs={'pk': self.pk})


##############################################

# class Projeto(Base):
#     entidade = models.ForeignKey(Entidade,on_delete=models.CASCADE, related_name='projetos')
#     ano = models.PositiveSmallIntegerField(
#         blank=True, 
#         null=True, 
#         validators=[MinValueValidator(1900), MaxValueValidator(2100)],
#     )
#     # equipe = models.ManyToManyField(
#     #     Pessoa, 
#     #     through="Participacao",
#     #     through_fields=("projeto", "pessoa"),
#     #     related_name='projetos',
#     # )
#     info = models.TextField(blank=True, null=True)

#     class Meta:
#         ordering = ['-ano', '-d0', 'nome']

# # class Portfolio(models.Model):
# #     entidade = models.ForeignKey(Entidade, on_delete=models.CASCADE)
# #     projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
# #     ordem = models.PositiveIntegerField()

# #     class Meta:
# #         ordering = ['ordem']


# # class Funcao(Base):
# #     nome = models.CharField(max_length=192, unique=True)

# #     def save(self, *args, **kwargs):
# #         self.nome = self.nome.lower()
# #         super().save(*args, **kwargs)


# # class Participacao(models.Model):
# #     projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
# #     pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE)
# #     funcao = models.ManyToManyField(Funcao)

