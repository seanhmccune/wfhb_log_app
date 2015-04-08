# Create your views here.
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log , RegiForm, VolunteerManager, Code
from django.views.generic.edit import CreateView
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import requires_csrf_token, ensure_csrf_cookie
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta, date
from django.utils.timezone import utc
from django.contrib import messages
import random, string

user = get_user_model()

# this is a tiny dictionary that holds all of the work types
work_types = dict()
work_types['Administration'] = 'a'
work_types['News'] = 'n'
work_types['Music'] = 'm'
work_types['Other'] = 'o'

# this will help us figure out the total quarterly hours on the views
global_now = datetime.today().date()
global_year = global_now.year
date_list = [ 
	date(global_year, 1, 1), 
	date(global_year, 4, 1), 
	date(global_year, 7, 1), 
	date(global_year, 10, 1)
]

# two quick functions that are boolean checks to see if a user 
# has NONE in the clock out session
def clock_out_check(volunteer):
	return Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and volunteer.is_staff()

# see how many hours someone worked since they've started
def overall_hours(email):
	# snag all of the hours that they have worked so far
	overall_hours_raw = Log.objects.filter(volunteer__email = email).aggregate(Sum('total_hours'))
	overall_hours = overall_hours_raw['total_hours__sum']
	if overall_hours:
		overall_hours = round(overall_hours, 2)
	else:
		overall_hours = 0
		
	return overall_hours
	
# just check the last quarterly hours
def quarterly_hours(email):
	# cycle through the dates to see where to start and end
	for i in range(0, len(date_list)):
		start = date_list[ i ]
		end = date_list[ i + 1 % 4 ]
		# if we found the right two times break out of the loop
		if global_now >= start and global_now < end:
			# if you are looking at the last quarter, we need to update the end date by 1 year
			if i == len(date_list):
				end = end + datetime.timedelta(years = 1)
			break
	
	# snag the hours for just this quarter
	quarterly_hours_raw = Log.objects.filter(volunteer__email = email, clock_in__gte = start, clock_in__lte = end).aggregate(Sum('total_hours'))
	quarterly_hours = quarterly_hours_raw['total_hours__sum']
	if quarterly_hours:
		quarterly_hours = round(quarterly_hours, 2)
	else:
		quarterly_hours = 0
		
	return quarterly_hours

# try to snag the last 5 work sessions	
def last_seven_sessions(email):
	# snag every possible entry from the Log table and sort them based on clock - out time and get the
	# first 7
	last_seven_sessions = Log.objects.filter(volunteer__email = email).order_by('-clock_out')[ : 7]
	return last_seven_sessions

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
  
			return HttpResponseRedirect('/login/')
	else:
		form = RegiForm()
	return render(request, 'loginPortal/regiform.html', {'form' : form})
		  
# this is a buffer view that will eventually become the authentication portal

# we will be writing a message to the screen depending on what needs to be displayed
def my_login(request):
	return render(request, 'loginPortal/login.html', { 'messages' : messages })

# log a user out and return back to the login page
def my_logout(request):
	logout(request)
	return HttpResponseRedirect('/login/')

# this is our authentication buffer, it takes the post from the login page and then just goes to work
def auth_buff(request):
	email = request.POST['email']
	password = request.POST['password']
	volunteer = authenticate(email=email, password=password)
	
	# if the volunteer is in the database
	if volunteer:

		# check if they have logged into a previous session
		users_bool = volunteer in get_all_logged_in_users()
		
		# if the volunteer is staff
		vol_bool = volunteer.is_staff
		
		#if the volunteer is active 
		if volunteer.is_active: 
			login(request, volunteer)
		
			# if they haven't clocked out and are staff
			if clock_out_check(volunteer):
				return HttpResponseRedirect('/login/clock_out')

			# staff looking to clock in
			elif vol_bool:
				return HttpResponseRedirect('/login/clock_in')

			# time stamp
			else:
				return HttpResponseRedirect('/login/time_stamp')
	
		# if the volunteer is logged in elsewhere
		else:
			messages.info(request, 'You are not active in the wfhb database')
	
	elif Volunteer.objects.filter(email = email):
		messages.info(request, 'You entered a valid email address, but the password was incorrect. Please try again!')
		
	# if we can't recognize the email
	else:
		messages.info(request, 'We do not recognize that email address. Please enter a valid email address')
	
	return HttpResponseRedirect('/login/')
		
