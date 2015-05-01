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
from datetime import datetime, timedelta, date, time
from django.utils.timezone import utc
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils.safestring import mark_safe
from recaptcha.client import captcha  
import random, string

# make sure that the user that we will use in the view corresponds to a volunteer
user = get_user_model()

# the person who will send all of the emails
EMAIL_HOST_USER = 'manager@wfhb.org'

# this is a tiny dictionary that holds all of the work types
work_types = dict()
work_types['Administration'] = 'a'
work_types['News'] = 'n'
work_types['Music'] = 'm'
work_types['Other'] = 'o'

# two quick functions that are boolean checks to see if a user 
# has NONE in the clock out session
def clock_out_check(volunteer):
	return Log.objects.filter(volunteer__email = volunteer.email, clock_out = None) and volunteer.is_staff
	
# this loops through the past logs and determines if a user is trying to clock in or out at a time that they have already worked	
def new_entry_check(volunteer, date):
	past_entries = Log.objects.filter(volunteer__email = volunteer.email)
	
	# if this is the first time they are loggin in
	if not past_entries :
		return True
		
	# loop through the entries and see if this user was already working during that time
	check = True
	for entry in past_entries:
		if not entry.clock_in or not entry.clock_out: 
			break
		if date > entry.clock_in and date < entry.clock_out:
			check = False
			break
			
	return check	
	
# http://stackoverflow.com/questions/16870663/how-do-i-validate-a-date-string-format-in-python
# this checks if an input is a date or not
def validate_date(date_text):
	try:
		return datetime.strptime(date_text, '%Y-%m-%d').date()
	except ValueError:
		return False

# if time_text is a valid string it returns a time, otherwise it returns false
def validate_time(time_text):
	try:
		return datetime.strptime(time_text, "%H:%M").time()
	except ValueError:
		return False

# this checks if an input is a float or not
def validate_float(num):
	try:
		return float(num)
	except ValueError:
		return False

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
def quarterly_hours(volunteer):
	# find the current year,  use that for the lower and upper bound
	current_date = timezone.now().date()
	lower_bound = date(current_date.year, volunteer.start_date.month, volunteer.start_date.day)
	upper_bound = date(current_date.year + 1, volunteer.start_date.month, volunteer.start_date.day)
	
	if lower_bound > current_date:
		upper_bound = lower_bound
		lower_bound = date(current_date.year - 1, volunteer.start_date.month, volunteer.start_date.day)
	
	# find the totaly number of hours that they have worked in the past year
	yearly_hours_raw = Log.objects.filter(volunteer__email = volunteer.email, clock_in__gte = lower_bound, clock_in__lte = upper_bound).aggregate(Sum('total_hours'))
	yearly_hours = yearly_hours_raw['total_hours__sum']
	
	if yearly_hours:
		yearly_hours = round(yearly_hours,2)
	else:
		yearly_hours = 0
	
	check_date = date(current_date.year, volunteer.start_date.month + 3, volunteer.start_date.day)	
	return (yearly_hours, current_date >= check_date) 

# try to snag the last 7 work sessions	
def last_seven_sessions_dates(email):
	last_seven = Log.objects.filter(volunteer__email = email).order_by('-clock_out')[ : 7]
	dates = []
	for entry in last_seven:
		date = entry.clock_in.date()
		dates.append((date, round(entry.total_hours, 2)))
	return dates

# This is a function that emails someone once a user has hit thiry hours for a single session
def email_cleveland(volunteer):
	message = str(volunteer.email) + ' ,' + str(volunteer.first_name) + ' ' + str(volunteer.last_name) + ' has volunteered for at least 30 hours this quarter'
	send_mail(str(volunteer.email) + ' quarterly hours', message, EMAIL_HOST_USER, [EMAIL_HOST_USER])

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
def my_login(request):
	return render(request, 'loginPortal/login.html', {})

# log a user out and return back to the login page
def my_logout(request):
	logout(request)
	return HttpResponseRedirect('/login/')

