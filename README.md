rcedit – Programmatic access to Research Catalogue web interface
================================================================

Important note:
---------------

The Research Catalogue (RC) API is not published and its protocol is not frozen!
Therefore, this Python module targets the API at the time of its creation. Nevertheless, it can work as a point of departure to interact with future API versions.


Quick tour:
-----------

The `RCEdit` class provides access to many features of an RC exposition.

```
# Import editor class from rcedit module using
from rcedit import RCEdit

# create RCEdit instance with exposition ID as argument
rc = RCEdit(1234567)
# log in using RC credentials
rc.login(username='my@email.com', password='goodpassword')

# list all pages in exposition (weaves in RC jargon)
pages = rc.page_list()
print("Pages:", pages)
# will print a dict of {page_id: page_name, ...}

# list pages filtered by a regular expression
pages = rc.page_list(r"Page [123]", regexp=True)
print("Pages:", pages)

# add new page (aka weave) to exposition
# page_id = rc.page_add(page_name, description='all about my page')

# remove page
# rc.page_remove(page_id)

# Get page options
rc.page_options_get(page_name)

# list all media sets (shared among expositions)
mediasets = rc.mediaset_list()
print("Media sets:", mediasets)
# will print a dict of {mediaset_id: mediaset_name, ...}

# add media set
mediaset_id = rc.mediaset_add(mediaset_name, mediaset_genre, authors, copyright)

# remove media set (and contained media items!)
# will only work if media items are not used in an exposition
rc.mediaset_remove(mediaset_id)

# list media
# if mediaset_id is None (or omitted): list simple media (in an exposition)
# if mediaset_id is given: list media contained in a media set
media = rc.media_list(mediaset_id)
print(f"Media in set {mediaset_id}:", media)
# will print a dict of {media_id: (media_type, media_name), ...}

# add media (without actual data contents)
# if mediaset_id is None (or omitted): add to simple media
# if mediaset_id is given: add to media set
media_id = rc.media_add(name, copyrightholder, media_type, license, mediaset_id)

# upload media contents
rc.media_upload(media_id, filename)

# remove media
# if mediaset_id is None (or omitted): remove form simple media
# if mediaset_id is given: remove from media set
# will only work if media item is not used in an exposition
rc.media_remove(self, media_id, mediaset_id)

# list items on a page
items = rc.item_list(page_id)
print(f"Items on page {page_id}:", items)
# will print a dict of {item_id: (item_type, item_name), ...}

# add media item to a page 
# 'tool' refers to the media type: this could be deduced from the media item (but it is slow)
item_id = rc.item_add(page_id, media_id, x, y, w, h, tool)

# remove item from a page
rc.item_remove(item_id)

# get item parameters
item = rc.item_get(item_id)
# will print a tuple
# (item_type, {
#	'common': {'title', title}},
#	'style': {'left', x}, {'top', y}, {'width', w}, {'height', h}, ...},
#	'options': { ... }
#	})
# options are specific to the item type

# set item parameters
# the key word arguments can be
# common = {'title': title},
# style = {...},
# options = {...},
rc.item_set(item_id, **kwargs)

# fast item update (only positioning)
# either parameter can be omitted
rc.item_update(item_id, x, y, w, h, r)

# lock/unlock item
# lock if 'lock' is nonzero, else unlock
rc.item_lock(item_id, lock)
```

