# rcedit – programmatic access to Research catalogue web interface
# (c)2021-2024 grrrr.org

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['RCException', 'RCEdit']

import requests
import re
import urllib
from html.parser import HTMLParser
import json
import time
from collections import defaultdict


class RCException(Exception):
    def __init__(self, reason=""):
        self.reason = reason
    def __repr__(self):
        return f'RCException("{self.reason}")'


class RCEdit:
    rcurl = "https://www.researchcatalogue.net"

    def __init__(self, exposition):
        self.session = requests.Session()
        self.exposition = exposition


    def login(self, username, password):
        rtext = self._post("/session/login", data=dict(username=username, password=password))
        if rtext.strip():
            raise RCException("login failed")


    def logout(self):
        self._get("/session/logout")


    def page_list(self, page_name=None, firstonly=False, regexp=False):
        "List pages (aka weaves), optionally filtered"
        
        # TODO: should we return id:(type,name) in _PageLister?
        # this would break backwards compatibility
        
        rtext = self._post("/editor/weaves", data=dict(research=self.exposition))
        pages = self._PageLister()(rtext)
        
        if page_name is None:
            crit = lambda x: True
        else:
            if regexp:
                r = re.compile(page_name)
                crit = lambda x: r.match(x) is not None
            else:
                crit = lambda x: x == page_name
                
        pages = [(pid,pnm) for pid,pnm in pages.items() if crit(pnm)]
            
        if firstonly:
            return pages[0] if len(pages) else None
        else:
            return dict(pages)


    def page_add(self, page_name, page_type='graphical', description=None, **kwargs):
        # kwargs can be 'style' or 'meta' dicts
        data = {
            'research': self.exposition,
            'meta[title][en]': page_name,
            'weave-type': page_type,
        #    'meta[iframe]': '',
        #    'style[marginleft]': 0,
        #    'style[margintop]': 0,
        #    'style[marginright]': 0,
        #    'style[marginbottom]': 0,
        #    'submitbutton': 'submitbutton',
        }
        if description:
            data['meta[description][en]'] = description
        for kk, kv in kwargs.items():
            for k,v in kv.items():
                data[f'{kk}[{k}]'] = v

        page_id = self._post("/weave/add", data=data)
        try:
            int(page_id)
            return page_id
        except ValueError:
            raise RCException("page_add failed")


    def page_remove(self, page_id):
        rtext = self._post("/weave/remove", data=dict(weave=page_id, confirmation='confirmation'))
        if rtext.strip():
            raise RCException("page_remove failed")


    def page_options_get(self, page_id):
        rtext = self._get("/weave/edit", params=dict(weave=page_id))
        return self._ItemData()(rtext)


    def page_options_set(self, page_id, **kwargs):
        """
        In kwargs, we need at least meta[title][en]
        """
        data = dict(
            weave=page_id,
            submitbutton='submitbutton'
        )
        for kk, kv in kwargs.items():
            for k,v in kv.items():
                data[f'{kk}[{k}]'] = v

        rtext = self._post("/weave/edit", data=data)
        if rtext.strip():
            raise RCException("page_options_set failed")

        
    license_options = {
        "all-rights-reserved", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd", "public-domain"        
    }

    
    mediaset_genres = {
        # publication
        'publication', 'paper', 'catalogue', 'article', 'book', 'broadcast', 'cd', 'dvd',
        # event 
        'event', 'exhibition', 'screening', 'concert', 'performance', 'festival', 'seminar', 
        'conference', 'presentation', 'workshop',
        # art object
        'art object', 'installation', 'scenery', 'piece', 'design', 'screenplay', 'sound', 
        'photograph', 'painting', 'scale model', 'digital artwork', 'visualisation', 'illustration', 
        'ceramic', 'print', 'construction', 'drawing', 'video', 'composition', 'movie',
    }


    def mediaset_list(self, mediaset_name=None, firstonly=False, regexp=False):
        "List media sets (aka works), optionally filtered"
        rtext = self._post('/editor/works', data=dict(research=self.exposition))
        mediasets = self._SetLister()(rtext) # {set_id: set_name, ...}

        if mediaset_name is None:
            crit = lambda x: True
        else:
            if regexp:
                r = re.compile(mediaset_name)
                crit = lambda x: r.match(x) is not None
            else:
                crit = lambda x: x == mediaset_name
                
        mediasets = [(msid,msnm) for msid,msnm in mediasets.items() if crit(msnm)]
            
        if firstonly:
            return mediasets[0] if len(mediasets) else None
        else:
            return dict(mediasets)


    def mediaset_find(self, ):
        "Find media set by name"


    def mediaset_add(self, mediaset_name, mediaset_genre, authors, copyright, date=None):
        "Add new media set"

        if mediaset_genre not in self.mediaset_genres:
            raise RCException(f"Mediaset genre '{mediaset_genre}' not valid")
                  
        data = {
            'meta[title][en]': mediaset_name,
            'meta[genre]': mediaset_genre,
            'meta[date]': date if date is not None else time.strftime("%d/%m/%Y"),   # format "dd/mm/yyyy"
            'meta[rcauthors][]': authors,
            'meta[copyrightholder]': copyright,
            'submitbutton': 'submitbutton',
        }
        mediaset_id = self._post("/work/add", data=data)
        return mediaset_id


    def mediaset_remove(self, mediaset_id):
        "Remove media set"
        rtext = self._post('/work/remove', data={'research': self.exposition, 'work[]': mediaset_id, 'confirmation': 'confirmation'})
        if rtext.strip():
            raise RCException("mediaset_remove failed")


    media_types = {'image', 'audio'}


    def media_list(self, mediaset_id=None, media_name=None, media_type=None, firstonly=False, regexp=False):
        # as of 2021-12, one must provide a weave ID
        # for now, we simply take the first page of the exposition
        # since media should be shared among all pages
        pages = list(self.page_list())
        if mediaset_id is None:
            # from simple-media
            rtext = self._post('/simple-media/list', data=dict(research=self.exposition, weave=pages[0]))
            media = self._SimpleMediaLister()(rtext)
        else:
            rtext = self._post('/editor/work-children', data=dict(research=self.exposition, work=mediaset_id, weave=pages[0]))
            lst = json.loads(rtext)
            media = {str(f['id']): (f['tool'], f['title']) for f in lst['files']}

        if media_name is None:
            critn = lambda n: True
        else:
            if regexp:
                r = re.compile(media_name)
                critn = lambda n: r.match(n) is not None
            else:
                critn = lambda n: n == media_name
            
        if media_type is None:
            critt = lambda t: True
        else:
            critt = lambda t: t == media_type
            
        media = [(mid,(mtp,mnm)) for mid,(mtp,mnm) in media.items() if critn(mnm) and critt(mtp)]
        
        if firstonly:
            return media[0] if len(media) else None
        else:
            return dict(media)


    def media_add(self, media_name, copyrightholder, media_type='image', license="cc-by-nc-nd", description='', mediaset_id=None):
        "Add media file to simple-media or set"
                  
        if media_type not in self.media_types:
            raise RCException(f"Media type '{media_type}' not valid")
                  
        if license not in self.license_options:
            raise RCException(f"License '{license}' not valid")
                  
        data = {
            'research': self.exposition,
            media_type+'[mediatype]': media_type,
            media_type+'[name]': media_name,
            media_type+'[copyrightholder]': copyrightholder,
            media_type+'[license]': license,
            media_type+'[description]': description,
#            media_type+'[media_delete]': '',
            media_type+'[submitbutton]': media_type+'[submitbutton]',
            'iframe-submit': 'true',
        }
        files = dict(media=('', '', 'application/octet-stream'))

        if mediaset_id is not None:
            data['work'] = mediaset_id
            url = "/work/upload-file"
            edit = "file/edit"
        else:
            url = "/simple-media/add"
            edit = "simple-media/edit"

        rtext = self._post(url, data=data, files=files)
        m = re.search(r"parent.window.formAction\s*=\s*\'\/?"+edit+r"\?file=(\d+)';", rtext)
        if m is None:
            raise RCException("media_add failed")
        media_id = m.group(1)
        return media_id


    def media_remove(self, media_id, mediaset_id=None):
        if mediaset_id is None:
            # Remove media from exposition
            data = {
                'file[]': media_id,
                'confirmation': 'confirmation',
            }
            rtext = self._post('/simple-media/remove', data=data)
        else:
            # Remove media from media_set
            rtext = self._post('/work/remove-file', data=dict(research=self.exposition, work=mediaset_id, file=media_id, confirmation='confirmation'))
        if rtext.strip():
            raise RCException("media_remove failed")


    def media_upload(self, media_id, filename):
        if filename.endswith('.png'):
            mimetype = 'image/png'
            mediatype = 'image'
        elif filename.endswith('.gif'):
            mimetype = 'image/gif'
            mediatype = 'image'
        elif filename.endswith('.svg'):
            mimetype = 'image/svg+xml'
            mediatype = 'image'
        elif filename.endswith('.tif') or filename.endswith('.tiff'):
            mimetype = 'image/tiff'
            mediatype = 'image'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mimetype = 'image/jpeg'
            mediatype = 'image'
        elif filename.endswith('.mp3'):
            mimetype = 'audio/mpeg'
            mediatype = 'audio'
        elif filename.endswith('.wav'):
            mimetype = 'audio/wave'
            mediatype = 'audio'
        else:
            raise ValueError('File type unknown')
        with open(filename, 'rb') as f:
            data = {
                'file': media_id,
                "submit-async-file": 'false',
                "iframe-submit": 'true',
                mediatype+'[submitbutton]': mediatype+'image[submitbutton]',
            }
            files = dict(media=(filename, f, mimetype))
            self._post("/file/edit", data=data, files=files)


    def item_list(self, page_id, item_name=None, item_type=None, firstonly=False, regexp=False):
        "List items on page (aka weave), optionally filtered"
        rtext = self._post("/editor/content", data=dict(research=self.exposition, weave=page_id))
        items = self._ItemLister()(rtext)

        if item_name is None:
            critn = lambda n: True
        else:
            if regexp:
                r = re.compile(item_name)
                critn = lambda n: r.match(n) is not None
            else:
                critn = lambda n: n == item_name

        if item_type is None:
            critt = lambda t: True
        else:
            critt = lambda t: t == item_type
                
        items = [(itid,(ittp,itnm)) for itid,(ittp,itnm) in items.items() if critn(itnm) and critt(ittp)]
            
        if firstonly:
            return items[0] if len(items) else None
        else:
            return dict(items)


    def item_find(self, page_id, item_name, item_type=None, firstonly=True):
        "Find item by name (either item_name or item_type may be None, indicating 'any')"
        items = [
            iid for iid,(itp,inm) in self.item_list(page_id).items() 
            if (item_name is None or inm == item_name) and (item_type is None or itp == item_type)
        ]
        if firstonly:
            return items[0] if len(items) else None
        else:
            return items


    def item_add(self, page_id, media_id, x, y, w, h=0, tool='picture'):
        "Add item to page (aka weave)"
        data = dict(
            research=self.exposition,
            weave=page_id,
            toolType=tool,
            tool=tool,
            file=media_id,
            left=x, top=y, width=w, height=h,
        )
        rtext = self._post("/item/add", data=data)
        m = re.search(r'data-id="(\d+)"', rtext)
        if m is None:
            raise RCException("item_add failed")
        item_id = m.group(1)
        return item_id


    def item_update(self, item_id, x, y, w, h, r=0):
        "Fast item positioning update"
        data = {
            'research': self.exposition,
            f'item[{item_id}]': item_id,
            f'left[{item_id}]': x,
            f'top[{item_id}]': y,
            f'width[{item_id}]': w,
            f'height[{item_id}]': h,
            f'rotate[{item_id}]': r,
        }
        rtext = self._post('/item/update', data=data)
        if rtext.strip():
            raise RCException("item_update failed")


    def item_lock(self, item_id, lock=True):
        rtext = self._post('/item/update-lock', data={f'lock[{item_id}]': 1 if lock else 0})
        if rtext.strip():
            raise RCException("item_lock failed")


    def item_get(self, item_id):
        rtext = self._get("/item/edit", params=dict(research=self.exposition, item=item_id))
        return self._ItemData()(rtext)


    def item_set(self, item_id, **kwargs):
        """
        In kwargs, we need at least common[title] and style[top,left,width,height,rotate]
        """
        data = dict(
            research=self.exposition, 
            item=item_id,
            submitbutton='submitbutton'
        )
        for kk, kv in kwargs.items():
            for k,v in kv.items():
                data[f'{kk}[{k}]'] = v

        rtext = self._post("/item/edit", data=data)
        if rtext.strip():
            raise RCException("item_set failed")


    def item_remove(self, item_id):
        "Remove item from page (aka weave)"
        rtext = self._post("/item/remove", data={'research': self.exposition, 'item[]': item_id, 'confirmation': 'confirmation'})
        if rtext.strip():
            raise RCException("item_remove failed")


    #### internal methods #####################################################

    class _PageLister(HTMLParser):
        def __call__(self, html):
            self.items = {}
            self.nest_tr = 0
            self.feed(html)
            return self.items

        def handle_starttag(self, tag, attrs):
            if tag == 'tr':
                self.nest_tr += 1
                if self.nest_tr == 1:
                    self.nest_td = 0
                    self.cnt_td = 0
                    attrs = dict(attrs)
                    try:
                        self.item = attrs['data-id']
                    except:
                        pass
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td += 1
                self.cnt_td += 1

        def handle_endtag(self, tag):
            if tag == 'tr':
                self.nest_tr -= 1
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td -= 1

        def handle_data(self, data):
            if self.nest_tr == 1:
                pos = (self.nest_td, self.cnt_td)
                # pos == (1,1): type (graphical, block, iframe)
                # pos == (1,2): title
                # pos == (1,3): date
                if pos == (1,2):
                    self.items[self.item] = data


    class _SetLister(HTMLParser):
        def __call__(self, html):
            self.items = {}
            self.nest_tr = 0
            self.feed(html)
            return self.items

        def handle_starttag(self, tag, attrs):
            if tag == 'tr':
                self.nest_tr += 1
                if self.nest_tr == 1:
                    self.nest_td = 0
                    self.cnt_td = 0
                    attrs = dict(attrs)
                    try:
                        if attrs['class'] == 'work':
                            self.item = attrs['data-id']
                    except:
                        pass
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td += 1
                self.cnt_td += 1

        def handle_endtag(self, tag):
            if tag == 'tr':
                self.nest_tr -= 1
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td -= 1

        def handle_data(self, data):
            if self.nest_tr == 1 and self.nest_td == 1 and self.cnt_td == 2:
                self.items[self.item] = data


    class _SimpleMediaLister(HTMLParser):
        def __call__(self, html):
            self.items = {}
            self.nest_tr = 0
            self.feed(html)
            return self.items

        def handle_starttag(self, tag, attrs):
            if tag == 'tr':
                self.nest_tr += 1
                if self.nest_tr == 1:
                    self.nest_td = 0
                    self.cnt_td = 0
                    attrs = dict(attrs)