# this is our authentication buffer, it takes the post from the login page and then just goes to work
# NEED TO CHECK
# if a user is not active - CHECK
# if a user needs to clock out - CHECK
# if a user is staff or not - CHECK
# good email bad password - CHECK
# bad email - CHECK
# if a user treis to acces this without logging in
def auth_buff(request):
	if request.method != 'POST':
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
	
	email = request.POST['email']
	password = request.POST['password']
	volunteer = authenticate(email=email, password=password)
	
	# if the volunteer is in the database
	if volunteer:
		
		#if the volunteer is active 
		if volunteer.is_active: 
			login(request, volunteer)
		
			# if they haven't clocked out and are staff
			if clock_out_check(volunteer):
				return HttpResponseRedirect('/login/clock_out')

			# staff looking to clock in
			elif volunteer.is_staff:
				return HttpResponseRedirect('/login/clock_in')

			# time stamp
			else:
				return HttpResponseRedirect('/login/time_stamp')
	
		# if the volunteer is logged in elsewhere
		else:
			messages.info(request, 'You are not active in the wfhb database')
	
	elif Volunteer.objects.filter(email = email):
		messages.info(request, 'The password you entered is incorrect. Please try again (make sure your caps lock is off).')
		
	# if we can't recognize the email
	else:
		messages.info(request, 'We do not recognize that email address. Please enter a valid email address')
	
	return HttpResponseRedirect('/login/')
		
# this is the view that holds the business logic for the clock in and out system
# NEED TO CHECK
# if a user tries to access this page without logging in - CHECK
def clock_in(request):
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
		
	if not volunteer.is_staff:
		messages.info(request, 'You do not have permission to access this page. You have been logged out.')
		return HttpResponseRedirect('/login/logout/')
			
	# Otherwise, snag all of the times when this volunteer logged in overall and quarterly		
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer)
	last_seven = last_seven_sessions_dates(volunteer.email)
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	return render( request, 'loginPortal/clock_in.html', 
									{'user' : user, 
									  'overall_hours' : total_hours, 
									  'quarterly_hours' : quart_hours[0],
									  'last_seven': last_seven })

# writes to the database after a user has clocked in 
# NEED TO CHECK
# user tries to access this page without logging in - CHECK
# user needs to clock out and tries to clock in - CHECK
# write to database - CHECK
def log_buff(request):
	volunteer = request.user
	
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	# if they stumbled upon this page and they need to clock out, redirect them to the clock out page
	if clock_out_check(volunteer):
		messages.info(request, 'You need to clock out before you clock-in. Also, you have been logged out')
		return HttpResponseRedirect('/login/logout')

	clock_in = timezone.now()
	clock_in_date = clock_in.date()
	work_type = 'a'	
	L = volunteer.log_set.create(clock_in = clock_in, work_type = work_type)
	L.save()
	return HttpResponseRedirect('/login/clock_out')
	
# this is used to clock users out	
# user tries to access this page without logging in - CHECK
# user needs to clock out and tries to clock in - CHECK
# write to database - CHECK
def clock_out(request):
	# should just load that clock-out page, when you hit clock-in
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
		
	if not volunteer.is_staff:
		messages.info(request, 'You do not have permission to access this page. You have been logged out.')
		return HttpResponseRedirect('/login/logout/')
	
	# Otherwise, snag all of the times when this volunteer logged in overall and quarterly		
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer)
	last_seven = last_seven_sessions_dates(volunteer.email)
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	return render(request, 'loginPortal/clock_out.html', {'user' : user, 
		 													 'overall_hours' : total_hours, 
														  	 'quarterly_hours' : quart_hours[0],
															 'last_seven': last_seven})
			
