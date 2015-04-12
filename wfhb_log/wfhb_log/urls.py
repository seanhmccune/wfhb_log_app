# urls.py - wfhb_log_app

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

handler403 = 'loginPortal.views.handler403'
urlpatterns = patterns('',
	# Examples:
	# url(r'^$', 'wfhb_log.views.home', name='home'),
	# url(r'^wfhb_log/', include('wfhb_log.foo.urls')),

	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	url(r'^admin/', include(admin.site.urls)),
	
	# this is where we put our loginPortal app
	url(r'^login/', include('loginPortal.urls')),
)
