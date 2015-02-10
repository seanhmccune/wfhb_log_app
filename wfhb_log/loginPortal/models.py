from django.db import models

# Create your models here.

class Person(models.Model):
	email = models.EmailField(max_length=75, primary_key=True)
	name = models.CharField(max_length=200)
	address = models.CharField(max_length=200)
	phone_number = models.CharField(max_length=100)
	
	def __unicode__(self):
		return self.email

class Volunteer(models.Model):
	volunteer = models.ForeignKey(Person, related_name="Volunteer")
	emergency_contact = models.ForeignKey(Person, related_name="Emergency Contact")
	relation_to_contact = models.CharField(max_length=200)
	date_of_birth = models.DateField('Birthday')
	start_date = models.DateField('start date')
	
	def __unicode__(self):
		return self.volunteer.email
		
class Log(models.Model):
	volunteer = models.ForeignKey(Volunteer)
	clock_in = models.DateTimeField('in')
	clock_out = models.DateTimeField('out', default=None)
	total_hours = models.IntegerField(default=0)
	work_type = models.CharField(max_length=50)
	
	def set_total_hours(self):
		pass