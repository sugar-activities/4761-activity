# Copyright 2016 Sam Parkinson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import math
import json
import logging
from datetime import date
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import WebKit2

from sugar3.graphics import style
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.style import GRID_CELL_SIZE
from sugar3.activity.activity import launch_bundle
from sugar3.datastore import datastore
from popwindow import PopWindow

from add_window import EntryWidget
from bib_types import WEB_TYPES, ALL_TYPES


HELP_TEXT = _( \
'''This Browse entry has no <i>bookmarks</i>.  You need to bookmark the pages
that you want to add to your bibliography.

Bookmark these pages by opening the Browse journal entry, and clicking
the <i>star</i> icon.  Remember to close Browse before importing it into
Bibliography activity, so that the bookmarks are saved!''')


class BrowseImportWindow(PopWindow):
    '''
    A window that let's users import items from a browse activity

    Args:
        data (dict): JSON decoded browse activity data
        toplevel (Gtk.Window): toplevel window
        jobject: jobject from object chooser
    '''

    save_item = GObject.Signal('save-item', arg_types=[str, str, str])
    try_again = GObject.Signal('try-again', arg_types=[object])

    def __init__(self, data, toplevel, jobject):
        PopWindow.__init__(self, transient_for=toplevel)
        self.props.size = PopWindow.FULLSCREEN
        w, h = PopWindow.FULLSCREEN
        self._toplevel = toplevel
        self._jobject = jobject

        self._links = data.get('shared_links', [])
        if not self._links:
            self._show_howto_copy()
            return

        self._total_links = len(self._links)
        self._entry = None

        self._paned = Gtk.Paned()
        self.add_view(self._paned)
        self._paned.show()

        self._webview = WebKit2.WebView()
        self._paned.add1(self._webview)
        self._webview.set_size_request(w / 2, h)
        self._webview.show()

        self._2box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._paned.add2(self._2box)
        self._2box.show()

        self._combo = Gtk.ComboBoxText()
        for t in WEB_TYPES:
            self._combo.append(t.type, t.name)
        self._combo.set_active(0)
        self._combo.connect('changed', self.__combo_changed_cb)
        self._2box.add(self._combo)
        self._combo.show()

        self.next_link()

        add = ToolButton(icon_name='dialog-ok')
        add.props.tooltip = \
            _('Add This Bibliography Item and Continue to Next Bookmark')
        add.connect('clicked', self.__add_clicked_cb)
        self.props.title_box.insert(add, -2)
        add.show()

    def _show_howto_copy(self):
        self.get_title_box().props.title = _('Learn to Bookmark in Browse')

        l = Gtk.Label()
        l.set_markup('<big>{}</big>'.format(HELP_TEXT))
        self.add_view(l)
        l.show()

        metadata = self._jobject.get_metadata()
        launch = Gtk.Button(
            label=_('Open "%s" in Browse and Add Bookmarks!') % metadata.get('title'))
        self.add_view(launch, fill=False)
        launch.connect('clicked', self.__launch_clicked_cb)
        launch.show()

        self._try_again = Gtk.Button(
            label=_('I added the bookmarks, let\'s try again'))
        self.add_view(self._try_again, fill=False)
        self._try_again.connect('clicked', self.__try_again_clicked_cb)

    def __launch_clicked_cb(self, button):
        launch_bundle(bundle_id='org.laptop.WebActivity',
                      object_id=self._jobject.object_id)
        self._try_again.show()

    def __try_again_clicked_cb(self, button):
        # Need to refresh the jobject, as the file probably changed
        new_jobject = datastore.get(self._jobject.object_id)
        self.try_again.emit(new_jobject)

    def next_link(self):
        '''
        Show the next link from the data to the user
        '''
        if len(self._links) == 0:
            self.destroy()
            return
        self._link = self._links.pop(0)

        label = ('<span bgcolor="#fff" color="#282828" size="x-large"'
                  '>{}/{}</span> {}').format(
            self._total_links - len(self._links),
            self._total_links,
            self._link.get('title', _('Untitled')))
        self.get_title_box().props.title = label

        self._webview.load_uri(self._link.get('url'))

        id_ = self._combo.get_active_id()
        bib_type = ALL_TYPES[id_]
        self._set_entry(bib_type)

    def _set_entry(self, type_):
        if self._entry is not None:
            self._entry.hide()
            self._2box.remove(self._entry)
            self._entry.destroy()

        self._entry = EntryWidget(
            type_,
            self._toplevel,
            timestamp=self._link.get('timestamp'),
            title=self._link.get('title'),
            uri=self._link.get('url'))
        self._2box.pack_start(self._entry, True, True, 0)
        self._entry.show()

    def __add_clicked_cb(self, button):
        self.save_item.emit( *self._entry.get_data())
        self.next_link()

    def __combo_changed_cb(self, combo):
        id_ = combo.get_active_id()
        bib_type = ALL_TYPES[id_]
        self._set_entry(bib_type)
