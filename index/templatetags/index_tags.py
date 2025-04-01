from django import template
from django.utils import timezone
# from django.urls import reverse, reverse_lazy
# from random import randint, choice
# from django.contrib.humanize.templatetags.humanize import intcomma

# {% load index_tags %}

register = template.Library()

###############################################################################
# tags
###############################################################################

@register.simple_tag
def set(value):
	return value

@register.simple_tag(takes_context=True)
def full_url(context, relative_url):
  request = context['request']
  return request.build_absolute_uri(relative_url)


###############################################################################
# filters
###############################################################################

@register.filter
def get_item(list,i):
	return list[i]

@register.filter
def descendente(p1,p2):
	'verifica se a p1 é descendente da p2'
	
	def ver_descendencia(p1,p2):
		if p2.filhos.all.exists():
			if p1 in p2.filhos.all():
				return True
			else:
				for filho in p2.filhos.all():
					ver_descendencia(p1,filho)
	
	ver_descendencia(p1,p2)			
	return False


@register.filter
def tempo_desde(data):
	agora = timezone.now()
	delta = agora - data
	dias=delta.days
	horas=delta.seconds // 3600
	resto=delta.seconds % 3600
	minutos=resto // 60
	segundos=resto % 60
	
	txt=f'{horas}:{minutos:02}:{segundos:02} horas'
	if dias:
		txt = f'{dias} dia{"s" if dias>1 else ""} e '+txt
	return txt

