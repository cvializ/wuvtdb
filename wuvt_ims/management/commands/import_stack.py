from django.core.management.base import BaseCommand
from itertools import chain
import os

import xlrd

from wuvt_ims.models import *

"""
 The command will take a given CSV Sheet and assign all albums in
 it to a specified stack.

 Columns are as follows:
 0: Artist Name
 1: Album Name
 2: Label
 3: Release Year
 4: Genre
 5: Location (Should be the same for all items in the sheet)
 6: M or Missing indicates track is missing

 The Excel Spreadsheets are much easier to deal with, IMO

"""
class Command(BaseCommand):
    args = '<datafile>'
    help = 'Adds an Excel Table'

    def handle(self, *args, **options):
        
        if (len(args) is 0):
            print "No argument supplied."
            return
        
        input_path = os.path.join(os.path.dirname(__file__), "../../", args[0])
        
        
        print "Input Path: " + input_path
        
        if os.path.isdir(input_path):
            print "Importing entire directory of stack sheets."
            self._import_directory(input_path)
        elif os.path.isfile(input_path):
            print "Importing single stack sheet."
            self._import_stack(input_path)
        else:
            print "Unknown input type"
            return

    def _import_directory(self, input_path):
        for path in os.listdir(input_path):
            print "Adding " + path + " to database"
            self._import_stack(os.path.join(input_path, path))
            
        return 
    
    def _import_stack(self, input_path):
        if(input_path[-3:] == "xls"):            
            try:
                book = xlrd.open_workbook(input_path)  
            except IOError:
                print "File Not Found: " + input_path
                return
        else:
            print "The file is not in xls format. Exiting."
            return

        stack_add_results = { "added": 0, "skipped": 0, "errors": 0 }
        for album_info in self._generate_album_rows(book):
            # If the Album already exists, we should ignore it and move on.
            album_query = Album.objects.filter(name = unicode(album_info["title"])).filter(artist__name = unicode(album_info["artist"]))
            if album_query.count() == 0:
                # Create a new Album object.
                al = Album()
                
                # Assign it its name.
                al.name = album_info["title"]

                # Now deal with the artist.  We see if there is an
                # artist in the database with the given name.
                # If not, we add a new one!
                try:
                    artist_temp = Artist.objects.get(name = album_info["artist"])
                except Artist.DoesNotExist:
                    artist_temp = Artist(name = album_info["artist"])
                    artist_temp.save()
                
                # Now deal with the label.  We see if there is a
                # label in the database with the given name.
                # If not, we add a new one!
                try:
                    label_temp = Label.objects.get(name = album_info["label"])
                except Label.DoesNotExist:
                    label_temp = Label(name = album_info["label"])
                    label_temp.save()

                # Now deal with the stack.  We see if there is a
                # stack in the database with the given name.
                # If not, we add a new one!   
                try:
                    stack_temp = Stack.objects.get(name = album_info["stack"])
                except Stack.DoesNotExist:
                    stack_temp = Stack(name = album_info["stack"])
                    stack_temp.save()                             
                    
                # Now deal with the missing info.  If the field contains
                # "missing" or "M", flag Missing.
                temp_missing = False
                #if row_missing == 'Missing':
                #    temp_missing = True
                #elif row_missing == 'M':
                #    temp_missing = True
                    
                al.artist = artist_temp
                al.label = label_temp
                al.stack = stack_temp
                
                album_info["year"] = str(album_info["year"])[:4]
                
                try:
                    album_info["year"] = str(int(album_info["year"]))
                except ValueError:
                    album_info["year"] = "0001"
   
                if len(album_info["year"]) < 4:
                        album_info["year"] = "0001"
                    
                al.date_released = album_info["year"] + "-01-01"
                
                al.num_discs = 1
                al.missing = temp_missing
                al.visible = True
                al.compilation = False
                al.needs_review = False
                
                try:
                    al.save()
                except:
                    print "**** Error: "
                    print al.name;
                    stack_add_results["errors"] += 1
                    continue
                    
                al = Album.objects.get(name = album_info['title'],
                                        artist = artist_temp)
                
                #genres are tricky. assume they're slash '/' separated
                try:
                    genres = unicode(album_info["genres"]).split('/')
                except:
                    print "****ERROR: " + unicode(album_info["genres"])
                    genres = []
                for genre in genres:
                    genre = genre.strip()
                    genre = genre.replace("  ", " ")
                    
                    try:
                        genre_temp = Genre.objects.get(name = genre)
                    except Genre.DoesNotExist:
                        genre_temp = Genre(name = genre)
                        genre_temp.save()
                        
                    al.genres.add(genre_temp)
                    
                stack_add_results["added"] += 1
            else: # the album exists
                stack_add_results["skipped"] += 1
              
        for key, value in stack_add_results.items():
            print str(key) + ": " + str(value)
        return
    
    def _generate_sheet(self, book):
        return (book.sheet_by_index(sheetIndex) for sheetIndex in xrange(0, book.nsheets))
    
    def _generate_row(self, sheet):
        return (sheet.row(rowIndex) for rowIndex in xrange(0, sheet.nrows))
    
    def _generate_album_rows(self, book):
        return ({"artist": unicode(row[0].value),
                 "title": unicode(row[1].value),
                 "label": unicode(row[2].value),
                 "year": row[3].value,
                 "genres": unicode(row[4].value),
                 "stack": row[5].value,
                 "missing": 0} for row in chain.from_iterable(self._generate_row(sheet) for sheet in self._generate_sheet(book)))
                        