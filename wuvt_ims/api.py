import urllib
import time
import hashlib
import requests
import pylast

from xml.etree import ElementTree
from wuvt_ims.models import *
from pylast import COVER_LARGE, IMAGES_ORDER_POPULARITY, WSError


class AbstractApi(object):
    def __init__(self, url, key):
        self._key = key
        self._url = url
        self._errors = []

    def get(self, resource, params=None, alternate_url=''):
        """Take a dict of params, and return what we get from the api"""
        if not params:
            params = {}

        params = urllib.urlencode(params)

        request_url = self._url
        if alternate_url:
            request_url = alternate_url

        url = request_url % (resource, self._key, params)

        resp = requests.get(url)

        if resp.status_code != 200 and resp.status_code != 400:
            self._errors.append(resp.error)

        return ElementTree.XML(resp.content)


class MusicApi(AbstractApi):
    def get_similar_artists(self, artist):
        raise NotImplementedError

    def get_similar_albums(self, album):
        raise NotImplementedError

    def get_track_list(self, album):
        raise NotImplementedError

    def get_track_sample(self, album, track):
        raise NotImplementedError

    def get_album_art(self, album):
        raise NotImplementedError

    def get_artist_art(self, album):
        raise NotImplementedError

    def search_for_albums_by_song(self, title):
        raise NotImplementedError

    def search_for_album_by_song(self, title, artist):
        raise NotImplementedError

    def errors(self):
        errors = list(self._errors)
        self._errors = []
        return errors


class EchoNest(MusicApi):
    def __init__(self):
        super(EchoNest, self).__init__('http://developer.echonest.com/api/v4/%s?api_key=%s&%s',
                                       'FB1MYKOM4ZVADN2MS');

    def get_artist_art(self, artist):
        request_args = {
            'name': artist,
            'format': 'xml',
            'results': '1',
            'license': 'unknown'
        }
        tree = self.get('artist/images', request_args)
        if tree is not None:
            artist_art_tag = tree.find(".//image/url")
            if artist_art_tag is not None:
                return artist_art_tag.text
        else:
            self._errors.append("Error retrieving artist art from EchoNest")


class PyLastFm(MusicApi):
    def __init__(self):
        super(PyLastFm, self).__init__('', '530c72108fe6d60d35bb4a8fda85efd5')
        self._secret = 'a01496aac8e2c7ddc90371aba5118317'
        self._network = pylast.LastFMNetwork(api_key=self._key,
                                             api_secret=self._secret,
                                             )

    def get(self, resource=None, params=None):
        raise NotImplementedError

    def get_similar_artists(self, lfm_artist):
        artist = self._network.get_artist(lfm_artist)
        try:
            return [similar_item.item.get_name() for similar_item in artist.get_similar(8)]
        except WSError:
            return []

    def get_album_art(self, lfm_artist, album_name):
        try:
            album = self._network.get_album(lfm_artist, album_name)
            return album.get_cover_image(COVER_LARGE)
        except WSError:
            return ''

    def get_track_list(self, lfm_artist, album_name):
        try:
            album = self._network.get_album(lfm_artist, album_name)
            return [track.get_name() for track in album.get_tracks()]
        except WSError:
            return []

    def get_artist_art(self, lfm_artist):
        try:
            artist = self._network.get_artist(lfm_artist)
            image_list = artist.get_images(IMAGES_ORDER_POPULARITY, 1)
            if len(image_list) > 0:
                return image_list[0].sizes.large
            else:
                return ''
        except WSError:
            return ''

    def search_for_album_by_song(self, title, artist_name):
        try:
            track = self._network.get_track(artist_name, title)
            if track.get_album() is not None:
                return track.get_album().get_name()
            else:
                return None
        except WSError:
            return None;

    def search_for_albums_by_song(self, title, artist=''):
        try:
            track_results = self._network.search_for_track(artist, title)
            return [(track.get_artist().get_name(), track.get_album().get_name())
                    for track in track_results.get_next_page()
                    if track.get_album() is not None and
                    track.get_artist() is not None]
        except WSError:
            return []
        

    def get_most_popular(self, artists):
        popularity = {}
        for artist in artists:
            try:
                lfm_artist = self._network.get_artist(artist)
                popularity[artist] = lfm_artist.get_playcount()
            except WSError:
                continue

        popularity = sorted(popularity.items(), key=lambda x: x[1], reverse=True)
        if popularity:
            return popularity[0][0]
        else:
            return None


