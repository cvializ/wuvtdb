from django import forms
from django.db.models import Q
from django.forms.util import ErrorList
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from pylast import WSError

from itertools import chain
import re, datetime

from wuvt_ims.models import *
from wuvt_ims.api import PyLastFm, LyricsWiki, EchoNest


class YearRangeCharField(forms.CharField):
    __metaclass__ = models.SubfieldBase
    
    def validate(self, value):
        'Value is a tuple containing two dates, or no dates'
        if value[0] is None:
            if value[1] is not None:
                raise ValidationError('There must be a first date if there is a second.')
            else:
                # Just leave if value[0] and value[1] are both None.
                return
        if value[1] is None and value[0] < datetime.datetime(1890, 1, 1):
            raise ValidationError('Your query predates recorded sound.')
        if value[1] is not None and value[0] > value[1]:
            raise ValidationError('The first date must be earlier than the second.')
    
    def to_python(self, value):
        if not value:
            return (None, None)
    
        if isinstance(value, tuple):
            return value;
    
        # Validate
        #self.validate(value)
    
        dash = value.find('-')
        year_range = (None, None)
        if dash != -1:
            year_from = value[:dash]
            year_to = value[dash+1:]
            year_range = (datetime.datetime(int(year_from), 1, 1), datetime.datetime(int(year_to), 1, 1))
        else:
            year_range = (datetime.datetime(int(value), 1, 1), None)
    
        return year_range


class SearchForm(forms.ModelForm):
    
    year = YearRangeCharField()
    
    class Meta:
        model = AlbumSearch
        exclude = ('start_year', 'stop_year')
    
        
    def clean_year(self):
        data = self.cleaned_data['year']
        
        field = YearRangeCharField()
        
        data = field.to_python(data)
        
        return data     
    
    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(SearchForm, self).save(commit=False)
        
        year_range = self.cleaned_data['year']
        instance.start_year = year_range[0].year if year_range[0] is not None else u''
        instance.stop_year = year_range[1].year if year_range[1] is not None else u''

        if commit:
            instance.save()
            
        return instance
    
    sortby = forms.ChoiceField(choices=[('artist', 'Artist'),
                                        ('album', 'Album'),
                                        ('label', 'Label'),
                                        ('genre', 'Genre'),
                                        ('stack', 'Stack'),
                                        ('-date_released', 'Date'), ],
                               initial='Artist')
    selected_page = forms.ChoiceField(required=False,
                                      choices=[(str(x), str(x)) for x in xrange(1, 101)],
                                      initial='1')
    items_per_page = forms.ChoiceField(required=False,
                                       choices=[('10', '10'),
                                                ('25', '25'),
                                                ('50', '50'),
                                                ('100', '100')],
                                       initial='25')

