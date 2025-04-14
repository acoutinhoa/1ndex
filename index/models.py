import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.urls import reverse
from django.utils.text import slugify
from datetime import datetime

Pronome = models.TextChoices("Pronome", "ELA ELE NENHUM QUALQUER_UM")

class Link(models.Model):
    nome = models.CharField(max_length=39)
    url = models.URLField()

    def __str__(self):
        return str(self.nome)

class Base(models.Model):
    d0 = models.DateTimeField(auto_now_add=True)
    d1 = models.DateTimeField(auto_now=True)
    nome = models.CharField(max_length=119, validators=[MinLengthValidator(2),])
    info = models.CharField(max_length=912, blank=True, null=True, verbose_name='descrição')
    links = models.ManyToManyField(Link)

    def __str__(self):
        return str(self.nome)

    class Meta:
        abstract = True
        ordering = ['-d1']

class User(AbstractUser, Base):
    # edita fields do djando
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=91, validators=[UnicodeUsernameValidator(),], unique=True, verbose_name='codinome',)
    email = models.EmailField(unique=True)
    
    # adiciona novos fields
    u0 = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='filhos')
    nome = models.CharField(max_length=119, blank=True, null=True)
    pronome = models.CharField(choices=Pronome, max_length=13, default='NENHUM')

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

    def get_absolute_url(self):
        return reverse('index:perfil', kwargs={'url': self.url})

    def __str__(self):
        return str(self.username)


class Grupo(Base):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    u0 = models.ManyToManyField(User, related_name='grupos') # adicionar o user aos u0 quando o grupo for criada
    publico = models.BooleanField(default=False, verbose_name='grupo público')

    def define_url(self, n=0):
        slug = slug0 = slugify(self.nome)
        while Url.objects.filter(nome=slug).exists():
            n += 1
            slug = f"{slug0}-{n}"
        return slug

    def mudar_visibilidade(self):
        self.publico = not self.publico
        self.save()

    def save(self, *args, **kwargs):
        novo = self._state.adding
        super().save(*args, **kwargs)
        
        if novo:
            Url.objects.create(grupo=self, nome=self.define_url(), ) # define url do grupo

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

    def get_absolute_url(self):
        return reverse('index:perfil', kwargs={'url': self.nome})


class Convite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    u0 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='convites')
    d0 = models.DateTimeField(auto_now_add=True)
    pronome = models.CharField(choices=Pronome, max_length=13, default='NENHUM')
    nome = models.CharField(max_length=119, validators=[MinLengthValidator(2),])
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return str(self.nome)

    class Meta:
        ordering = ['-d0']

    def get_absolute_url(self):
        return reverse('index:convite', kwargs={'pk': self.pk})

class Tag(models.Model):
    nome = models.CharField(max_length=39)
    publico = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nome)

    class Meta:
        ordering = ['nome']


def projeto_imagepath(instance, filename):
    return 'index/{0}/{1}'.format(instance.pk, filename)

class Projeto(Base):
    u0 = models.ForeignKey(User, on_delete=models.CASCADE) # >>>>>>>>>>>>> definir o on_delete
    texto = models.TextField(blank=True, null=True)
    publico = models.BooleanField(default=False)
    perfil = models.ForeignKey(Url, on_delete=models.CASCADE, related_name='projetos')
    tags = models.ManyToManyField(Tag, related_name='projetos')
    ano = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)], default=datetime.today().year)
    url = models.SlugField(max_length=119)
    Etapa = models.IntegerChoices("Etapa", "RASCUNHO DESENVOLVIMENTO FINALIZADO")
    etapa = models.IntegerField(choices=Etapa, default=3)
    links = models.ManyToManyField(Link)
    # imagem = models.ImageField(upload_to=projeto_imagepath, max_length=100, blank=True, null=True,)
    # -equipe [m2m] [user] > [trabalho] (X criador) ‘projetos’
    # -ordem [] ()
    # -tempo total [gen] (X)

    def define_url(self, n=0):
        slug = slug0 = slugify(self.nome)
        while Projeto.objects.filter(perfil=self.perfil, url=slug).exists():
            n += 1
            slug = f"{slug0}-{n}"
        return slug

    def mudar_visibilidade(self):
        self.publico = not self.publico
        self.save()

    def save(self, *args, **kwargs):
        if self._state.adding: 
            self.url = self.define_url() # define url ao criar o projeto
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('index:projeto', kwargs={'url': self.perfil, 'purl':self.url})


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