#                    print(tag, attrs)
                    try:
                        if 'simple-media' in attrs['class'].split():
                            self.item = attrs['data-id']
                            self.tool = attrs['data-tool']
                    except:
                        pass
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td += 1
                self.cnt_td += 1

        def handle_endtag(self, tag):
            if tag == 'tr':
                self.nest_tr -= 1
            elif tag == 'td' and self.nest_tr == 1:
                self.nest_td -= 1

        def handle_data(self, data):
            if self.nest_tr == 1 and self.nest_td == 1 and self.cnt_td == 2:
                self.items[self.item] = (self.tool, data)


    class _ItemLister(HTMLParser):
        def __call__(self, html):
            self.items = {}
            self.feed(html)
            return self.items

        def handle_starttag(self, tag, attrs):
            if tag == 'div':
                attrs = dict(attrs)
                try:
                    self.items[attrs['data-id']] = (attrs['data-tool'], attrs['data-title'])
                except:
                    pass


    class _ItemData(HTMLParser):
        toolmatch = re.compile(r'edit\s*([^\s]+)\s*tool')
        bracketmatch = re.compile(r'([^\[]+)\[([^\]]+)\]')
        
        def __call__(self, html):
            self.title = None
            self.data = defaultdict(dict)
            self.select = None
            self.textarea = None
            self.feed(html)
            return self.title, self.data

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag =='form':
                try:
                    m = self.toolmatch.match(attrs['title'])
                except KeyError:
                    m = None
                if m is not None:
                    self.title = m.group(1)
            elif tag == 'input':  
                tp = attrs.get('type', 'text')
                m = self.bracketmatch.match(attrs['name'])
                v = None
                if m is not None:
                    if tp != 'checkbox' or "checked" in attrs:
                        v = attrs['value']
                if v is not None:
                    self.data[m.group(1)][m.group(2)] = v
            elif tag == 'select':
                m = self.bracketmatch.match(attrs['name'])
                if m is not None:
                    self.select = (m.group(1),m.group(2))
            elif tag == 'option' and self.select is not None:
                if 'selected' in attrs:
                    self.data[self.select[0]][self.select[1]] = attrs['value']
            elif tag == 'textarea':
                m = self.bracketmatch.match(attrs['name'])
                if m is not None:
                    self.textarea = (m.group(1),m.group(2))
            
        def handle_data(self, data):
            if self.textarea is not None:
                self.data[self.textarea[0]][self.textarea[1]] = data
            
        def handle_endtag(self, tag):
            if tag == 'select':
                self.select = None
            elif tag == 'textarea':
                self.textarea = None


    def _post(self, url, data=None, files=None, headers=None):
        r = self.session.post(f"{self.rcurl}{url}", data=data, files=files, headers=headers)
        self.last_response = r
        if r.status_code != 200:
            raise RCException(f'POST {url} failed with status code {r.status_code}')
        return r.text


    def _get(self, url, params=None):
        r = self.session.get(f"{self.rcurl}{url}", params=params)
        self.last_response = r
        if r.status_code != 200:
            raise RCException(f'GET {url} failed with status code {r.status_code}')
        return r.text
