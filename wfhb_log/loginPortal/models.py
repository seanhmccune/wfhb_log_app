from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Create your models here.

# don't tell me what to do

# this is a table that stores all of the emergency contact information
class Contact(model.models):
	contact_first_name = models.CharField(max_length=25)
	contact_last_name = models.CharField(max_length=25)
	contact_phone_number = models.CharField(max_length=100)
	relation_to_contact = models.CharField(max_length=200)

# this class helps us create new Volunteers and 'superusers' that is, people who have
# access to the admin page
class VolunteerManager(BaseUserManager):
	
	# this is the function that creates the a new user
	def _create_user(email, password=None, fn, ln, address, pn, cfn, cln, cpn, rtc, dob, is_staff, is_superuser):
		now  = timezone.now()
		
		# create a new contact
		new_contact = Contact(cfn, cln, cpn, rtc)
		
		# check if they passed an email
		if not email:
			raise ValueError('The given email is not good')
		email = self.normalize_email(email)
		
		# create the user
		user = self.model(
			email = email,
			first_name = fn,
			last_name = ln,
			address = address,
			phone_number = pn,
			date_of_birth = dob,
			start_date = now,
			e_contact = new_contact,
			is_active = False,
			is_staff = is_staff,
			is_superuser = is_superuser
		)
		
		# save the contact and the user 
		new_contact.save(using=self._db)
		user.set_password(password)
		user.save(using=self._db)
		return user

	# creates a normal user, a 'volunteer' if I may
	def create_user(self, email, password=None, fn, ln, address, pn, cfn, cln, cpn, rtc, dob):
		return self._create_user(email, password, fn, ln, address, pn, cfn, cln, cpn, rtc, dob, False, False)
	
	# creates a super user, someone who is an admin
	def create_super_user(self, email, password, fn, ln, address, pn, cfn, cln, cpn, rtc, dob):
		return self._create_user(email, password, fn, ln, address, pn, cfn, cln, cpn, rtc, dob, True, True)


# this allows use to define a new user based on the volunteer class 
# this means that we can also create an authentication process that
# uses our Volunteer objects
class Volunteer(AbstractBaseUser, PermissionsMixin):
	# there is an implicit primary key that is declared - its just an integer 
	# so if you look at this table there will be a primary key called 'id' that 
	# will be an integer
	email = models.EmailField(max_length=75, primary_key=True)
	first_name = models.CharField(max_length=25)
	last_name = models.CharField(max_length=25)
	address = models.CharField(max_length=200)
	phone_number = models.CharField(max_length=100)
	date_of_birth = models.DateField('Birthday')
	start_date = models.DateField('start date')
	contact = models.ForeignKey(Contact, relation="Emergency Contact")
	is_active = models.BooleanField(default=False)
	
	# make sure that the username field points to the email address
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name', 'address', 'phone_number', 'date_of_birth']
	
	objects = VolunteerManager()
	
	def get_full_name(self):
		return self.email
		
	def get_short_name(self):
		return self.email
		
	def email_user(self, subject, message, from_email=None):
		send_mail(subject, message, from_email, [self.email])
	
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
			