# this is the buffer that helps users clock out
# if a user tries to access this page without logging in - CHECK	
def out_buff(request):
	volunteer = request.user
	
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
	
	# if the volunteer is staff
	vol_bool = volunteer.is_staff
	
	# if they stumbled upon this page and they need to clock in, redirect them to the clock in page
	if not clock_out_check(volunteer):
		messages.info(request, 'You need to clock in before you clock out. Also, you have been logged out.')
		return HttpResponseRedirect('/login/logout')

	# check the quarterly hours for this volunteer
	quart_hours = quarterly_hours(volunteer)

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
# if a user tries to access this page without logging in - CHECK
def time_stamp(request):
	# get the volunteer info
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
		
	if volunteer.is_staff:
		messages.info(request, 'You do not have permission to access this page. You have been logged out.')
		return HttpResponseRedirect('/login/logout/')
	
	user = volunteer.email
	# find their total hours
	user = volunteer.email
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer)
	last_seven = last_seven_sessions_dates(volunteer.email)
	
	welcome = "Hello %s, you are at the time stamp portal" % volunteer.email
	return render(request, 'loginPortal/time_stamp.html', 
								{	'user' : user, 
									'overall_hours' : total_hours, 
									'quarterly_hours' : quart_hours[0],
									'last_seven' : last_seven})
	
# this is the time stamp buffer that holds all of the logic behind the time stamp system
# if a user tries to acces this page without logging in - CHECK
# if the date is past the current date - CHECK
# if the date is before 2015 - CHECK 
# if the total hours variable is greater than 24 - CHECK 
# if the date is invalid - CHECK
# if the time is invalid - CHECK
# write the date a midnight to the database - CHECK
def time_stamp_buff(request):
	# get some information off of the page
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
	
	work_type = request.POST['work_type']
	total_hours = request.POST['total_hours']
	date = request.POST['date']
	global_date = timezone.now().date()
	
	# check to see if inputs are valid
	d = validate_date(date)
	num = validate_float(total_hours)
	
	# if the date is not valid
	if d and num:
		# if the input date is a day that has yet to happen
		if num < 0:
			messages.info(request, "Please enter a positive integer")
		
		elif d > global_date:
			messages.info(request, "You cannot enter in a date that has not happened yet")
	
		# if they tried to clock in before the apps existence 
		elif d.year < 2015:
			messages.info(request, "You cannot enter in a date before 2015")
		
		# if they tried to clock in more than 24 hours
		elif num > 24:
			messages.info(request, "You cannot log in for more than 24 hours at a time")
		
		# so you can save to the database
		else:
			# hack around the timezone issues that I don't wanna deal with right now
			date_time = datetime(d.year, d.month, d.day, 0, 0, 0)
			new_time = volunteer.log_set.create(clock_in = date_time.replace(tzinfo=utc), clock_out = date_time.replace(tzinfo=utc), total_hours = total_hours, work_type = work_types[work_type])
			
			# check the quarterly hours for this volunteer, if they have just gone past 30 hours for this
			# quarter send cleveland an email
			quart_hours = quarterly_hours(volunteer)
			if quart_hours[0] < 30 and quart_hours[0] + num >= 30 and quart_hours[1]:
				email_cleveland(volunteer)
			
			new_time.save()
			messages.success(request, "You successfully entered clocked in at %s for %d hours" % (d, num))
	
	elif not d:
		messages.info(request, 'Please enter a valid date')
	
	# if the input number is not a number
	elif not num:
		messages.info(request, "You must enter in a valid number for the total hours section")

	# return to the time stamp page
	return HttpResponseRedirect('/login/time_stamp')

# NEED TO CHECK
# can they go to this page if they haven't logged in? NOPE	
def missedpunch(request):
	volunteer = request.user
	
	# if they tried to access this page without loggin in first - redirect them to the login page
	if volunteer.is_anonymous():
		messages.info(request, 'You have not logged in yet')
		return HttpResponseRedirect('/login/')
	
	if not volunteer.is_staff:
		messages.info(request, 'You do not have permission to access this page. You have been logged out.')
		return HttpResponseRedirect('/login/logout/')
	
	# loads missedpunch page
	total_hours = overall_hours(volunteer.email)
	quart_hours = quarterly_hours(volunteer)
	last_seven = last_seven_sessions_dates(volunteer.email)
	
	# if they stumbled upon this page and they need to clock out, redirect them to the clock out page
	if not volunteer.is_staff:
		messages.info(request, 'This page is not for you')
		return HttpResponseRedirect('/login/')
		
	return render(request, 'loginPortal/missedpunch.html', {'user' : volunteer.email, 'overall_hours' : total_hours, 'quarterly_hours' : quart_hours[0], 'last_seven' : last_seven})
	
