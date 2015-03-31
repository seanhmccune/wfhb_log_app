# Create your views here.
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from loginPortal.models import Volunteer, Log , RegiForm, VolunteerManager, Code
from django.views.generic.edit import CreateView
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta, date
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
		if global_now >= start and global_now <= end:
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
def my_login(request, flag = "0"):
	# we will be writing a message to the screen depending on what needs to be displayed
	message = ''
	
	#if a user is not active
	if flag == "1":
		message = 'You are not yet active in the WFHB database'
	
	# if the user entered a valid email, but a bad password
	elif flag == "2":
		message = 'You entered a valid email address, but the password was incorrect. Please try again!'
	
	# if we cannot recognize the email	
	elif flag == "3":
		message = 'We do not recognize that email address. Please enter a valid email address'
	
	# if we have successfully sent them an email for reseting their password	
	elif flag == "4":
		message = "We have just sent you an email with some information about reseting your password"
		
	# if we couldn't send them an email	
	elif flag == "5":
		message = "We had trouble sending you an email - Please try again"
		
	# if we have successfully reset their password	
	elif flag == "6":
		message = "Your password has successfully been reset"
	
	# if we already have a password reset for the user	
	elif flag == "7":
		message = "We already have a password reset code in the database"
			
	return render(request, 'loginPortal/login.html', { 'message' : message })

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
		
		#if the volunteer is active 
		if volunteer.is_active:
			login(request, volunteer)

			# if the volunteer is staff
			vol_bool = volunteer.is_staff
			
			# if they haven't clocked out and are staff
			if Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and vol_bool:
				return HttpResponseRedirect('/login/clock_out')
			
			# staff looking to clock in
			elif vol_bool:
				return HttpResponseRedirect('/login/clock_in')
			
			# time stamp
			else:
				return HttpResponseRedirect('/login/time_stamp')
		# if the volunteer is not active
		else:
			return HttpResponseRedirect('/login/%s' % '1')
	
	# if the entered a valid email, but the password was bad 
	elif Volunteer.objects.filter(email = email):
		return HttpResponseRedirect('/login/%s' % '2')
	
	# if we can't recognize the email
	else:
		return HttpResponseRedirect('/login/%s' % '3')	
		
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
	if Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and vol_bool:
		return HttpResponseRedirect('/login/clock_out')
	else:
		return render(request, 'loginPortal/clock_in.html', {	'user' : user, 
																'overall_hours' : total_hours, 
																'quarterly_hours' : quart_hours,
																'last_seven': last_seven })
	
# writes to the database after a user has clocked in 
def log_buff(request):
	volunteer = request.user
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
	if not Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and vol_bool:
		return HttpResponseRedirect('/login/clock_in')
	else:
		return render(request, 'loginPortal/clock_out.html',{'user' : user, 
																'overall_hours' : total_hours, 
																'quarterly_hours' : quart_hours,
																'last_seven' : last_seven })
		
# this is the buffer that helps users clock out	
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
	return render(request, 'loginPortal/time_stamp.html', {	'user' : user, 
																'overall_hours' : total_hours, 
																'quarterly_hours' : quart_hours,
																'last_seven' : last_seven })
	
# this is a tiny dictionary that holds all of the work types
def time_stamp_buff(request):
	# get some information off of the page
	volunteer = request.user
	work_type = request.POST['work_type']
	total_hours = request.POST['total_hours']
	date = request.POST['date']
	new_time = volunteer.log_set.create(clock_in = date, clock_out = date, total_hours = total_hours, work_type = work_types[work_type])
	new_time.save()
	return HttpResponseRedirect('/login/time_stamp')
	
# render the missed punch page
def missedpunch(request):
	# loads missedpunch page
	return render(request, 'loginPortal/missedpunch.html', {})
		
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
		if Code.objects.get(volunteer__email = email, code = code):
			return HttpResponseRedirect('/login/%s' % "7")
		C = volunteer.code_set.create(code = code)
		C.save()
		EMAIL_CONTENT = 'To change your password, please put this link in your url: (we will figure out a link later - for now, just go to your 127.0.0.1:8000/login/setpassword). '
		EMAIL_CONTENT += 'Once you are there please enter in your email and this code: '
		EMAIL_CONTENT += code
		
		# try to send them an email
		if volunteer.email_user("Password reset", EMAIL_CONTENT):
			return HttpResponseRedirect('/login/%s' % "4")
		else: 
			return HttpResponseRedirect('/login/%s' % "5")
	
	# if we don't recognize their email address
	else:
		return HttpResponseRedirect('/login/%s' % "3")

# just return the page prompting the user to enter an email and the code that was emailed to them		
def set_password(request):
	return render(request, 'loginPortal/set_password.html', {})
	
def set_password_buff(request):
	# snag these values from the form on the previous page
	email = request.POST['email']
	code = request.POST['code']
	password = request.POST['password']
	
	# check to see if they are a volunteer and if they are in the code database
	code_bool = Code.objects.get(volunteer__email = email, code = code)
	volunteer = Volunteer.objects.get(email__exact = email)

	# if there is a code in the database
	if code_bool:
		# reset their password, save the change, then remove that line from the database
		volunteer.set_password(password)
		volunteer.save()
		code_bool.delete()
		return HttpResponseRedirect('/login/%s' % "6")
	else:
		return HttpResponseRedirect('/login/%s' % "2")

