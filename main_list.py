import json
import logging
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject

from sugar3.graphics.palette import Palette
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.palettemenu import PaletteMenuItem
try:
    NEW_INVOKER = True
    from sugar3.graphics.palette import TreeViewInvoker
    from sugar3.graphics.scrollingdetector import ScrollingDetector
except ImportError:
    NEW_INVOKER = False
    from sugar3.graphics.palette import CellRendererInvoker


class MainList(Gtk.TreeView):
    '''
    Manages the list of references.  The list is made from:

        Bib. text (str)
        Bib. type (str)
        Bib. data (list[str] as json str)
    '''

    __gtype_name__ = 'BibliographyMainList'
    __gsignals__ = {
        'deleted-row': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str)),
        'edit-row': (GObject.SIGNAL_RUN_FIRST, None, (str, str))
    }

    COLUMN_TEXT = 0
    COLUMN_TYPE = 1
    COLUMN_DATA = 2

    def __init__(self, scrolled_window, collab):
        self._collab = collab
        self._store = Gtk.ListStore(str, str, str)

        self._sort = Gtk.TreeModelSort(self._store)
        self._store.set_sort_column_id(self.COLUMN_TEXT,
                                       Gtk.SortType.ASCENDING)
        Gtk.TreeView.__init__(self, self._sort)

        self.props.headers_visible = False
        self.props.rules_hint = True

        renderer = TextRenderer(self)
        column = Gtk.TreeViewColumn('Bibliography', renderer, markup=0)
        column.props.max_width = 0
        self.append_column(column)

        if NEW_INVOKER:
            self._invoker = TreeViewInvoker()
            self._invoker.attach_treeview(self)

            scrolld = ScrollingDetector(scrolled_window)
            scrolld.connect('scroll-start', self.__scroll_start_cb)
            scrolld.connect('scroll-end', self.__scroll_end_cb)

        self._editing_iter = None

    def __scroll_start_cb(self, event):
        self._invoker.detach()

    def __scroll_end_cb(self, event):
        self._invoker.attach_treeview(self)

    def add(self, text, type_, data):
        self._store.append([text, type_, data])

    def all(self):
        return [row[:] for row in self._store]

    def load_json(self, list_):
        # Only add entries we don't already have, eg resuming shared activity
        for row in list_:
            if row not in self._store:
                self._store.append(row)
            else:
                # Somebody added this offline
                self._collab.post(dict(
                    action='add_item',
                    args=row
                ))

    def edit(self, row):
        self._editing_iter = None
        for i in self._store:
            if list(i) == row:
                self._editing_iter = i.iter
                break
        if self._editing_iter is None:
            logging.error('Trying to edit a row that does not exist')
            logging.error('Row: {}'.format(self._editing_iter))
            return

        self.emit('edit-row', row[self.COLUMN_TYPE], row[self.COLUMN_DATA])

    def edited_row_cb(self, window, *row):
        if self._editing_iter is None:
            logging.error('No editing_iter when edited_row_cb is called')
            return

        self._store.set(self._editing_iter, range(3), row)
	self._collab.post(dict(
            action='edit_item',
            path=self._store.get_string_from_iter(self._editing_iter),
            args=row
        ))

        window.hide()
        window.get_parent().remove(window)

    def edited_via_collab(self, path, row):
        i = self._store.get_iter_from_string(path)
        self._store.set(i, range(3), row)

    def delete(self, delete_row):
        for row in self._store:
            if list(row) == delete_row:
                self._store.remove(row.iter)
                self.emit('deleted-row', *delete_row)
                return

    def create_palette(self, path, column):
        row = list(self.get_model()[path])
        return ItemPalette(row, self, self._collab)


class TextRenderer(Gtk.CellRendererText):

    def __init__(self, tree_view):
        Gtk.CellRendererText.__init__(self)
        self._tree_view = tree_view
        screen = Gdk.Screen.get_default()

        self.props.font_desc = Pango.FontDescription('sans 16')
        self.props.wrap_width = screen.get_width()
        self.props.wrap_mode = Pango.WrapMode.WORD_CHAR

        if not NEW_INVOKER:
            self._invoker = CellRendererInvoker()
            self._invoker.attach_cell_renderer(tree_view, self)

    def create_palette(self):
        model = self._tree_view.get_model()
        row = list(model[self._invoker.path])
        return ItemPalette(row, self._tree_view)

class ItemPalette(Palette):

    def __init__(self, row, tree_view, collab):
        Palette.__init__(self, primary_text=_(row[MainList.COLUMN_TYPE]))
        self._collab = collab
        self._row = row
        self._tree_view = tree_view

        box = PaletteMenuBox()
        self.set_content(box)
        box.show()

        menu_item = PaletteMenuItem(_('Edit'), icon_name='toolbar-edit')
        menu_item.connect('activate', lambda *args: tree_view.edit(row))
        box.append_item(menu_item)
        menu_item.show()

        menu_item = PaletteMenuItem(_('Delete'), icon_name='edit-delete')
        menu_item.connect('activate', self.__delete_cb) 
        box.append_item(menu_item)
        menu_item.show()

    def __delete_cb(self, *args):
        self._tree_view.delete(self._row)
        self._collab.post(dict(
            action='delete_row',
            args=self._row
        ))
