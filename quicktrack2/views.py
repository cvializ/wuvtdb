from django import forms
from django.forms import ModelForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from datetime import datetime

from quicktrack2.models import *
from wuvt_ims.models import *

# Handles URL:  /quicktrack/<station>/
def qt(request, station):
    # First, figure out what station is being asked for.
    try:
        st = Station.objects.get(name=station)
    except Station.DoesNotExist:
        return
    
    # Now, we see if there is an operator on right now.  This is determined by whether
    # the last entry for given station has a NULL End Time or not.
    # If there is an operator, redirect to /quicktrack/station/stationlog
    # If there is not an operator, redirect to /quicktrack/station/login
    
    try:
        op = OperatorLog.objects.filter(station=st).latest('time_on')
        off = op.time_off
    except OperatorLog.DoesNotExist:
        off = "never"
    
    # There is no current operator.  We should create a page to let the user log in.
    if off is None:
        # There is an operator, because current ops have a time_off of None
        # We should take the user to the station log page.
        return HttpResponseRedirect('/quicktrack/' + station + '/stationlog/') # Redirect after POST
    else:
        # There is no operator (i.e., the time off is some time in the past)
        # Let the user log in as a new operator.
        return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST

def qt_login(request, station):
    class LoginForm(forms.Form):
        show = forms.ModelChoiceField(
            queryset=Show.objects.filter(station__name = station),
            empty_label = None)

    try:
        st = Station.objects.get(name = station)
    except Station.DoesNotExist:
        return
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid(): # All validation rules pass
            op = OperatorLog()
            op.show = form.cleaned_data['show']
            op.station = st
            op.time_on = datetime.now()
            op.save()

            return HttpResponseRedirect('/quicktrack/' + station + '/') # Redirect after POST
    else:
        form = LoginForm()
        return render_to_response('show_login.html', {'form': form,},
            context_instance=RequestContext(request))
    
    #else
    # That operator is currently on air.  We should take them to the QT Entry Page.
    # After a user submits a login form, we should retrieve the current operator field
    # and render the playlist for that operator.  From now on, just track the current operator
    # until they log out!
        

def qt_logout(request, station):
    try:
        st = Station.objects.get(name = station)
    except Station.DoesNotExist:
        return
    
    try:
        op = OperatorLog.objects.filter(station=st).latest('time_on')
    except OperatorLog.DoesNotExist:
        return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST
        
    op.time_off = datetime.now()
    op.save()
    return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST
        

# This view handles the generation of a new show.
def qt_newshow(request, station):
    class ShowForm(ModelForm):
        class Meta:
            model = Show

    if request.method == 'POST': # If the form has been submitted...
        form = ShowForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            form.save()

            return HttpResponseRedirect('/quicktrack/' +
                                        form.cleaned_data['station'].name +
                                        '/') # Redirect after POST
    else:
        form = ShowForm() # An unbound form

    return render_to_response('showform.html', {'form': form,}, context_instance=RequestContext(request))
    
def qt_stationlog(request, station):
    class TrackForm(forms.Form):
        song = forms.CharField()
        tracknumber = forms.IntegerField()
        artist = forms.CharField()
        album = forms.CharField()
        label = forms.CharField()
        req = forms.BooleanField(required = False)
        vin = forms.BooleanField(required = False)
        

    # First, figure out what station is being asked for.
    try:
        st = Station.objects.get(name=station)
    except Station.DoesNotExist:
        return
    
    # Now, we see if there is an operator on right now.  This is determined by whether
    # the last entry for given station has a NULL End Time or not.
    # If there is an operator, redirect to /quicktrack/station/stationlog
    # If there is not an operator, redirect to /quicktrack/station/login
    
    try:
        op = OperatorLog.objects.filter(station=st).latest('time_on')
    except OperatorLog.DoesNotExist:
        return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST
        
    
    tracks = StationLog.objects.filter(operator = op).order_by('-timestamp')
    
    if request.method == 'POST':
        form = TrackForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            try:
                label = Label.objects.get(name = form.cleaned_data['label'])
            except Label.DoesNotExist:
                label = Label(
                    name = form.cleaned_data['label'] )
                label.save()
                    
            try:
                artist = Artist.objects.get(name = form.cleaned_data['artist'])
            except Artist.DoesNotExist:
                artist = Artist(
                    name = form.cleaned_data['artist'] )
                artist.save()
            
            try:
                album = Album.objects.get(name = form.cleaned_data['album'])
                
            except Album.DoesNotExist:
            
                try:
                    sta = Stack.objects.get(name = 'Not WUVT Property')
                except Stack.DoesNotExist:
                    sta = Stack(
                        name = 'Not WUVT Property' )
                    sta.save()
                    
                album = Album(
                    name = form.cleaned_data['album'],
                    label = label,
                    artist = artist,
                    stack = sta,
                    num_discs = 1,
                    missing = False,
                    visible = True,
                    compilation = False,
                    needs_librarian_review = False,
                )
            
            try:
                so = Song.objects.get(name = form.cleaned_data['song'], album = album)
            except Song.DoesNotExist:
                so = Song(
                    name = form.cleaned_data['song'],
                    album = album,
                    track_num = form.cleaned_data['tracknumber'],
                )
                so.save()
                
            rec = StationLog(
                operator = op,
                timestamp = datetime.now(),
                song = so,
                request = form.cleaned_data['req'],
                vinyl = form.cleaned_data['vin'],
                visible_public = True,
            )
            rec.save()
            form = TrackForm()
    else:
        form = TrackForm() # An unbound form

    return render_to_response('stationlog.html', {
        'form': form,
        'tracks': tracks,
        'station': station,
        'operator': op,
        }, context_instance=RequestContext(request))

# Handles URL of /quicktrack/<station>/show/<id>
def qt_showplaylist(request, station, showid):

    # First, figure out what station is being asked for.
    try:
        st = Station.objects.get(name=station)
    except Station.DoesNotExist:
        return

    # Next, pull the operator record by the show id passed.
    try:
        op = OperatorLog.objects.get(pk = showid)
    except OperatorLog.DoesNotExist:
        return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST

    try:
        tracks = StationLog.objects.filter(operator = op).order_by('timestamp')
    except StationLog.DoesNotExist:
        return
        
    return render_to_response('stationlog.html', {
        'tracks': tracks,
        'station': station,
        'operator': op,
        }, context_instance=RequestContext(request))
    
# Handles URL of /quicktrack/<station>/show/<id>
#def qt_listshows(request, station, year, month, day):
#
#    # First, figure out what station is being asked for.
#    try:
#        st = Station.objects.get(name=station)
#    except Station.DoesNotExist:
#        return
#
#    # Next, pull the operator record by the show id passed.
#    try:
#        op = OperatorLog.objects.filter(sign_on.year = year).filter(sign_on.month = month).filter(sign_on.day = day)
#    except OperatorLog.DoesNotExist:
#        return HttpResponseRedirect('/quicktrack/' + station + '/login/') # Redirect after POST
#
#    try:
#        tracks = StationLog.objects.filter(operator = op).order_by('timestamp')
#    except StationLog.DoesNotExist:
#        return
#        
#    return render_to_response('stationlog.html', {
#        'tracks': tracks,
#        'station': station,
#        'operator': op,
#        }, context_instance=RequestContext(request))
