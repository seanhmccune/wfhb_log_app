# urls.py - loginPortal

# import some stuff we will need from django and our own views pages
from django.conf.urls import patterns, url
from loginPortal import views

urlpatterns = patterns( ' ', 
	# ex /login/ - below it is when we pass in an extra argument (when the user cannot login and is redirected)
	url(r'^$', views.my_login, name="login"),
	url(r'^(\d{1})/$', views.my_login, name ="login"),

	# this is the form
	url(r'^regi/$', views.regi, name="regi"),
	
	# this is the authentication buffer
	url(r'^auth/$', views.auth_buff, name="auth_buff"),
	
	# /login/3 - this is for the clock in page
	url(r'^clock_in/$', views.clock_in, name="clock_in"),
	
	url(r'^log/$', views.log_buff, name="log_buff"),
	
	#clock-out
	url(r'^clock_out/$', views.clock_out, name="clock_out"),
	
	url(r'^out/$', views.out_buff, name="out_buff"),
	
	#missedpunch
	url(r'^missedpunch/$', views.missedpunch, name="missedpunch"),
	
	#new_password
	url(r'^newpassword/$', views.new_password, name="newpassword"),
	
	url(r'^newpasswordbuff/$', views.new_password_buff, name="newpasswordbuff"),
	
	# time_stamp - this page is for volunteers who need to record their hours
	# NOTE: this is not the clock-in / clock-out page. They just enter total hours worked
	url(r'^time_stamp/$', views.time_stamp, name="time_stamp"),
	
	# this is the buffer for the time stamp that will write to the database to figure shit out
	url(r'^time_stamp_buff/$', views.time_stamp_buff, name="time_stamp_buff"),
	
	# this is the logout buffer, it will bring you back to the login page after loggin a user out
	url(r'^logout/$', views.my_logout, name="logout"),
	
)
