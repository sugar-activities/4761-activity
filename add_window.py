# Copyright 2014-2016 Sam Parkinson
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

from sugar3.graphics import style
from sugar3.graphics.toolbutton import ToolButton
from popwindow import PopWindow


def get_toplevel_size(toplevel):
    # Fixes a big where the window overflows on the XO
    screen = Gdk.Screen.get_default()
    return min(toplevel.get_allocated_width(), screen.width()), \
           min(toplevel.get_allocated_height(), screen.height())


SPECIAL_PLACEHOLDERS = {
    'datenow': lambda: '{:%d %B %Y}'.format(date.today())
}


class EntryWidget(Gtk.EventBox):
    '''
    A widget that lets the user compose a bibliography item, using
    a pre built template/formatter.

    Args:
        bib_type (BibType): the type of item the user will add
        toplevel (Gtk.Window): top level window that this will be added to
        previous_values (list):  Values to use when updating the entry
        timestamp (int): timestamp to use in a website template
        title (str): title to use in a website template
        uri (str): uri to use in a website template
    '''

    def __init__(self, bib_type, toplevel, previous_values=None,
                 timestamp=None, title=None, uri=None):
        Gtk.EventBox.__init__(self)
        self._type = bib_type
        self.get_style_context().add_class('window-event-box')

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(sw)
        sw.show()

        alignment = Gtk.Alignment()
        alignment.set_padding(6, 6, 6, 6)
        sw.add(alignment)
        alignment.show()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        alignment.add(box)
        box.show()
        
        example = Gtk.Label()
        markup = '<b> {} Reference List Example: </b>\n{}'.format(
            self._type.name,
            self._type.format([(SPECIAL_PLACEHOLDERS[i[1:]]() \
                                if i.startswith('*') else i) \
                              for _, i in self._type.items]))
        example.set_markup(markup)
        example.props.wrap = True
        example.props.max_width_chars = \
            (get_toplevel_size(toplevel)[0] / 2) / 18
        box.add(example)
        example.show()
        
        table = Gtk.Table(int(math.ceil(len(self._type.items)/2.0) * 3) - 1,
                          2, True)
        table.props.column_spacing = 6
        box.add(table)
        table.show()

        self._text_entries = []
        for i, v in enumerate(self._type.items):
            text, placeholder = v
            label = Gtk.Label(text)
            entry = Gtk.Entry()

            if placeholder.startswith('*'):
                entry.set_text(SPECIAL_PLACEHOLDERS[placeholder[1:]]())
            else:
                entry.set_placeholder_text(placeholder)
            if placeholder == '*datenow' and timestamp is not None:
               entry.set_text('{:%d %B %Y}'.format(
                    date.fromtimestamp(timestamp)))
            if i == self._type.web_title_index and title is not None:
                entry.set_text(title)
            if i == self._type.web_uri_index and uri is not None:
                entry.set_text(uri)
            if previous_values:
                entry.set_text(previous_values[i])
            self._text_entries.append(entry)

            start = math.floor(i / 2.0) * 3
            col = i % 2
            table.attach(label, col, col + 1, start, start + 1)
            table.attach(entry, col, col + 1, start + 1, start + 2)
            label.show()
            entry.show()
    
    def get_data(self):
        '''
        Returns the state of the entry window as a tuple of:

        * String of markup
        * Type name (`BibType.type`)
        * JSON dump of the values (good for use with `previous_values`)
        '''
        values = []
        for e in self._text_entries:
            values.append(e.get_text())
        result = self._type.format(map(GLib.markup_escape_text, values))
        
        return (result, self._type.type, json.dumps(values))


class EntryWindow(PopWindow):

    __gsignals__ = {
        'save-item': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str))
    }

    def __init__(self, bib_type, toplevel, previous_values=None):
        PopWindow.__init__(self,
                           transient_for=toplevel)
        self.props.size = (int(Gdk.Screen.height() * 0.75),
                           Gdk.Screen.width() / 2)
        self.get_title_box().props.title = _('Edit Bibliography Entry')
        self._type = bib_type

        add = ToolButton(icon_name='dialog-ok')
        add.props.tooltip = _('Add Bibliography Item')
        add.connect('clicked', self.__add_bib_cb)
        self.get_title_box().insert(add, 1)
        add.show()

        self._entry = EntryWidget(bib_type, toplevel, previous_values)
        self.add_view(self._entry)
        self._entry.show()

    def __add_bib_cb(self, button):
        self.emit('save-item', *self._entry.get_data())
