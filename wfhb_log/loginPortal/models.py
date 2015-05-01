from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django import forms
from functools import partial
from captcha.fields import CaptchaField

# this is the email that we will use to send emails
EMAIL_HOST_USER = 'manager@wfhb.org'

# Create your models here.

# this class helps us create new Volunteers and 'superusers' that is, people who have
# access to the admin page
class VolunteerManager(BaseUserManager):

	# creates a normal user, a 'volunteer' if I say
	def create_user(self, email, first_name, last_name, address, phone_number, date_of_birth, contact_first_name, contact_last_name, contact_phone_number, relation_to_contact, password):
		now  = timezone.now()
		
		# check if they passed an email
		if not email:
			raise ValueError('The given email is not good')
		email = self.normalize_email(email)
		
		# create the user
		user = self.model(
			email = email,
			first_name = first_name,
			last_name = last_name,
			address = address,
			phone_number = phone_number,
			date_of_birth = date_of_birth,
			start_date = now,
			contact_first_name = contact_first_name,
			contact_last_name = contact_last_name,
			contact_phone_number = contact_phone_number,
			relation_to_contact = relation_to_contact,
			is_active = False,
			is_staff = False,
			is_superuser = False
		)
		
		# save the user
		user.set_password(password)
		user.save(using=self._db)
		return user
		
	# creates a super user, someone who is an admin
	def create_superuser(self, email, first_name, last_name, address, phone_number, date_of_birth, contact_first_name, contact_last_name, contact_phone_number, relation_to_contact, password):
		now  = timezone.now()
		
		# check if they passed an email
		if not email:
			raise ValueError('The given email is not good')
		email = self.normalize_email(email)
		
		# create the user
		user = self.model(
			email = email,
			first_name = first_name,
			last_name = last_name,
			address = address,
			phone_number = phone_number,
			date_of_birth = date_of_birth,
			start_date = now,
			contact_first_name = contact_first_name,
			contact_last_name = contact_last_name,
			contact_phone_number = contact_phone_number,
			relation_to_contact = relation_to_contact,
			is_active = True,
			is_staff = True,
			is_superuser = True
		)
		
		# save the new user
		user.set_password(password)
		user.save(using=self._db)
		return user

# this allows use to define a new user based on the volunteer class 
# this means that we can also create an authentication process that
# uses our Volunteer objects
class Volunteer(AbstractBaseUser, PermissionsMixin):
	# there is an implicit primary key that is declared - its just an integer 
	# so if you look at this table there will be a primary key called 'id' that 
	# will be an integer. However, email is still unique and will be used for authentication
	email = models.EmailField(max_length=75, unique=True, db_index=True)
	first_name = models.CharField(max_length=25)
	last_name = models.CharField(max_length=25)
	address = models.CharField(max_length=200)
	phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
	phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=15)
	date_of_birth = models.DateField('Birthday')
	start_date = models.DateField('start date')
	contact_first_name = models.CharField(max_length=25)
	contact_last_name = models.CharField(max_length=25)
	contact_phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=15)
	relation_to_contact = models.CharField(max_length=200)
	is_active = models.BooleanField(default=False)
	is_staff = models.BooleanField(default = False)
	
	# make sure that the username field points to the email address
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = [
		'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', 
		'contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact']
	
	objects = VolunteerManager()
	
	def get_full_name(self):
		return self.first_name + " " + self.last_name
		
	def get_short_name(self):
		return self.email
		
	def email_user(self, subject, message):
		return send_mail(subject, message, EMAIL_HOST_USER, [self.email])
	
	def __unicode__(self):
		return self.email
		
# these are the four choices from which a worker can select when clocking in
WORK_CHOICES = (
	('a', 'Administration'),
	('n', 'News'),
	('m', 'Music'),
	('o', 'Other'),
)
		
class Log(models.Model):
	# there is an implicit primary key that is declared - its just an integer 
	# so if you look at this table there will be a primary key called 'id' that 
	# will be an integer
	volunteer = models.ForeignKey(Volunteer)
	clock_in = models.DateTimeField('in')
	clock_out = models.DateTimeField('out', default=None, null=True)
	total_hours = models.FloatField(default=0)
	work_type = models.CharField(max_length=1, choices=WORK_CHOICES)
	
	def __unicode__(self):
		return "clock-in: " + str(self.clock_in)[ :16] + " clock-out: " + str(self.clock_out)[ :16] + " total hours: " + str(round(self.total_hours,2))

# This is a database table that will hold a temporary code and volunteer. This will ensure that only a user with the right code can change their password
class Code(models.Model):
	volunteer = models.ForeignKey(Volunteer)
	code = models.CharField(max_length = 20)
	
	def __unicode__(self):
		return "email " + str(self.volunteer.email) + " code: " + str(self.code)

cDateInput = partial(forms.DateInput, {'class': 'datepicker'})
class RegiForm(forms.Form):
	
	DateInput = partial(forms.DateInput, {'class': 'datepicker'})
	email = forms.EmailField(max_length=75)
	first_name = forms.CharField(max_length=25)
	last_name = forms.CharField(max_length=25)
	address = forms.CharField(max_length=200)
	phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
	phone_number = forms.CharField(validators=[phone_regex], max_length=15)
	date_of_birth = forms.DateField(widget=DateInput())
	start_date = forms.DateField(widget=DateInput())
	contact_first_name = forms.CharField(max_length=25)
	contact_last_name = forms.CharField(max_length=25)
	contact_phone_number = forms.CharField(validators=[phone_regex], max_length=15)
	relation_to_contact = forms.CharField(max_length=200)
	password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    	password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput)
    	captcha = CaptchaField()
	#password confirmation   	
    	def clean_password2(self):
        	password = self.cleaned_data.get('password')
        	password2 = self.cleaned_data.get('password2')
        	if password and password2:
            		if password != password2:
                		raise forms.ValidationError(_("Passwords didn't match."))
        		return password
