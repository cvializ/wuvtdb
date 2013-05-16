from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^library/$', 'wuvt_ims.views.lib_main'),
    (r'^library/artist/(?P<artist_name>([\w|\W])+)$','wuvt_ims.views.lib_artist'),
    (r'^library/album/(?P<album_title>[\w|\W]+)/artist/(?P<artist_name>([\w|\W])+)$','wuvt_ims.views.lib_album'),
 
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)