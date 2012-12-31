from wuvt_ims.models import *

from django.contrib import admin

admin.site.register(Stack)
admin.site.register(Reviewer)
admin.site.register(Label)
admin.site.register(Artist)
admin.site.register(Song)

class SongInline(admin.TabularInline):
    model = Song
    fieldsets = [
        (None, {'fields': ['track_num', 'name', 'fcc', 'suggested']}),
    ]
    extra = 10

class AlbumAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'artist', 'label', 'stack', 'num_discs', 'compilation', 'date_added', 'date_released', 'review', 'genres', 'librarian_note', 'related_albums', 'visible', 'missing', 'needs_librarian_review']}),
    ]
    inlines = [SongInline]

admin.site.register(Album, AlbumAdmin)
