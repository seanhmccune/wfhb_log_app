from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

# this is the new user
from loginPortal.models import Volunteer

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
		
class UserChangeForm(forms.ModelForm):
	# this is a form for updating users 
	
	# this ensures that we store only the hashed value of the password - not the password itself
	password = ReadOnlyPasswordHashField()
	
	class Meta:
		model = Volunteer
		
	def clean_password(self):
		# changes the password
		return self.initial['password'] 
		
class VolunteerAdmin(UserAdmin):
	# here are the forms that add and change users
	form = UserChangeForm
	add_form = UserCreationForm
	
	# these are the fields that will be displayed 
	list_display = ('email', 'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', 
		'contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact')
		
	# overwriting what is normally displayed by django
	fieldsets = (
		(None, {'fields' : ('email', 'password', )}), 
		('Personal Info', {'fields' : ('first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', )}),
		('Contact Info', {'fields' : ('contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact', )}),
		('Permissions', {'fields' : ('is_active', 'is_staff', 'is_superuser', )}),
	)
	
	# we use this attribute to create a user
	add_fieldsets = (
		(None, {
			'classes': ('wide', ),
			'fields': ('email', 'first_name', 'last_name', 'address', 'phone_number', 'date_of_birth', 'start_date',
		'contact_first_name', 'contact_last_name', 'contact_phone_number', 'relation_to_contact', 'password1', 'password2'),
		}),
	)
	
	search_fields = ('email', )
	ordering = ('email', )
	filter_horizontal = ()
	
# this helps us register the new user with the admin
admin.site.register(Volunteer, VolunteerAdmin)

# disables the group use because we will never need it
admin.site.unregister(Group)
	
	