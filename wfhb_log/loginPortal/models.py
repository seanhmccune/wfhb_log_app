from django.db import models

# Create your models here.

# don't tell me what to do

class Person(models.Model):
	email = models.EmailField(max_length=75, primary_key=True)
	name = models.CharField(max_length=200)
	address = models.CharField(max_length=200)
	phone_number = models.CharField(max_length=100)
	
	def __unicode__(self):
		return self.email

class Volunteer(models.Model):
	# there is an implicit primary key that is declared - its just an integer 
	# so if you look at this table there will be a primary key called 'id' that 
	# will be an integer
	volunteer = models.ForeignKey(Person, unique=True, related_name="Volunteer")
	emergency_contact = models.ForeignKey(Person, related_name="Emergency Contact")
	password = models.CharField(max_length=100)
	relation_to_contact = models.CharField(max_length=200)
	date_of_birth = models.DateField('Birthday')
	start_date = models.DateField('start date')
	
	def __unicode__(self):
		return self.volunteer.email
		
class Log(models.Model):
	# there is an implicit primary key that is declared - its just an integer 
	# so if you look at this table there will be a primary key called 'id' that 
	# will be an integer
	volunteer = models.ForeignKey(Volunteer)
	clock_in = models.DateTimeField('in')
	clock_out = models.DateTimeField('out', default=None, null=True)
	total_hours = models.FloatField(default=0)
	work_type = models.CharField(max_length=50)
	
	def set_total_hours(self):
		if self.clock_out:
			diff = self.clock_out - self.clock_in
			minutes = diff.days * 1440 + diff.seconds // 60
			self.total_hours = float(minutes) / 60
		else:
			print "can't do that yet - you need to clock out"
			