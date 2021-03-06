from django.db import models
from django.contrib.localflavor.us.models import PhoneNumberField
from django.core.exceptions import ValidationError


class AlbumSearch(models.Model):
    song = models.CharField(max_length=255, blank=True)
    artist = models.CharField(max_length=255, blank=True)
    album = models.CharField(max_length=255, blank=True)
    label = models.CharField(max_length=255, blank=True)
    start_year = models.CharField(max_length=255, blank=True)
    stop_year = models.CharField(max_length=255, blank=True)
    genre = models.CharField(max_length=255, blank=True)
    stack = models.CharField(max_length=255, blank=True)    
        
    def clean(self):
        form_empty = True
        for field_name, field_value in self.__dict__.iteritems():
            # Check for None or '', so IntegerFields with 0 or similar things don't seem empty.
            if field_value is not None and field_value != '':
                form_empty = False
                break
        if form_empty:
            raise ValidationError(u"You must fill at least one field!")

class Stack(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Reviewer(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Review(models.Model):
    reviewer = models.ForeignKey(Reviewer, related_name='reviewer_set')
    text = models.TextField()

    def __unicode__(self):
        return str(self.text)


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


class Artist(models.Model):
    name = models.CharField(max_length=100)
    api_name = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField('About the Artist', null=True, blank=True)
    librarian_note = models.TextField('WUVT Notes', null=True, blank=True)
    related_artists = models.ManyToManyField("self", null=True, blank=True)
    needs_librarian_review = models.BooleanField()

    def __unicode__(self):
        return self.name

    @property
    def name_and_alternatives(self):
        """Splits names and parentheticals into possible alternative names:
            'M + M (Martha and the Muffins)' -> ['M + M','Martha ... ']
            It should try:
                The Whole Thing
                The Whole Thing without Commas
                Just Parenthetical
                No Parenthetical"""
        name_options = [self.name, self.name.replace(',', '')]
        insignificant_cues = ['featuring', 'of', 'member of']
        if '(' in self.name and ')' in self.name:
            # add what's before the parens, assuming a space before the (
            before_parens = self.name[:self.name.find('(') - 1]
            name_options.append(Artist.decommafy(before_parens))
            # add what's between the parens, if it's significant
            between_parens = self.name[self.name.find('(') + 1:self.name.find(')')]
            insignificant = False
            for cue in insignificant_cues:
                if cue in between_parens:
                    insignificant = True
                    break
            if not insignificant:
                name_options.append(between_parens)

        return name_options

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
        if ',' in label:
            firstCommaPosition = label.find(',')
            firstAndPosition = label.find('&') if label.find('&') != -1 else label.find('and')
            if (firstCommaPosition < firstAndPosition):
                return label[firstCommaPosition + 2:firstAndPosition] + \
                    label[:firstCommaPosition] + " " + \
                    label[firstAndPosition:]
            else:
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


class Album(models.Model):
    name = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, related_name='artist_set')
    composer = models.ForeignKey(Artist, related_name='album_composer_set', null=True, blank=True)
    label = models.ForeignKey(Label)
    stack = models.ForeignKey(Stack)
    num_discs = models.IntegerField()
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


class Song(models.Model):

    SUGGESTED_CHOICES = (
        (u'N', u'Not Suggested'),
        (u'S', u'Suggested'),
        (u'!', u'Highly Suggested'),
    )

    album = models.ForeignKey(Album)
    name = models.CharField(max_length=255)
    track_num = models.IntegerField(null=True, blank=True)
    fcc = models.BooleanField()
    suggested = models.CharField(max_length=1, choices=SUGGESTED_CHOICES, null=True, blank=True)
    lyrics = models.TextField(null=True, blank=True)
    librarian_note = models.TextField(null=True, blank=True)
    needs_librarian_review = models.BooleanField()

    def __unicode__(self):
        return self.name