# this is the view that holds the business logic for the clock in and out system
def clock_in(request):
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		return HttpResponseRedirect('/login/')
			
	# Otherwise, snag all of the times when this volunteer logged in overall and quarterly		
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer.email)
	last_seven = last_seven_sessions(volunteer.email)
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	# if they stumbled upon this page and they need to clock out, redirect them to the clock out page
	if clock_out_check(volunteer):
		return HttpResponseRedirect('/login/clock_out')
	else:
		return render( request, 'loginPortal/clock_in.html', 
										{'user' : user, 
										  'overall_hours' : total_hours, 
										  'quarterly_hours' : quart_hours,
										  'last_seven': last_seven })
	
# writes to the database after a user has clocked in 
def log_buff(request):
	volunteer = request.user
	global message
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	# if they stumbled upon this page and they need to clock out, redirect them to the clock out page
	if clock_out_check(volunteer):
		message = 'You need to clock out before you clock-in'
		return HttpResponseRedirect('/login/')

	clock_in = timezone.now() 
	work_type = 'a'	
	L = volunteer.log_set.create(clock_in = clock_in, work_type = work_type)
	L.save()
	return HttpResponseRedirect('/login/clock_out')
	
# this is used to clock users out	
def clock_out(request):
	# should just load that clock-out page, when you hit clock-in
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		return HttpResponseRedirect('/login/')
	
	# Otherwise, snag all of the times when this volunteer logged in overall and quarterly		
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer.email)
	last_seven = last_seven_sessions(volunteer.email)
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	# if they stumbled upon this page and they need to clock in, redirect them to the clock in page
	if not clock_out_check(volunteer):
		return HttpResponseRedirect('/login/clock_in')
	else:
		return render(request, 'loginPortal/clock_out.html', {'user' : user, 
		 														  	'overall_hours' : total_hours, 
																  	'quarterly_hours' : quart_hours,
																  	'last_seven': last_seven})
			
# this is the buffer that helps users clock out	
def out_buff(request):
	volunteer = request.user
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	global message
	# if they stumbled upon this page and they need to clock in, redirect them to the clock in page
	if not clock_out_check(volunteer):
		message = 'You need to clock in before you clock out'
		return HttpResponseRedirect('/login/')

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
time_error = ''
def time_stamp(request):
	# get the volunteer info
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		return HttpResponseRedirect('/login/')
	
	user = volunteer.email
	# find their total hours
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer.email)
	last_seven = last_seven_sessions(volunteer.email)
	welcome = "Hello %s, you are at the time stamp portal" % volunteer.email
	global time_error
	return render(request, 'loginPortal/time_stamp.html', 
								{	'user' : user, 
									'overall_hours' : total_hours, 
									'quarterly_hours' : quart_hours,
									'last_seven' : last_seven,
									'time_error' : time_error })
	
# this is a tiny dictionary that holds all of the work types
def time_stamp_buff(request):
	# get some information off of the page
	volunteer = request.user
	work_type = request.POST['work_type']
	total_hours = request.POST['total_hours']
	date = request.POST['date']
	
	# change the unicode date to a date
	d = datetime.strptime(date, "%Y-%m-%d").date()
	
	# snag today's date
	global global_now
	global time_error
	
	# do some error checks
	if d > global_now:
		time_error = "You cannot enter in a date that has not happened yet"
	elif d.year < 2015:
		time_error = "You cannot enter in a date before 2015"
	elif not isinstance(total_hours, float):
		time_error = "You must enter in a valid number for the total hours section"
	elif total_hours > 24:
		time_error = "You cannot volunteer more than 24 hours"
	else:
		time_error = ''
		new_time = volunteer.log_set.create(clock_in = date, clock_out = date, total_hours = total_hours, work_type = work_types[work_type])
		new_time.save()

	return HttpResponseRedirect('/login/time_stamp')
	
def missedpunch(request):
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		return HttpResponseRedirect('/login/')
	
	# loads missedpunch page
	user = volunteer.email
	overall_hours_raw = Log.objects.filter(volunteer__email = volunteer.email).aggregate(Sum('total_hours'))
	overall_hours = overall_hours_raw['total_hours__sum']
	
	if overall_hours:
		overall_hours = int(overall_hours)
	else:
		overall_hours = 0
	# if they stumbled upon this page and they need to clock out, redirect them to the clock out page
	if not volunteer.is_staff():
		message = 'This page is not for you'
		return HttpResponseRedirect('/login/')
		
	return render(request, 'loginPortal/missedpunch.html', {'user' : user, 'overall_hours' : overall_hours})
		
