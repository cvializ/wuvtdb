from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wuvtdb.views.home', name='home'),
    # url(r'^wuvtdb/', include('wuvtdb.foo.urls')),


    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),


    (r'^quicktrack/(?P<station>[a-z]+)/$', 'quicktrack2.views.qt'),
    (r'^quicktrack/(?P<station>[a-z]+)/login/$', 'quicktrack2.views.qt_login'),
    (r'^quicktrack/(?P<station>[a-z]+)/stationlog/$', 'quicktrack2.views.qt_stationlog'),
    (r'^quicktrack/(?P<station>[a-z]+)/newshow/$', 'quicktrack2.views.qt_newshow'),
    (r'^quicktrack/(?P<station>[a-z]+)/logout/$', 'quicktrack2.views.qt_logout'),
    (r'^quicktrack/(?P<station>[a-z]+)/show/(?P<showid>[0-9]+)/$', 'quicktrack2.views.qt_showplaylist'),
    # (r'^quicktrack/(?P<station>[a-z]+)/date/(?P<year>d{4})/(?P<month>d{1,2})/(?P<day>d{1,2})/$', 'wuvt_ims.views.qt_listshows'),
    
    (r'^library/$', 'wuvt_ims.views.lib_main'),
    (r'^library/artist/(?P<artist_name>([\w|\W])+)$','wuvt_ims.views.lib_artist'),
    (r'^library/album/(?P<album_title>[\w|\W]+)/artist/(?P<artist_name>([\w|\W])+)$','wuvt_ims.views.lib_album'),
    
    # quicktrack/<studio>/
    # quicktrack/<studio>/show/<pk>
    # quicktrack/<studio>/show/add
    # quicktrack/<studio>/search/
    # quicktrack/<studio>/datetime/ (Playlist for that date)
    # quicktrack/<studio>/reports/songlist/
    # quicktrack/<studio>/reports/cmj/
    # quicktrack/<studio>/reports/chart/
    # quicktrack/<studio>/reports/sublist/
    
    
    
    # database/
    # database/album/pk
    # database/artist/pk
    # database/label/pk
    # database/song/pk
    
    
    #(r'^quicktrack/fm$', 'wuvt_ims.views.quicktrack'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)