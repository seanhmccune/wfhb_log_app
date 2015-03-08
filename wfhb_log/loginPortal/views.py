# Create your views here.
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log
from django.views.generic.edit import CreateView
from django.utils import timezone

user = get_user_model()

# this is a tiny dictionary that holds all of the work types
work_types = dict()
work_types['Administration'] = 'a'
work_types['News'] = 'n'
work_types['Music'] = 'm'
work_types['Other'] = 'o'


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
			if volunteer.is_staff:
				return HttpResponseRedirect('/login/clock_in')
			else:
				return HttpResponseRedirect('/login/time_stamp')
		else:
			return HttpResponse("You ain't active yets")
	else:
		return HttpResponse("bad email and password")

# this is the view that holds the business logic for the clock in and out system
# right now, it prints a simple statement
def clock_in(request):
	volunteer = request.user
	welcome = "Hello %s, you are at the clock in portal" % volunteer.email
	return render(request, 'loginPortal/clock_in.html', {'welcome' : welcome})
	
def clock_out(request):
	# should just load that clock-out page, when you hit clock-in
	volunteer = request.user
	return render(request, 'loginPortal/clock_out.html', {})

# here are the functions that will deal with the time stamp 
def time_stamp(request):
	volunteer = request.user
	welcome = "Hello %s, you are at the time stamp portal" % volunteer.email
	return render(request, 'loginPortal/time_stamp.html', {'welcome' : welcome})
	
# this is a tiny dictionary that holds all of the work types
def time_stamp_buff(request):
	volunteer = request.user
	work_type = request.POST['work_type']
	total_hours = request.POST['total_hours']
	new_time = volunteer.log_set.create(clock_in = timezone.now(), clock_out = timezone.now(), total_hours = total_hours, work_type = work_types[work_type])
	new_time.save()
	response_string = "Vol-id: '{0}'; work type: '{1}', total hours: '{2}'".format(volunteer.email, work_type, total_hours)
	return HttpResponse(response_string)
	
def missedpunch(request):
	# loads missedpunch page
	return render(request, 'loginPortal/missedpunch.html', {})
	
def my_logout(request):
	logout(request)
	return HttpResponseRedirect('/login/')