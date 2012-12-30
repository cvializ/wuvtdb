from django import forms
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime

from wuvt_ims.models import *
from wuvt_ims.api import PyLastFm,AllMusic,LyricsWiki

def lib_main(request):
    class SearchForm(forms.Form):
        song = forms.CharField(required = False)
        artist = forms.CharField(required = False)
        album = forms.CharField(required = False)
        label = forms.CharField(required = False)
        year = forms.CharField(required = False)
        genre = forms.CharField(required = False)
        stack = forms.CharField(required = False)
        sortby = forms.ChoiceField(choices = [('artist','Artist'),
                                              ('album','Album'),
                                              ('label','Label'),
                                              ('genre','Genre'),
                                              ('stack', 'Stack')],
                                   initial = 'Artist')
        selected_page = forms.ChoiceField(required = False, 
                                          choices = [ (str(x),str(x)) for x in xrange(1,101)],
                                          initial = '1')
        items_per_page = forms.ChoiceField(required = False,
                                                choices = [('10', '10'),('25', '25'),('50', '50'),('100', '100')],
                                                initial = '25')
        
    albums = []
    errors = []
    
    pager = Paginator([],1)
    
    selected_page = 1
    
    form = None # it's our search form
    # If a form was just submitted
    if request.method == 'POST':
        form = SearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass    
            temp_genre = Genre.objects.filter(name__icontains = form.cleaned_data['genre'])            
            
            dash = form.cleaned_data['year'].find('-')
            
            # Search with the given year
            year = (None, None)
            if form.cleaned_data['year'] <> "":
                try:
                    if dash <> -1:
                        year_from = form.cleaned_data['year'][:dash]
                        year_to = form.cleaned_data['year'][dash+1:]
                        year = (datetime(int(year_from), 1, 1), datetime(int(year_to), 1, 1))
                    else:
                        year = (datetime(int(form.cleaned_data['year']), 1, 1), None)
                except ValueError:
                    errors.append("Invalid year or range entered.")
                    year = (None, None)
            
            if len(errors) < 1:
                song = form.cleaned_data['song']
                albums = Album.objects.all()
                if song <> '':
                    albums_with_track = PyLastFm().search_for_albums_by_song(song)
                    albums = albums.filter(name__in = albums_with_track)
                # First try to match the artist name with a comma, since artists are stored that way in the database
                albums = albums.filter(artist__name__icontains = Artist.commafy(form.cleaned_data['artist']))
                # If we didn't find the commafy-d title, try without the comma
                if (albums.count() < 1):
                    albums = albums.filter(artist__name__icontains = form.cleaned_data['artist'])
                    
                albums = albums.filter(name__icontains = form.cleaned_data['album'])
                albums = albums.filter(label__name__icontains = form.cleaned_data['label'])
                albums = albums.filter(genres__in = temp_genre)
            
                if year[0] is not None and year[1] is not None:
                    albums = albums.filter(date_released__gte = year[0])
                    albums = albums.filter(date_released__lte = year[1])
                elif year[0] is not None:
                    albums = albums.filter(date_released = year[0])
            
                
                sortby = form.cleaned_data['sortby']
            
                if sortby == "album":
                    sortby = "name"
                else:
                    sortby = sortby + "__name"    
                
                    
                albums = albums.filter(stack__name__icontains = form.cleaned_data['stack'])
                albums = albums.order_by(sortby).distinct()
                
                pager = Paginator(albums, form.cleaned_data['items_per_page'])
                selected_page = int(form.cleaned_data['selected_page'])
                
                page_list = [(str(x), str(x)) for x in pager.page_range][:100]
                if len(page_list) is 0:
                    form.fields['selected_page'].choices = [('1','1')]
                else:
                    form.fields['selected_page'].choices = page_list
                    
                form.fields['selected_page'].initial = selected_page
    else:
        form = SearchForm(initial = {
                                    'artist': request.GET.get('artist'),
                                    'album': request.GET.get('album'),
                                    'label': request.GET.get('label'),
                                    'year': request.GET.get('year'),
                                    'genre': request.GET.get('genre'),
                                    'stack': request.GET.get('stack'),
                                    'selected_page': "1",
                                    'items_per_page': "25",
                                    })
        form.fields['selected_page'].choices = [(str(x), str(x)) for x in pager.page_range][:100]
    
    albums_page = []
    try:
        albums_page = pager.page(selected_page).object_list
    except EmptyPage:
        albums_page = pager.page(1).object_list
        errors.append("That page is empty.")

    return render_to_response('library.html', {
        'form': form,
        'albums': albums_page,
        'errors': errors,
        }, context_instance=RequestContext(request))

def lib_artist(request, artist_name):
    artist_name_comma = Artist.commafy(artist_name)
    
    artist = get_object_or_none(Artist, name=artist_name_comma)
    if (artist is None):
        artist = get_object_or_none(Artist, name=artist_name)

    errors = []
    albums = []
    similar_artists = []
    artist_art = ''
    api = PyLastFm()
    
    if artist is not None:
        albums = Album.objects.filter(artist__name__iexact = artist.name).order_by("-date_released")
        
        if albums.count() > 0:
            similar_artists = [ similar for similar in api.get_similar_artists(artist)
                                if Artist.objects.filter(name__iexact = similar).count() > 0 or
                                Artist.objects.filter(name__iexact = Artist.commafy(similar)).count() > 0
                                ]
            artist_art = api.get_artist_art(artist)
            errors.extend(api.errors())

    return render_to_response('artist.html', {
        'errors': errors,
        'albums': albums,
        'artist': artist,
        'artist_art': artist_art,
        'similar_artists': similar_artists,
        }, context_instance=RequestContext(request)) 


def lib_album(request, artist_name, album_title):    
    errors = []
    songs = []
    album_art = ''
    api = PyLastFm()
    
    album = get_object_or_none(Album, artist__name__iexact = artist_name, name__iexact = album_title)
    artist = get_object_or_none(Artist, name__iexact = artist_name)
     
    if album is not None and artist is not None:
        album_art = api.get_album_art(album)
        track_list = api.get_track_list(album)
        
        songs = [ Song(name=track,
                       album=album,
                       fcc=LyricsWiki.has_fcc(LyricsWiki().get_lyrics(album.artist, track)),
                       ) \
                 for track in track_list ]
        errors.extend(api.errors())
    else:
        if artist is None:
            errors.append('The artist was not found in the WUVT Library.')
        if album is None:
            errors.append('The album was not found in the WUVT library.')

    return render_to_response('album.html', {
        'errors' : errors,
        'album': album,
        'album_art': album_art,
        'songs': songs,
        }, context_instance=RequestContext(request)) 
        
def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None