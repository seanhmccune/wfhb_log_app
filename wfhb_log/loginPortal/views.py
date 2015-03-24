# Create your views here.
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log , RegiForm, VolunteerManager
from django.views.generic.edit import CreateView
from django.utils import timezone
from django.db.models import Sum
import datetime

user = get_user_model()

# this is a tiny dictionary that holds all of the work types
work_types = dict()
work_types['Administration'] = 'a'
work_types['News'] = 'n'
work_types['Music'] = 'm'
work_types['Other'] = 'o'

# this will help us figure out the total quarterly hours on the views
global_now = timezone.now()
global_year = global_now.year
date_list = ( 
	datetime.date(global_year, 1, 1), 
	datetime.date(global_year, 4, 1), 
	datetime.date(global_year, 7, 1), 
	datetime.date(global_year, 10, 1)
)

def overall_hours(email):
	# snag all of the hours that they have worked so far
	overall_hours_raw = Log.objects.filter(volunteer__email = email).aggregate(Sum('total_hours'))
	overall_hours = overall_hours_raw['total_hours__sum']
	if overall_hours:
		overall_hours = round(overall_hours, 2)
	else:
		overall_hours = 0
		
	return overall_hours
	
def quarterly_hours(email):
	# cycle through the dates to see where to start and end
	for i in range(0, len(date_list)):
		start = date_list( i )
		end = date_list( i + 1 % 4 )
		# if we found the right two times break out of the loop
		if global_now >= start and global_now <= end:
			break
	
	# snag the hours for just this quarter
	quarterly_hours_raw = Log.objects.filter(volunteer__email = email, clock_in >= start, clock_in <= end).aggregate(Sum('total_hours'))
	quarterly_hours = quarterly_hours_raw['total_hours__sum']
	if quarterly_hours:
		quarterly_hours = round(quarterly_hours, 2)
	else:
		quarterly_hours = 0
		
	return quarterly_hours
	  

# this is a buffer view that will eventually become the authentication portal
def my_login(request):
	# just go to this page - it will go to an authentications view when pressed enter
	return render(request, 'loginPortal/login.html', {})

#this is a registration form
def regi(request):
	if request.method == 'POST':
		form = RegiForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			first_name = form.cleaned_data['first_name']
			last_name = form.cleaned_data['last_name']
			address = form.cleaned_data['address']
			phone_number = form.cleaned_data['phone_number']
			date_of_birth = form.cleaned_data['date_of_birth']
			#date_of_birth = datetime.date.today()
			#start_date = datetime.date.today()
			start_date = form.cleaned_data['start_date']
			contact_first_name = form.cleaned_data['contact_first_name']
			contact_last_name = form.cleaned_data['contact_last_name']
			contact_phone_number = form.cleaned_data['contact_phone_number']
			relation_to_contact = form.cleaned_data['relation_to_contact']
			password = form.cleaned_data['password']
			Volunteer.objects.create_user(email, first_name, last_name, address, phone_number, date_of_birth, contact_first_name, contact_last_name, contact_phone_number, relation_to_contact, password)
  
			return HttpResponse('/Thanks/')
	else:
		form = RegiForm()
	return render(request, 'loginPortal/regiform.html',{'form' : form})
	
# this is our authentication buffer, it takes the post from the login page and then just goes to work
def auth_buff(request):
	email = request.POST['email']
	password = request.POST['password']
	volunteer = authenticate(email=email, password=password)
	
	if volunteer:
		if volunteer.is_active:
			login(request, volunteer)

			# we probably don't need this, but just in case
			vol_bool = volunteer.is_staff
			
			# if they haven't clocked out and are staff
			if Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and vol_bool:
				return HttpResponseRedirect('/login/clock_out')
			
			#staff looking to clock in
			elif vol_bool:
			
				return HttpResponseRedirect('/login/clock_in')
			
			# time stamp
			else:
				return HttpResponseRedirect('/login/time_stamp')
		
		else:
			return HttpResponse("You'ze ain't active yets")
	else:
		return HttpResponse("bad email and password")

# this is the view that holds the business logic for the clock in and out system
def clock_in(request):
	volunteer = request.user
	user = volunteer.email
	# snag all of the times when this volunteer logged in overall and quarterly
	total_hours = overall_hours(volunteer.email)
	quarterly_hours = quarterly_hours(volunteer.email)
	
	return render(request, 'loginPortal/clock_out.html', {'user' : user, 'overall_hours' : total_hours, 'quarterly_hours' : quarterly_hours})
	
def log_buff(request):
	volunteer = request.user
	clock_in = timezone.now()
	work_type = 'a'	
	#if request.method == 'POST':
	L = volunteer.log_set.create(clock_in = clock_in, work_type = work_type)
	L.save()
	return HttpResponseRedirect('/login/clock_out')
	
def clock_out(request):
	# should just load that clock-out page, when you hit clock-in
	volunteer = request.user
	user = volunteer.email
	# snag all of the times when this volunteer logged in overall and quarterly
	total_hours = overall_hours(volunteer.email)
	quarterly_hours = quarterly_hours(volunteer.email)
	
	return render(request, 'loginPortal/clock_out.html', {'user' : user, 'overall_hours' : total_hours, 'quarterly_hours' : quarterly_hours})
	
def out_buff(request):
	volunteer = request.user
	# now we will do some fancy conversion to change days and seconds into hours
	now = timezone.now()
	L = Log.objects.get(volunteer__email = volunteer.email, clock_out = None)
	L.clock_out = now
	diff = now - L.clock_in
	hours = diff.days * 24 + float(diff.seconds) / 3600
	L.total_hours = hours
	
	# save that stuff
	L.save()
	return HttpResponseRedirect('/login/clock_in')

# here are the functions that will deal with the time stamp 
def time_stamp(request):
	volunteer = request.user
	user = volunteer.email
	welcome = "Hello %s, you are at the time stamp portal" % volunteer.email
	return render(request, 'loginPortal/time_stamp.html', {'user' : user})
	
# this is a tiny dictionary that holds all of the work types
def time_stamp_buff(request):
	volunteer = request.user
	work_type = request.POST['work_type']
	total_hours = request.POST['total_hours']
	date = request.POST['date']
	new_time = volunteer.log_set.create(clock_in = date, clock_out = date, total_hours = total_hours, work_type = work_types[work_type])
	new_time.save()
	return HttpResponseRedirect('/login/time_stamp')
	
def missedpunch(request):
	# loads missedpunch page
	return render(request, 'loginPortal/missedpunch.html', {})
	
def my_logout(request):
	logout(request)
	return HttpResponseRedirect('/login/')