def missrequest(request):
	volunteer = request.user
	user = volunteer.email
	switch = request.POST['sex']
	date = request.POST['datepick']
	work_type = 'a'	
	overall_hours_raw = Log.objects.filter(volunteer__email = volunteer.email).aggregate(Sum('total_hours'))
	overall_hours = overall_hours_raw['total_hours__sum']
	
	if overall_hours:
		overall_hours = int(overall_hours)
	else:
		overall_hours = 0
	
	#military time conversion	
	if switch == "female":	
		time = 12
	else:
		time = 0
	
	#grabs civilianTime from input on missedpunch page
	civilianTime = request.POST['missedpunch']	
	
	#converts civilianTime into military time
	now = str(int(civilianTime[:2]) + time) + civilianTime[2:]
	
	#grabs the date and time strings and converts them to datetime
	d = datetime.strptime(date, "%Y-%m-%d").date()
	t = datetime.strptime(now, "%H:%M").time()
	
	#combines date and time into datetime field
	finalTime = datetime.combine(d, t).replace(tzinfo=utc)
	
	#if the user has selected clock_in do this
	if request.POST.get('misstable') == 'clock_in':
		L = volunteer.log_set.create(clock_in = finalTime, work_type = work_type)
		L.save()

	#if the user has selected clock_out do this	
	else:
		L = Log.objects.get(volunteer__email = volunteer.email, clock_out = None)
		L.clock_out = finalTime
		diff = finalTime - L.clock_in
		hours = diff.days * 24 + float(diff.seconds) / 3600
		L.total_hours = hours
		# save that stuff
		L.save()
	
	return HttpResponseRedirect('/login/missedpunch')
		
# this is a buffer that will be used to send an email to a user when they want a new password
def new_password(request):
	return render(request, 'loginPortal/new_password.html', {})

def new_password_buff(request):
	# snag their email 
	email = request.POST['email']
	
	# if they are in the database, then send them an email
	volunteer = Volunteer.objects.get(email = email)

	if volunteer:
		# generate a random string of 20 digits / uppercase letters - save it to the code table
		code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
		if Code.objects.filter(volunteer__email = email):
			global message
			message = "We already have a password reset code in the database"
		else:	
			EMAIL_CONTENT = 'To change your password, please put this link in your url: (we will figure out a link later - for now, just go to your 127.0.0.1:8000/login/setpassword).'
			EMAIL_CONTENT += 'Once you are there please enter in your email and this code: '
			EMAIL_CONTENT += code
		
			# try to send them an email
			if volunteer.email_user("Password reset", EMAIL_CONTENT):
				C = volunteer.code_set.create(code = code)
				C.save()
				global message
				message = "We have just sent you an email with some information about reseting your password"
			else: 
				global message
				message = "We had trouble sending you an email - Please try again"
	
	# if we don't recognize their email address
	else:
		global message
		message = 'We do not recognize that email address. Please enter a valid email address'

	return HttpResponseRedirect('/login/')

'''
So here's the steps we should take to be able to change your password
1) enter in an email address
2) check if that email address is in our system. If so, send them an email with a code and link to the generate new password page
(see step three for a continuation). If not, tell them we don't recognize that email and tell them to try again.
3) Take the code and put that in a list with their email. So now we have a set of tuples (code, email) in a database, where you can only 
reset your password with the appropraite code
4) Make them log in with their code and email
5) reset their password, then wipe that table from the database 
'''

# just return the page prompting the user to enter an email and the code that was emailed to them		
def set_password(request):
	return render(request, 'loginPortal/set_password.html', {})
	
def set_password_buff(request):
	# snag these values from the form on the previous page
	email = request.POST['email']
	code = request.POST['code']
	password = request.POST['password']
	
	# check to see if they are a volunteer and if they are in the code database
	code_bool = Code.objects.filter(volunteer__email = email, code = code)
	volunteer = Volunteer.objects.get(email__exact = email)
	global message

	# if there is a code in the database
	if code_bool:
		# reset their password, save the change, then remove that line from the database
		volunteer.set_password(password)
		volunteer.save()
		code_bool = Code.objects.get(volunteer__email = email, code = code)
		code_bool.delete()
		global message
		message = "Your password has successfully been reset"
	else:
		message = 'You entered a valid email address, but the password was incorrect. Please try again!'
	
	return HttpResponseRedirect('/login/')

# below are some error handlers
def error403(request):
	HttpResponse("hello")