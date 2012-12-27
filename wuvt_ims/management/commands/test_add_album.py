from django.core.management.base import BaseCommand, CommandError
from wuvtdb.wuvt_ims.models import *
from optparse import make_option

class Command(BaseCommand):
    args = '<albumname artistname labelname>'
    help = 'Adds a test album with the specified info'

    def handle(self, *args, **options):
        al = Album()
        al.name = args[0]
        self.stdout.write('Album "%s"\n' % al.name)
        
        
        try:
            artist_temp = Artist.objects.get(name=args[1])
        except Artist.DoesNotExist:
            artist_temp = Artist()
            artist_temp.name = args[1]
            artist_temp.save()
            
        try:
            label_temp = Label.objects.get(name=args[2])
        except Label.DoesNotExist:
            label_temp = Label()
            label_temp.name = args[2]
            label_temp.save()
            
        try:
            stack_temp = Stack.objects.get(name='Test')
        except Stack.DoesNotExist:
            stack_temp = Stack()
            stack_temp.name = 'Test'
            stack_temp.save()
            
        try:
            composer_temp = Composer.objects.get(name='None')
        except Composer.DoesNotExist:
            composer_temp = Composer()
            composer_temp.name = 'None'
            composer_temp.save()
            
        try:
            rotation_bin_temp = RotationBin.objects.get(name='Not in Rotation')
        except RotationBin.DoesNotExist:
            rotation_bin_temp = RotationBin()
            rotation_bin_temp.name = 'Not in Rotation'
            rotation_bin_temp.save()
            
        al.album_artist = artist_temp
        al.album_composer = composer_temp
        al.label = label_temp
        al.stack = stack_temp
        al.rotation_bin = rotation_bin_temp
        al.num_discs = 1
        al.missing = False
        al.visible = True
        al.compilation = False
        al.needs_review = False
        al.save()

        self.stdout.write('Successfully added album "%s"\n' % al.name)