# this is tries to write to the database
# NEED TO CHECK
# invalid date - CHECK 
# invalid time - CHECK
# enter in a date/time after the current day - CHECK
# if they try to clock in when they need to clock out - CHECK
# if they try to clock out at a time before their last clock in - CHECK
# if they try to clock out at a time that is more than 24 hours after their last clock in - CHECK
# if they try to clock out when they need to clock in - CHECK
# if they try to enter a time in which they have already worked - CHECK 
def missrequest(request):
	volunteer = request.user
	user = volunteer.email
	switch = request.POST['sex']
	date = request.POST['datepick']
	in_or_out = request.POST.get('misstable') 
	work_type = 'a'
	today = timezone.now()
	check_out_bool = clock_out_check(volunteer)
	
	#military time conversion
	btn = None	
	if switch == "female":	
		btn = 12
	
	#grabs civilianTime from input on missedpunch page and checks to see if it is valid
	civilian_time = request.POST['missedpunch']	
	
	#tries to convert the date to a string 
	d = validate_date(date)
	
	# tries to convert the time to a string
	t = validate_time(civilian_time)

	# if we have a valid time and date do all of this stuff
	if d and t:
		
		# so now that both of the inputs are valid, we need to convert to military time and combine the 
		# date and time
		final_time_copy = datetime.combine(d, t).replace(tzinfo=utc) 
		final_time = final_time_copy + timedelta(minutes = 240)
		
		if btn and t.hour < 12:
			final_time = final_time + timedelta(minutes=720)
		
		# if the input date is a day that has yet to happen
		if final_time > today:
			messages.info(request, "You cannot enter in a date and/or time that has not happened yet")
	
		# if they tried to clock in before this apps existence 
		elif final_time.date().year < 2015:
			messages.info(request, "You cannot enter in a date before 2015")
	
		# if they are trying to say they missed a punch during a shift they already worked
		elif not new_entry_check(volunteer, final_time):
			messages.info(request, "You already worked at that time")
	
		# bad time
		elif t.hour > 12:
			messages.info(request, "Make sure your hours are between 1 and 12")
			
		# bad minute
		elif t.minute > 60:
			messages.info(request, "Make sure your minutes are between 0 and 60")
			
		#if the user has selected clock_in do this
		elif in_or_out == 'clock_in':
			# if they can log in - do this, otherwise they need to clock out 
			if not check_out_bool:
				# the database is in UTC so we have to offset the final_time
				L = volunteer.log_set.create(clock_in = final_time, work_type = work_type)
				L.save()
				messages.success(request, 'You just clocked in at %s %s <br /> <a href="/login/clock_out">HOME</a>' % (str(final_time_copy)[:19], 'PM' if btn else 'AM'),extra_tags='safe')
			else: 
				messages.info(request, 'You need to clock out first')
		
		#if the user has selected clock_out do this	
		else:
			if check_out_bool:
				L = Log.objects.get(volunteer__email = volunteer.email, clock_out = None)
				# if the date entered is before the time that they clocked in
				if final_time < L.clock_in:
					messages.info(request, 'Please enter a date after your last login %s' % L.clock_in)
				
				# if they try to enter in a clock out date that is more than a day 
				elif (final_time - L.clock_in).total_seconds() > 86400:
					messages.info(request, 'You cannot enter in a date that is more than a day from your last clock in %s' % L.clock_in)
				else:
					L.clock_out = final_time
					diff = final_time - L.clock_in
					hours = diff.days * 24 + float(diff.seconds) / 3600
					L.total_hours = hours
					
					# check the quarterly hours for this volunteer, if they have just gone past 30 hours for 
					# this quarter, send cleveland an email
					quart_hours = quarterly_hours(volunteer)
					if quart_hours[0] < 30 and quart_hours[0] + hours >= 30 and quart_hours[1]:
						email_cleveland(volunteer)
					messages.success(request, 'You just clocked out at %s %s <br /> <a href="/login/clock_out">HOME</a>' % (str(final_time_copy)[:19], 'PM' if btn else 'AM'), extra_tags='safe' )
					# save that stuff
					L.save()
	
			else:
				messages.info(request, 'You need to clock in first')
	
	# if the date is not valid
	elif not d:
		messages.info(request, 'Please enter a valid date')
		
	# if the time is not valid
	else:
		messages.info(request, 'Please enter a valid time')
	
	# return to ths missed punch page
	return HttpResponseRedirect('/login/missedpunch')
		
