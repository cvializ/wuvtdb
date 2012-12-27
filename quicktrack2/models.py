from django.contrib.localflavor.us.models import PhoneNumberField
from django.db import models
from wuvt_ims.models import Song
# STATION
# A way to ID what playlist something is in.
# Generally, three options: FM, AM, and Test.
# I suppose this could be expanded in the future if we added an HD2 or something.
class Station(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        return self.name

# TRAFFIC TYPE
# Various types of traffic.  Currently consists of:
# PSA, Underwriting, Liner, ID, Promo.  Used simply as a way to pidgeonhole a traffic item.
class TrafficType(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        return self.name

# A show is a radio show that a DJ does.  Used to keep track of
# the current operator at the station and tie playlists and so forth to the DJ.
class Show(models.Model):
    name = models.CharField('Show Name',max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = PhoneNumberField()
    email = models.EmailField()
    description = models.TextField('Public Description of Your Show for the Website')
    genres = models.CharField('Types of music you play.', max_length=255)
    station = models.ForeignKey(Station, related_name="show_station_set")
    visible = models.BooleanField()
    
    def __unicode__(self):
        return self.name


# UNDERWRITERS.
# Just a rolodex of people who underwrite so we can tie their UA together.
class Underwriter(models.Model):
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        return self.name

# Similar to a Song, but a piece of traffic like PSA, UA, etc.
class Traffic(models.Model):
    name = models.CharField(max_length=100)
    underwriter = models.ForeignKey(Underwriter, null=True, blank=True)
    ref = models.CharField('Internal Reference Number', max_length = 32)
    type = models.ForeignKey(TrafficType)
    copy = models.TextField('Radio Copy', null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    kill = models.DateTimeField(null=True, blank=True)
    public_display = models.BooleanField()
    librarian_note = models.TextField(null=True, blank=True)

# The Operator Log contains the list of operators who have signed on and off of each
# given station.  We use this to ID the traffic log as well as the engineering log.
class OperatorLog(models.Model):
    show = models.ForeignKey(Show)
    station = models.ForeignKey(Station)
    time_on = models.DateTimeField()
    time_off = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.show.name

# The master table of everything people play.  Ever.  Colums are used to separate
# AM, FM playlists, and each item played is tied to a given show.
# Start and Stop times are determined by the Operator Log table.
class StationLog(models.Model):    
    operator = models.ForeignKey(OperatorLog)
    timestamp = models.DateTimeField('Time Played')

    song = models.ForeignKey(Song, null=True, blank=True)
    traffic = models.ForeignKey(Traffic, null=True, blank=True)

    request = models.BooleanField()
    vinyl = models.BooleanField()
    visible_public = models.BooleanField()
    
    def __unicode__(self):
        return self.song.name    

class EngineeringLog(models.Model):
    operator = models.ForeignKey(OperatorLog)   
    timestamp = models.DateTimeField('Time of Reading')
    voltage = models.FloatField('Transmitter Voltage')
    current = models.FloatField('Transmitter Current')
    forward = models.FloatField('Forward Power')
    reflected = models.FloatField('Reflected Power')
    temproom = models.FloatField('Indoor Temperature', null=True, blank=True)
    tempstack = models.FloatField('Stack Temperature', null=True, blank=True)
    tempout = models.FloatField('Outside Temperature', null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        return self.show.name  

# Traffic times deal mainly with UA.  By assigning a time a traffic item, we can bug the DJ
# at that time to read it.  mainly good for UA's.  This is kludgy and could stand to be improved.
class TrafficTime(models.Model):
    time = models.DateTimeField()
    traffic_item = models.ForeignKey(Traffic)
    
    def __unicode__(self):
        return self.time