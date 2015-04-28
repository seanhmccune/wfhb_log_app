import csv 		# this will help when exporting a csv file from the admin page
from django import forms
from django.http import HttpResponse
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.encoding import smart_str # turns strings into unicode or something like that
from datetime import datetime, timedelta, date
import time

# this is the new user
from loginPortal.models import Volunteer, Log

# this is a function that will be used in the actions drop down menu
# we want to be able to search through all of the in_active users and make them active
# this will be easier for the Big C
def make_active(modeladmin, request, queryset):
	queryset.update(is_active = True)
	
# this will be a command that makes sure that you can export the resulting query to a CSV file
def export_csv_vol(modeladmin, request, queryset):
	# instead of text/html, we render the response as a text/csv file
	response = HttpResponse(mimetype='text/csv')
	response['Content-Disposition'] = 'attachement; filename="volunteer.csv"'
	writer = csv.writer(response, csv.excel)
	
	# this will ensure that the encoding is utf8 so that excel can properly open the file
	response.write(u'\ufeff'.encode('utf8'))
	
	# these are the four fields that will be exported by django (first row)
	writer.writerow([
		smart_str(u"Email"),
		smart_str(u"First Name"),
		smart_str(u"Last name"),
		smart_str(u"Start Date"),
		smart_str(u"Active")
	])
	
	# now we need to write every row that the Big C 
	for obj in queryset:
		s = time.strptime(str(obj.start_date.month) + ' ' + str(obj.start_date.day) + ' ' + str(obj.start_date.year), "%m %d %Y")
		s = time.strftime("%m/%d/%Y", s)
		writer.writerow([
			smart_str(obj.email),
			smart_str(obj.first_name),
			smart_str(obj.last_name),
			smart_str(s),
			smart_str(obj.is_active)
		])
	
	return response
	  
def export_csv_log(modeladmin, request, queryset):
	# instead of text/html, we render the repsonse as a text/csv file
	response = HttpResponse(mimetype='text/csv')
	response['Content-Disposition'] = 'attachement; filename="log.csv"'
	writer = csv.writer(response, csv.excel)
	
	# this will ensure that the encoding is utf8 so that excel can properly open the file
	response.write(u'\ufeff'.encode('utf8'))
	
	# these are the four fields that will be exported by django
	writer.writerow([
		smart_str(u"Email"),
		smart_str(u"Clock-in"),
		smart_str(u"Clock-out"),
		smart_str(u"Total hours"),
		smart_str(u"Work type"),
	])
	
	# go through the result of the query set and put it in the csv file
	for obj in queryset:
		in_4 = obj.clock_in - timedelta(minutes = 240)
		out_4 = obj.clock_out - timedelta(minutes = 240)
		s_in = time.strptime(str(in_4.month) + ' ' + str(in_4.day) + ' ' + str(in_4.year), "%m %d %Y")
		s_in = time.strftime("%m/%d/%Y", s_in)
		s_out = time.strptime(str(out_4.month) + ' ' + str(out_4.day) + ' ' + str(out_4.year), "%m %d %Y")
		s_out = time.strftime("%m/%d/%Y", s_out)
		
		writer.writerow([
			smart_str(obj.volunteer),
			smart_str(s_in),
			smart_str(s_out),
			smart_str(obj.total_hours),
			smart_str(obj.work_type),
		])
		
	return response

# rename this function so it looks nice.
# NOTE: we have the same short description for two distinct functions
export_csv_vol.short_description = u"Export CSV"
export_csv_log.short_description = u"Export CSV"

# this is the new form that will help use create a user
class UserCreationForm(forms.ModelForm):
	# this is a form for creating new users
	
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
	
	class Meta:
		# the model will be the volunteer and there are some required fields
		model = Volunteer
		fields = ('email', 'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', 'start_date',
		'contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact')
		
	# this double checks the password to make sure that they are the same password
	def clean_password2(self):
		# check that the two password entities match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError("Passwords don't match")
		return password2
		
	# this saves a new user to the database
	def save(self, commit=True):
		# Save the provided password in hashed format
		user = super(UserCreationForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user

# this is the form that will help use change some aspects of a currently registered user		
class UserChangeForm(forms.ModelForm):
	# this is a form for updating users 
	
	# this ensures that we store only the hashed value of the password - not the password itself
	password = ReadOnlyPasswordHashField()
	
	class Meta:
		model = Volunteer
		
	def clean_password(self):
		# changes the password
		return self.initial['password'] 
	
# finally this is what we will see when we look at the volunteer section on the admin page	
class VolunteerAdmin(UserAdmin):
	# here are the forms that add and change users
	form = UserChangeForm
	add_form = UserCreationForm
	
	# these are the fields that will be displayed when we are LOOKING at all the users
	list_display = ('email', 'first_name', 'last_name', 'start_date', 'is_active')
		
	# overwriting what is normally displayed by django - this will display when we are trying to CHANGE 
	# some aspect of the user
	fieldsets = (
		(None, {'fields' : ('password', )}), 
		('Personal Info', {'fields' : ('email', 'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', )}),
		('Contact Info', {'fields' : ('contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact', )}),
		('Permissions', {'fields' : ('is_active', 'is_staff', 'is_superuser', )}),
	)
	
	# we use this attribute to CREATE a user
	add_fieldsets = (
		(None, {
			'classes': ('wide', ),
			'fields': ('email', 'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', 'start_date',
		'contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact', 'password1', 'password2'),
		}),
	)
	
	# possible search fields right now
	search_fields = ('email', 'first_name', 'last_name',)
	ordering = ('email', )
	actions = [make_active, export_csv_vol]
	filter_horizontal = ()
	
# this will be the custom admin of the log page
class LogAdmin(admin.ModelAdmin):
	# these two changes will determine what shows up in the logs search
	list_display = ('volunteer', 'clock_in', 'clock_out', 'total_hours', 'work_type')
	search_fields = ('volunteer__email', 'volunteer__first_name', 'volunteer__last_name',)
	
	# we can now filter based on work type and volunteer
	list_filter = ['work_type', 'volunteer__is_staff']
	actions = [export_csv_log]
	
# this helps us register the new user with the admin
admin.site.register(Volunteer, VolunteerAdmin)

# register the Log app
admin.site.register(Log, LogAdmin)

	