# render the page that will send them an email to reset their password
def new_password(request):
	return render(request, 'loginPortal/new_password.html', {})

# this will send an email to a user with the desired code
# it will throw back an error if it is
# NEED TO CHECK
# sends email - CHECK
# won't let you send two emails to yourself, if you haven't changed your password - CHECK
# sends back an error for a bad email - CHECK
def new_password_buff(request):
	# snag their email 
	email = request.POST['email']
	
	# if they are in the database, then send them an email, otherwise throw an error
	volunteer = None
	if Volunteer.objects.filter(email = email):
		volunteer = Volunteer.objects.get(email = email)

	if volunteer:
		# generate a random string of 20 digits / uppercase letters - save it to the code table
		code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
		if Code.objects.filter(volunteer__email = email):
			messages.info(request, "We already have a password reset code in the database - check your email")
		else:	
			EMAIL_CONTENT = 'To change your password, please put this link in your url: (we will figure out a link later - for now, just go to your time.wfhb.org/login/setpassword).'
			EMAIL_CONTENT += ' Once you are there please enter in your email and this code: '
			EMAIL_CONTENT += code
		
			# try to send them an email
			if volunteer.email_user("Password reset", EMAIL_CONTENT):
				C = volunteer.code_set.create(code = code)
				C.save()
				messages.info(request, "We have just sent you an email with some information about reseting your password")
			else: 
				message.info(request, "We had trouble sending you an email - Please try again")
	
	# if we don't recognize their email address
	else:
		messages.info(request, 'We do not recognize that email address. Please enter a valid email address')

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

# make sure all of their information goes to the database - redirect them if the any errors arrise	
# NEED TO CHECK
# bad email - CHECK
# bad code - CHECK
# cant enter in same code twice - CHECK
def set_password_buff(request):
	# snag these values from the form on the previous page
	email = request.POST['email']
	code = request.POST['code']
	password = request.POST['password']
	password2 = request.POST['password2']
	
	# check to see if they are a volunteer and if they are in the code database
	code_bool = Code.objects.filter(volunteer__email = email, code = code)
	
	# if they are in the database, then send them an email, otherwise throw an error
	volunteer = None
	if Volunteer.objects.filter(email = email):
		volunteer = Volunteer.objects.get(email = email)

	# if there is a code in the database
	if password != password2:
		messages.info(request, "These passwords do not match")
	elif code_bool:
		# reset their password, save the change, then remove that line from the database
		volunteer.set_password(password)
		volunteer.save()
		code_bool = Code.objects.get(volunteer__email = email, code = code)
		code_bool.delete()
		messages.info(request, "Your password has successfully been reset")
		return HttpResponseRedirect('/login/')
	elif volunteer:
		messages.info(request, 'You entered a valid email address, but the code was incorrect. Please try again!')
	else:
		messages.info(request, 'We do not recognize that email or you may have not requested a password reset')
		
	
	return HttpResponseRedirect('/login/setpassword/')

# Below is a 403 handler
def handler403(request):
	response = render(request, 'loginPortal/403.html', {})
	response.status_code = 403
	return response
