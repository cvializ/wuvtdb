from django.db import models
from django.contrib.localflavor.us.models import PhoneNumberField

class Stack(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name
        
# REVIEWERS
# People who review records.  Keeps things nice and orderly
# and separates reviewers from user accounts.  This is necessary to accomodate past album
# reviews that will be painfully and meticulously added to the database.  yeah.
class Reviewer(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
  
# Labels are record labels.  They are assigned by album, not artist.
class Label(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField('About the Label', null=True, blank=True)
    contact = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    related_labels = models.ManyToManyField("self", null=True, blank=True)
    
    def __unicode__(self):
        return self.name

# An Artist has a name, bio, note from Len, and related artists.
class Artist(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField('About the Artist', null=True, blank=True)
    librarian_note = models.TextField('WUVT Notes', null=True, blank=True)
    related_artists = models.ManyToManyField("self", null=True, blank=True)
    needs_librarian_review = models.BooleanField()
    
    def __unicode__(self):
        return self.name
    
    @property
    def name_without_comma(self):
        """Swaps the two segments of text before and after the first comma: Bowie, David -> David Bowie"""
        return self.decommafy(unicode(self.name))
        
    @property
    def name_with_comma(self):
        """Separates the first word of text and places it at the end with a comma The Flaming Lips -> Flaming Lips, The"""
        return self.commafy(unicode(self.name)) 

    @staticmethod
    def decommafy(label):
        firstCommaPosition = label.find(',')
        firstAndPosition = label.find('&') if label.find('&') <> -1 else label.find('and')
        if (firstCommaPosition < firstAndPosition):
            return label[firstCommaPosition + 2:firstAndPosition] + \
                    label[:firstCommaPosition] + " " + \
                    label[firstAndPosition:]
            
        if (firstCommaPosition > -1):
            return label[firstCommaPosition + 2:] + " " + label[:firstCommaPosition]
        else:
            return label
        
    @staticmethod
    def commafy(label):
        """Separates the first word of text and places it at the end with a comma The Flaming Lips -> Flaming Lips, The"""
        firstSpacePosition = label.find(" ")
        if (firstSpacePosition > -1 and label.count(',') == 0):
            return label[firstSpacePosition + 1:] + ", " + label[:firstSpacePosition]
        else:
            return label   
        
# An individual, physical album in the stacks at WUVT.
class Album(models.Model):
    name = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, related_name='artist_set')
    album_composer = models.ForeignKey(Artist, related_name='album_composer_set', null=True, blank=True)
    label = models.ForeignKey(Label)
    stack = models.ForeignKey(Stack)
    num_discs = models.IntegerField()
    reviewer = models.ForeignKey(Reviewer, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    date_added = models.DateField(null=True, blank=True)
    date_released = models.DateField(null=True, blank=True)
    librarian_note = models.TextField('WUVT Notes', null=True, blank=True)
    related_albums = models.ManyToManyField("self", null=True, blank=True)
    missing = models.BooleanField()
    visible = models.BooleanField()
    compilation = models.BooleanField()
    needs_librarian_review = models.BooleanField()
    
    def __unicode__(self):
        return self.name

# A song.  Each song can live on one album.

class Song(models.Model):

    SUGGESTED_CHOICES = (
        (u'N', u'Not Suggested'),
        (u'S', u'Suggested'),
        (u'!', u'Highly Suggested'),
    )

    album = models.ForeignKey(Album)
    song_artist = models.ForeignKey(Artist, related_name='song_artist_set', null=True, blank=True)
    song_composer = models.ForeignKey(Artist, related_name='song_composer_set', null=True, blank=True)
    name = models.CharField(max_length=100)
    track_num = models.IntegerField(null=True, blank=True)
    fcc = models.BooleanField()
    suggested = models.CharField(max_length=1, choices=SUGGESTED_CHOICES, null=True, blank=True)
    lyrics = models.TextField(null=True, blank=True)
    librarian_note = models.TextField(null=True, blank=True)
    needs_librarian_review = models.BooleanField()
    
    def __unicode__(self):
        return self.name
