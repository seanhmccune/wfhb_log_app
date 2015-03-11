# Create your views here.
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log
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
date_list = ( 
	datetime.date(global_now.year, 1, 1), 
	datetime.date(global_now.year, 4, 1), 
	datetime.date(global_now.year, 7, 1), 
	datetime.date(global_now.year, 10, 1)
)

# this is a buffer view that will eventually become the authentication portal
def my_login(request):
	# just go to this page - it will go to an authentications view when pressed enter
	return render(request, 'loginPortal/login.html', {})
	
# this is our authentication buffer, it takes the post from the login page and then just goes to work
def auth_buff(request):
	email = request.POST['email']
	password = request.POST['password']
	volunteer = authenticate(email=email, password=password)
	
	if volunteer:
		if volunteer.is_active:
			login(request, volunteer)
			# SEAN PUT CODE HERE VVVVVVVV
			if volunteer.is_staff:
				return HttpResponseRedirect('/login/clock_in')
			else:
				return HttpResponseRedirect('/login/time_stamp')
			# CODE GOES HERE ^^^^^^^^^^^^^
		else:
			return HttpResponse("You'ze ain't active yets")
	else:
		return HttpResponse("bad email and password")

# this is the view that holds the business logic for the clock in and out system
# right now, it prints a simple statement
def clock_in(request):
	volunteer = request.user
	user = volunteer.email
	# snag all of the times when this volunteer logged in
	overall_hours_raw = Log.objects.filter(volunteer__email = volunteer.email).aggregate(Sum('total_hours'))
	overall_hours = int(overall_hours_raw['total_hours__sum'])
	
	print global_now.year
	return render(request, 'loginPortal/clock_in.html', {'user' : user, 'overall_hours' : overall_hours})
	
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
	# snag all of the times when this volunteer logged in
	overall_hours_raw = Log.objects.filter(volunteer__email = volunteer.email).aggregate(Sum('total_hours'))
	overall_hours = int(overall_hours_raw['total_hours__sum'])
	return render(request, 'loginPortal/clock_out.html', {'user' : user, 'overall_hours' : overall_hours})
	
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