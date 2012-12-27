import urllib
import time
import hashlib
import requests
from requests import ConnectionError

from xml.etree import ElementTree
from wuvt_ims.models import *

class AbstractApi(object):
    def __init__(self, url, key):
        self._key = key
        self._url = url
        self._errors = []

    def get(self, resource, params = None):
        """Take a dict of params, and return what we get from the api"""
        if not params:
            params = {}

        params = urllib.urlencode(params)

        url = self._url % (resource, self._key, params)

        resp = requests.get(url)

        if resp.status_code <> 200 and resp.status_code <> 400:
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
    
    def errors(self):
        errors = list(self._errors)
        self._errors = []
        return errors
    
class LastFm(MusicApi):
    def __init__(self):
        super(LastFm, self).__init__('http://ws.audioscrobbler.com/2.0/?%s&api_key=%s&%s',
                             '530c72108fe6d60d35bb4a8fda85efd5')
    
    def get(self, resource, params = None):
        params['method'] = resource['method']
        return super(LastFm, self).get('',params)
    
    def get_similar_artists(self, artist):
        request_args = {'artist': artist.name_without_comma, 'limit': 8}
            
        tree = self.get({'method': 'artist.getsimilar'}, request_args)
        if tree is not None:
            # Only show a similar artist if WUVT has it.
            all_similar_artists = [ unicode(tag.text) for tag in tree.iterfind('.//name') ]
            return [ wuvt_artist for wuvt_artist in all_similar_artists \
                        if Artist.objects.filter(name__iexact = wuvt_artist).count() > 0 or \
                        Artist.objects.filter(name__iexact = Artist.commafy(wuvt_artist)).count() > 0 ]
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
                        'album': album.name
                       }
        tree = self.get({'method': 'album.getinfo'}, request_args)
        
        if tree is not None:
            return [ unicode(tag.text) for tag in tree.iterfind('.//track/name') ]
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")
            
    def get_album_art(self, album):
        request_args = {'artist': album.artist.name_without_comma,
                        'album': album.name
                       }
        tree = self.get({'method': 'album.getinfo'}, request_args)
        
        if tree is not None:
            album_art_tag = tree.find(".//image[@size='large']")
            if album_art_tag is not None:
                return album_art_tag.text
        else:
            self._errors.append("Error retrieving album art from Last.fm")
        
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

    def get(self, resource, params=None):       
        params['sig'] = self._sig()
        return super(AllMusic, self).get(resource, params)
    
    def get_track_list(self, album):
        tree = self.get('album/tracks', { 'album': album.name })
        
        if tree is not None:
            return [ unicode(tag.text) for tag in tree.iterfind('.//{com.rovicorp.metadataservice}Track/{com.rovicorp.metadataservice}title') ]
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")
    
    def get_track_sample(self, track):
        request_args = { 'track': track }
        tree = self.get('song/sample', request_args)
        
        if tree is not None:
            sample_tag = tree.find('.//{com.rovicorp.metadataservice}sample')
            if sample_tag is not None:
                return sample_tag.text
        else:
            self._errors.append("Error retrieving tracklist from Last.fm")

class LyricsWiki(AbstractApi):
    def __init__(self):
        super(LyricsWiki, self).__init__('http://lyrics.wikia.com/api.php?format=xml&action=query&%s&prop=revisions&rvprop=content',
                             '')
    def _wikify(self, label):
        return label.title().replace(' ','_')
        
    def get(self, resource, params):
        params = { key : self._wikify(value) for key, value in params.items() }
        params = urllib.urlencode(params)
        url_request = self._url % (params)

        response = requests.get(url_request)
        
        if (response.status_code <> 200 and response.status_code <> 400):
            self._errors.append("Error accessing Lyrics Wiki")

        return ElementTree.XML(response.content)
    
    def get_lyrics(self, artist, track):
        tree = self.get('',{ 'titles': artist.name_without_comma + ':' + track })
        
        if tree is not None:
            lyric_tag = tree.find('.//rev')
            if lyric_tag is not None:
                return lyric_tag.text
            
    @staticmethod     
    def has_fcc(lyrics):
        if lyrics is None:
            return False
        
        fcc_words = ['shit','piss','fuck','cunt','cock', 'goddamn','god damn','bitch','nigger']
        for word in fcc_words:
            if lyrics.find(word) <> -1:
                return True
        return False