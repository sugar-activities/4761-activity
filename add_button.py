# Copyright 2014 Sam Parkinson
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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from gettext import gettext as _

from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.iconentry import IconEntry, ICON_ENTRY_PRIMARY
from sugar3.graphics import style


class AddToolButton(ToolButton):

    __gsignals__ = {
        'add-type': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self, types):
        ToolButton.__init__(self, 'list-add')
        self.set_tooltip(_('Add Bibliography Entry'))
        
        self.palette_invoker.props.toggle_palette = True
        self.palette_invoker.props.lock_palette = True
        self._p = self.get_palette()

        self._search_box = IconEntry()
        self._search_box.add_clear_button()
        self._search_box.set_icon_from_name(
            ICON_ENTRY_PRIMARY, 'system-search')
        self._search_box.show()

        types_store = Gtk.ListStore(str)
        for i in types:
            types_store.append([i])

        self._filter_model = types_store.filter_new()
        self._filter_model.set_visible_func(self.__model_filter_cb)
        self._search_box.connect('changed',
                                 lambda *args: self._filter_model.refilter())
        self._search_box.connect('activate', self.__search_box_activate_cb)

        treeview = Gtk.TreeView(self._filter_model)
        treeview.props.headers_visible = False
        try:
            treeview.props.activate_on_single_click = True
        except AttributeError:
            pass
        treeview.get_style_context().add_class('add-new-treeview')
        treeview.connect('row-activated', self.__row_clicked_cb)
        treeview.show()

        r = Gtk.CellRendererText()
        c = Gtk.TreeViewColumn(_('Type'), r, text=0)
        treeview.append_column(c)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        sw.props.height_request = 300
        sw.add(treeview)
        sw.show()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add(self._search_box)
        box.add(sw)
        box.show()
        self._p.set_content(box)
        
    def __row_clicked_cb(self, treevieew, path, view_column):
        row = self._filter_model.get_iter(path)
        type_ = self._filter_model.get_value(row, 0)
        self.emit('add-type', type_)
        self._p.popdown()
        
    def __model_filter_cb(self, model, iter, data):
        return self._search_box.get_text().lower() in \
            model.get(iter, 0)[0].lower()

    def __search_box_activate_cb(self, entry):
        row = self._filter_model.get_iter(Gtk.TreePath.new_first())
        type_ = self._filter_model.get_value(row, 0)
        self.emit('add-type', type_)
        self._p.popdown()
