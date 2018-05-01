from django.conf import settings
from django.db import models


class Technician(models.Model):
	fullname = models.CharField(
		max_length=100)
		
	address = models.CharField(
		max_length=100)
		
	phone = models.CharField(
		max_length=100)
		
	certificate_photo = models.ImageField(upload_to='images/%m/%d')
	
	user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='technicians',
        on_delete=models.SET_NULL)
	
	datetime_created = models.DateTimeField(
		auto_now_add=True, editable=False)


	class Meta:
		verbose_name_plural = 'technicians'
		
"""	def __unicode__(self)
		return u"%s's Technician Info" %self.user_id"""
		
		
		
		
class Permit(models.Model):
	test = models.CharField()
	
	
	
	
class Inspection(models.Model):
	test = models.CharField()
