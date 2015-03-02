# Create your views here.
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log

user = get_user_model()

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
		login(request, volunteer)
		return HttpResponseRedirect('/login/%s' % volunteer.id)
	else:
		return HttpResponse("bad email and password")

# this is the view that holds the business logic for the clock in and out system
# right now, it prints a simple statement
def clock_in(request, volunteer_id):
	volunteer = Volunteer.objects.get(pk=volunteer_id)
	welcome = "Hello %s, you are at the clock in portal!!!" % volunteer.email
	return render(request, 'loginPortal/clock_in.html', {'welcome' : welcome})
	
def clock_out(request, volunteer_id):
	# should just load that clock-out page, when you hit clock-in
	return render(request, 'loginPortal/clock_out.html', {})
	
def missedpunch(request, volunteer_id):
	# loads missedpunch page
	return render(request, 'loginPortal/missedpunch.html', {})
	
def my_logout(request):
	logout(request)
	return HttpResponseRedirect('/login/')