def lib_main(request):
    albums = []
    errors = ErrorList()

    pager = Paginator([], 1)
    selected_page = 1

    form = None  # it's our search form
    # If a form was just submitted
    if request.method == 'POST':
        form = SearchForm(request.POST)  # A form bound to the POST data
        if form.is_valid():
            # Use the form fields to search and filter albums from the db
            albums = lib_main_filter_albums(form)

            pager = Paginator(albums, form.cleaned_data['items_per_page'])
            selected_page = int(form.cleaned_data['selected_page'])

            page_list = [(str(x), str(x)) for x in pager.page_range][:100]
            if len(page_list) is 0:
                form.fields['selected_page'][('1', '1')]
            else:
                form.fields['selected_page'].choices = page_list
            form.fields['selected_page'].initial = selected_page
        else:
            # Add all of the errors in the form.errors dict to our error list
            errors.extend(chain.from_iterable(form.errors.values()))
        form.save()
    else:
        form = SearchForm(initial={'artist': request.GET.get('artist'),
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


def lib_main_filter_albums(form):
    # Initialize the query
    albums = Album.objects.all()

    # First filter by song, since it's the most limiting and costly
    song = form.cleaned_data['song']
    artist = form.cleaned_data['artist']
    if song:
        artist = re.sub(' ?(the|of|and)', '', artist)
        albums_with_track = PyLastFm().search_for_albums_by_song(song, artist)

        q_album = Q()
        for track_album in albums_with_track:
            q_matches_artist = Q(artist__name__icontains=track_album[0]) | Q(artist__name__icontains=Artist.commafy(track_album[0]))
            q_matches_album = Q(name__icontains=track_album[1])
            q_album = q_album | (q_matches_artist & q_matches_album)
        albums = albums.filter(q_album)
#        for album in albums:
#            save_track_list(album)
    else:
        current_query = albums
        # Try to match the artist name with a comma, since artists are stored that way in the database
        albums = current_query.filter(artist__name__icontains=Artist.commafy(artist))
        # If we didn't find the commafy-d title, try without the comma
        if (albums.count() < 1):
            albums = current_query.filter(artist__name__icontains=artist)

    # Filter by fields
    if form.cleaned_data['album']:
        albums = albums.filter(name__icontains=form.cleaned_data['album'])
    if form.cleaned_data['label']:
        albums = albums.filter(label__name__icontains=form.cleaned_data['label'])
    if form.cleaned_data['stack']:
        albums = albums.filter(stack__name__icontains=form.cleaned_data['stack'])
    if form.cleaned_data['genre']:
        temp_genre = Genre.objects.filter(name__icontains=form.cleaned_data['genre'])
        albums = albums.filter(genres__in=temp_genre)

    # Filter by year or year range
    year = form.cleaned_data['year']
    if year[0] is not None and year[1] is not None:
        albums = albums.filter(date_released__gte=year[0].date)
        albums = albums.filter(date_released__lte=year[1].date)
    elif year[0] is not None:
        albums = albums.filter(date_released=year[0].date)

    # Sort the query
    sortby = form.cleaned_data['sortby']
    if sortby == 'album':
        sortby = 'name'
    elif 'date_released' not in sortby:
        sortby = sortby + '__name'
    albums = albums.order_by(sortby).distinct()

    return albums


def lib_artist(request, artist_name):
    artist_name_comma = Artist.commafy(artist_name)

    artist = get_object_or_none(Artist, name=artist_name_comma)
    if (artist is None):
        artist = get_object_or_none(Artist, name=artist_name)

    errors = ErrorList()
    albums = []
    similar_artists = []
    artist_art = ''
    api = PyLastFm()
    art_api = EchoNest()

    if artist is not None:
        albums = Album.objects.filter(artist=artist).order_by("-date_released")

        if albums.count() > 0:
            lfm_artist = get_last_fm_artist_name(artist)
            if lfm_artist:
                similar_artists = [similar for similar in api.get_similar_artists(lfm_artist)
                                   if Artist.objects.filter(name__iexact=similar).count() > 0 or
                                   Artist.objects.filter(name__iexact=Artist.commafy(similar)).count() > 0
                                   ]
                artist_art = art_api.get_artist_art(lfm_artist)
            else:
                errors.append('The artist could not be found by Last.Fm')

    return render_to_response('artist.html', {
        'errors': errors,
        'albums': albums,
        'artist': artist,
        'artist_art': artist_art,
        'similar_artists': similar_artists,
    }, context_instance=RequestContext(request))


def lib_album(request, artist_name, album_title):
    errors = ErrorList()
    songs = []
    album_art = ''
    api = PyLastFm()

    album = get_object_or_none(Album, artist__name__iexact=artist_name, name__iexact=album_title)
    artist = get_object_or_none(Artist, name__iexact=artist_name)

    if album is not None and artist is not None:
        # Check if we have the track listing in our database
        songs = Song.objects.filter(album=album).order_by('track_num')

        try:
            lfm_artist = get_last_fm_artist_name(artist)
            album_art = api.get_album_art(lfm_artist, album.name)
            # If not, get the track listing from Last.fm and save it.
            if songs.count() == 0:
                songs = save_track_list(album)
        except WSError:
            errors.append('The album or artist could not be found by Last.Fm')
            
    else:
        if artist is None:
            errors.append('The artist was not found in the WUVT Library.')
        if album is None:
            errors.append('The album was not found in the WUVT library.')

    return render_to_response('album.html', {
        'errors': errors,
        'album': album,
        'album_art': album_art,
        'songs': songs,
    }, context_instance=RequestContext(request))


def get_last_fm_artist_name(lib_artist):
    if lib_artist.api_name:
        return lib_artist.api_name

    # If there's more than one alternative name (the first is the db name)
    # then we have actual alternatives
    alternative_names = lib_artist.name_and_alternatives
    if len(alternative_names) > 1:
        api = PyLastFm()
        lib_artist.api_name = api.get_most_popular(alternative_names)
        lib_artist.save()
        return lib_artist.api_name
    else:
        return lib_artist.name_without_comma


def save_track_list(album):
    lib_list = Song.objects.filter(album=album)
    if lib_list.count() > 0:
        return lib_list
    else:
        api = PyLastFm()
        songs = []
        track_list = api.get_track_list(get_last_fm_artist_name(album.artist), album.name)
        for track in track_list:
            song = Song(name=track,
                        album=album,
                        fcc=LyricsWiki.has_fcc(LyricsWiki().get_lyrics(album.artist, track)),
                        track_num=track_list.index(track)
                        )
            songs.append(song)
            song.save()
        return songs


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
