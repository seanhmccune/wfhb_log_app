# urls.py - loginPortal

# import some stuff we will need from django and our own views pages
from django.conf.urls import patterns, url
from loginPortal import views

urlpatterns = patterns( ' ', 
	# ex /loginPortal/
	url(r'^$', views.login, name="login"),
	
	# this is the authentication buffer
	url(r'^auth/', views.auth_buff, name="auth_buff"),
	
	# /loginPortal/3 - this is for the clock in page
	url(r'^(?P<volunteer_id>\d+)/$', views.clock_in, name="clock_in"),
)
