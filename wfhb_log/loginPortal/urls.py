# urls.py - loginPortal

# import some stuff we will need from django and our own views pages
from django.conf.urls import patterns, url
from loginPortal import views

urlpatterns = patterns( ' ', 
	# ex /loginPortal/
	url(r'^$', views.my_login, name="login"),
	
	# this is the authentication buffer
	url(r'^auth/', views.auth_buff, name="auth_buff"),
	
	# /login/3 - this is for the clock in page
	url(r'^(?P<volunteer_id>\d+)/$', views.clock_in, name="clock_in"),
	
	# this is the logout buffer, it will bring you back to the login page after loggin a user out
	url(r'^logout/', views.my_logout, name="logout"),
	
	# clockout 
	url(r'^$', views.clock_out, name="clock_out"),
)