class LastFm(MusicApi):
    def __init__(self):
        super(LastFm, self).__init__('http://ws.audioscrobbler.com/2.0/?%s&api_key=%s&%s',
                                     '530c72108fe6d60d35bb4a8fda85efd5')

    def get(self, resource, params=None):
        params['method'] = resource['method']
        return super(LastFm, self).get('', params)

    def get_similar_artists(self, artist):
        request_args = {'artist': artist.name_without_comma, 'limit': 8}

        tree = self.get({'method': 'artist.getsimilar'}, request_args)
        if tree is not None:
            # Only show a similar artist if WUVT has it.
            return [unicode(tag.text) for tag in tree.iterfind('.//name')]
        else:
            self._errors.append("Error retrieving similar artists from Last.fm")

    def get_artist_art(self, artist):
        request_args = {'artist': artist.name_without_comma, 'limit': 8}
        tree = self.get({'method': 'artist.getinfo'}, request_args)
        if tree is not None:
            artist_art_tag = tree.find(".//image[@size='large']")
            if artist_art_tag is not None:
                return artist_art_tag.text
        else:
            self._errors.append("Error retrieving artist art from Last.fm")

    def get_track_list(self, album):
        request_args = {'artist': album.artist.name_without_comma,
                        'album': album.name}
        tree = self.get({'method': 'album.getinfo'}, request_args)

        if tree is not None:
            return [unicode(tag.text) for tag in tree.iterfind('.//track/name')]
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")

    def get_album_art(self, album):
        request_args = {'artist': album.artist.name_without_comma,
                        'album': album.name}
        tree = self.get({'method': 'album.getinfo'}, request_args)

        if tree is not None:
            album_art_tag = tree.find(".//image[@size='large']")
            if album_art_tag is not None:
                return album_art_tag.text
        else:
            self._errors.append("Error retrieving album art from Last.fm")

    def search_for_albums_by_song(self, title):
        request_args = {'track': title}
        tree = self.get({'method': 'track.search'}, request_args)

        if tree is not None:
            return [(tag.find('artist').text.encode('utf-8'),
                     self._search_for_album_by_song(tag.find('name').text.encode('utf-8'),
                                                    tag.find('artist').text.encode('utf-8')))
                    for tag in tree.iterfind('.//track')]
        else:
            self._errors.append("Error retrieving album titles containing a track from Last.fm")

    def search_for_album_by_song(self, title, artist_name):
        request_args = {'track': title,
                        'artist': artist_name}
        tree = self.get({'method': 'track.getInfo'}, request_args)

        if tree is not None:
            album_title_tag = tree.find(".//album/title")
            if album_title_tag is not None:
                return album_title_tag.text.encode('utf-8')


class AllMusic(MusicApi):
    def __init__(self):
        super(AllMusic, self).__init__('http://api.rovicorp.com/data/v1/%s?apikey=%s&format=xml&%s',
                                       'w257dh2mk53pg8rz3uyqnght')
        self._secret = 'sneGF2JCmN'

    def _sig(self):
        timestamp = int(time.time())

        m = hashlib.md5()
        m.update(self._key)
        m.update(self._secret)
        m.update(str(timestamp))

        return m.hexdigest()

    def get(self, resource, params=None, alternate_url=""):
        params['sig'] = self._sig()
        return super(AllMusic, self).get(resource, params)

    def get_track_list(self, album):
        tree = self.get('album/tracks', {'album': album.name})

        if tree is not None:
            return [unicode(tag.text) for tag in tree.iterfind('.//{com.rovicorp.metadataservice}Track/{com.rovicorp.metadataservice}title')]
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")

    def get_track_sample(self, track):
        request_args = {'track': track}
        tree = self.get('song/sample', request_args)

        if tree is not None:
            sample_tag = tree.find('.//{com.rovicorp.metadataservice}sample')
            if sample_tag is not None:
                return sample_tag.text
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")

    def search_by_song(self, title):
        v2service_url = "http://api.rovicorp.com/search/v2.1/music/%s?apikey=%s&format=xml&%s"
        request_args = {'entitytype': 'song',
                        'query': title,
                        'size': 20}
        tree = self.get('search', request_args, alternate_url=v2service_url)
        if tree is not None:
            song_tags = tree.findall('.//{com.rovicorp.metadataservice}song')
            if song_tags is not None:
                return song_tags.text
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")


class LyricsWiki(AbstractApi):
    def __init__(self):
        super(LyricsWiki, self).__init__('http://lyrics.wikia.com/api.php?format=xml&action=query&%s&prop=revisions&rvprop=content',
                                         '')

    def _wikify(self, label):
        return label.title().replace(' ', '_')

    def get(self, resource, params):
        params = dict((key, self._wikify(value)) for (key, value) in params.items())
        params = urllib.urlencode(params)
        url_request = self._url % (params)

        response = requests.get(url_request)

        if (response.status_code != 200 and response.status_code != 400):
            self._errors.append("Error accessing Lyrics Wiki")

        return ElementTree.XML(response.content)

    def get_lyrics(self, artist, track):
        tree = self.get('', {'titles': artist.name_without_comma + ':' + track})

        if tree is not None:
            lyric_tag = tree.find('.//rev')
            if lyric_tag is not None:
                return lyric_tag.text

    @staticmethod
    def has_fcc(lyrics):
        if lyrics is None:
            return False

        fcc_words = ['shit', 'piss', 'fuck', 'cunt', 'cock', 'goddamn', 'god damn', 'bitch', 'nigger']
        for word in fcc_words:
            if lyrics.find(word) != -1:
                return True
        return False
