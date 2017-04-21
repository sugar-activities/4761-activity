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

import os
import time
import json
import logging
from gettext import gettext as _

import dbus
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

from sugar3.activity import activity
from sugar3.datastore import datastore
from sugar3.graphics.alert import Alert
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics import style
from sugar3.graphics.icon import Icon

from sugar3.datastore import datastore
from sugar3.graphics.objectchooser import ObjectChooser
from sugar3.graphics.objectchooser import FILTER_TYPE_ACTIVITY

try:
    from sugar3.activity.activity import get_bundle, launch_bundle
except ImportError:
    get_bundle = lambda **kwargs: None

try:
    from sugar3.presence.wrapper import CollabWrapper
    logging.error('USING SUGAR COLLAB WRAPPER!')
except ImportError:
    from textchannelwrapper import CollabWrapper

from add_button import AddToolButton
from add_window import EntryWindow
from browsewindow import BrowseImportWindow
from bib_types import ALL_TYPES, ALL_TYPE_NAMES
from main_list import MainList


class BibliographyActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self._has_read_file = False
        self._collab = CollabWrapper(self)
        self._collab.message.connect(self.__message_cb)

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider.get_default()
        css_provider.load_from_path('style.css')
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)

        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        html = ToolButton('export-as-html')
        html.set_tooltip(_('Save as HTML'))
        html.connect('clicked', self.__export_as_html_cb)
        activity_button.props.page.insert(html, -1)
        html.show()

        abiword = ToolButton('export-as-abiword')
        abiword.set_tooltip(_('Save as a Write document'))
        abiword.connect('clicked', self.__export_as_abiword_cb)
        activity_button.props.page.insert(abiword, -1)
        abiword.show()

        add_button = AddToolButton(ALL_TYPE_NAMES)
        add_button.connect('add-type', self.__add_type_cb)
        toolbar_box.toolbar.insert(add_button, -1)
        add_button.show()

        browse = ToolButton('import-browse')
        browse.set_tooltip(_('Add Web Pages from Browse Entry'))
        browse.connect('clicked', self.__import_from_browse_cb)
        toolbar_box.toolbar.insert(browse, -1)
        browse.show()
   
        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        self._main_sw = Gtk.ScrolledWindow()
        self._main_sw.set_policy(Gtk.PolicyType.NEVER,
                                 Gtk.PolicyType.ALWAYS)
        self._main_sw.connect('key-press-event',
                              self.__key_press_event_cb)

        self._main_list = MainList(self._main_sw, self._collab)
        self._main_list.connect('edit-row', self.__edit_row_cb)
        self._main_list.connect('deleted-row', self.__deleted_row_cb)
        self._main_sw.add(self._main_list)
        self._main_list.show()

        self._empty_message = EmptyMessage()

        self.set_canvas(self._empty_message)
        self._empty_message.show()

        self._collab.setup()

    def add_item(self, text, type_, data):
        self._empty_message.hide()
        self.set_canvas(self._main_sw)
        self._main_sw.show()
        self._main_list.show()
        self._main_list.add(text, type_, data)

    def __message_cb(self, collab, buddy, msg):
        action = msg.get('action')
        if action is None:
            return

        args = msg.get('args')
        if action == 'add_item':
            self.add_item(*args)
        elif action == 'delete_row':
            self._main_list.delete(args)
        elif action == 'edit_item':
            self._main_list.edited_via_collab(msg.get('path'), args)
        else:
            logging.error('Got message that is weird %r', msg)

    def __add_type_cb(self, add_button, type_):
        window = EntryWindow(ALL_TYPES[type_], self)
        window.connect('save-item', self.__save_item_cb)
        window.show()
    
    def __save_item_cb(self, window, *args):
        self.add_item(*args)
        window.hide()
        self._collab.post(dict(
            action='add_item',
            args=args
        ))
        window.destroy()

    def __import_from_browse_cb(self, button):
        chooser = ObjectChooser(parent=self,
                                what_filter='org.laptop.WebActivity',
                                filter_type=FILTER_TYPE_ACTIVITY)
        result = chooser.run()

        if result == Gtk.ResponseType.ACCEPT:
            logging.debug('ObjectChooser: %r' % chooser.get_selected_object())
            jobject = chooser.get_selected_object()
            self._load_browse(jobject)

        chooser.destroy()
        del chooser

    def __try_again_cb(self, window, jobject):
        window.hide()
        window.destroy()
        self._load_browse(jobject)

    def _load_browse(self, jobject):
        if jobject and jobject.file_path:
            with open(jobject.file_path) as f:
                data = json.load(f)
            window = BrowseImportWindow(data, self, jobject)
            window.connect('save-item', self.__save_item_importer_cb)
            window.connect('try-again', self.__try_again_cb)
            window.show()

    def __save_item_importer_cb(self, window, *args):
        self.add_item(*args)
        self._collab.post(dict(
            action='add_item',
            args=args
        ))

    def __edit_row_cb(self, tree_view, type_, json_string):
        previous_values = json.loads(json_string)
        window = EntryWindow(ALL_TYPES[type_], self, previous_values)
        window.connect('save-item', tree_view.edited_row_cb)
        window.show()

    def __deleted_row_cb(self, tree_view, *row):
        if len(tree_view.get_model()) == 0:
            self._main_list.hide()
            self.set_canvas(self._empty_message)
            self._empty_message.show()

    def __key_press_event_cb(self, scrolled_window, event):
        keyname = Gdk.keyval_name(event.keyval)

        vadjustment = scrolled_window.props.vadjustment
        if keyname == 'Up':
            if vadjustment.props.value > vadjustment.props.lower:
                vadjustment.props.value -= vadjustment.props.step_increment
        elif keyname == 'Down':
            max_value = vadjustment.props.upper - vadjustment.props.page_size
            if vadjustment.props.value < max_value:
                vadjustment.props.value = min(
                    vadjustment.props.value + vadjustment.props.step_increment,
                    max_value)
        else:
            return False

    def __export_as_html_cb(self, button):
        jobject = datastore.create()
        jobject.metadata['title'] = \
            _('{} as HTML').format(self.metadata['title'])
        jobject.metadata['mime_type'] = 'text/html'
        preview = self.get_preview()
        if preview is not None:
            jobject.metadata['preview'] = dbus.ByteArray(preview)

        # write out the document contents in the requested format
        path = os.path.join(self.get_activity_root(),
                            'instance', str(time.time()))
        with open(path, 'w') as f:
            f.write('''<html>
                         <head>
                           <title>{title}</title>
                         </head>

                         <body>
                           <h1>{title}</h1>
                    '''.format(title=jobject.metadata['title']))
            for item in self._main_list.all():
                f.write('<p>{}</p>'.format(
                    item[self._main_list.COLUMN_TEXT]))
            f.write('''
                         </body>
                       </html>
                    ''')
        jobject.file_path = path

        datastore.write(jobject, transfer_ownership=True)
        self._journal_alert(jobject.object_id, _('Success'), _('Your'
                            ' Bibliography was saved to the journal as HTML'))
        jobject.destroy()
        del jobject

    def __export_as_abiword_cb(self, button):
        jobject = datastore.create()
        jobject.metadata['title'] = \
            _('{} as Write document').format(self.metadata['title'])
        jobject.metadata['mime_type'] = 'application/x-abiword'
        preview = self.get_preview()
        if preview is not None:
            jobject.metadata['preview'] = dbus.ByteArray(preview)

        path = os.path.join(self.get_activity_root(),
                            'instance', str(time.time()))
        with open(path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<abiword>\n'
                    '<section>')
            entries = []
            for item in self._main_list.all():
                markup = item[self._main_list.COLUMN_TEXT]
                abiword = '<p><c>{}</c></p>'.format(markup) \
                    .replace('<b>', '<c props="font-weight:bold">') \
                    .replace('<i>', '<c props="font-style:italic;'
                             ' font-weight:normal">') \
                    .replace('</b>', '</c>').replace('</i>', '</c>')
                entries.append(abiword)
            f.write('\n<p><c></c></p>\n'.join(entries))
            f.write('</section>\n</abiword>')
        jobject.file_path = path

        datastore.write(jobject, transfer_ownership=True)
        self._journal_alert(jobject.object_id, _('Success'), _('Your'
                            ' Bibliography was saved to the journal as a Write'
                            ' document'))
        jobject.destroy()
        del jobject

    def _journal_alert(self, object_id, title, msg):
        alert = Alert()
        alert.props.title = title
        alert.props.msg = msg

        bundle = get_bundle(object_id=object_id)
        if bundle is not None:
            alert.add_button(Gtk.ResponseType.ACCEPT,
                             _('Open with {}').format(bundle.get_name()),
                             Icon(file=bundle.get_icon()))
        else:
            alert.add_button(Gtk.ResponseType.APPLY,
                             _('Show in Journal'),
                             Icon(icon_name='zoom-activity'))
        alert.add_button(Gtk.ResponseType.OK, _('Ok'),
                         Icon(icon_name='dialog-ok'))

        # Remove other alerts
        for alert in self._alerts:
            self.remove_alert(alert)

        self.add_alert(alert)
        alert.connect('response', self.__alert_response_cb, object_id)
        alert.show_all()

    def __alert_response_cb(self, alert, response_id, object_id):
        if response_id is Gtk.ResponseType.ACCEPT:
            launch_bundle(object_id=object_id)
        if response_id is Gtk.ResponseType.APPLY:
            activity.show_object_in_journal(object_id)
        self.remove_alert(alert)

    def write_file(self, file_path):
        if self._main_list is None:
            return  # WhataTerribleFailure
        data = self._main_list.all()
        with open(file_path, 'w') as f:
            json.dump(data, f)

        self.metadata['mime_type'] == 'application/json+bib'

    def get_data(self):
        return self._main_list.all()

    def read_file(self, file_path):
        # FIXME: Why does sugar call read_file so many times?
        if self._has_read_file:
            return
        self._has_read_file = True

        with open(file_path) as f:
            l = json.load(f)
        self.set_data(l)

    def set_data(self, l):
        if len(l) > 0:
            self._main_list.load_json(l)
            self._empty_message.hide()
            self.set_canvas(self._main_sw)
            self._main_sw.show()
            self._main_list.show()


class EmptyMessage(Gtk.EventBox):

    def __init__(self):
        Gtk.EventBox.__init__(self)
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        alignment = Gtk.Alignment.new(0.5, 0.5, 0.1, 0.1)
        self.add(alignment)

        box = Gtk.VBox()
        alignment.add(box)

        icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                    icon_name='view-list',
                    stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                    fill_color=style.COLOR_BUTTON_GREY.get_svg())
        box.pack_start(icon, expand=True, fill=False, padding=0)

        label = Gtk.Label()
        color = style.COLOR_BUTTON_GREY.get_html()
        label.set_markup('<span weight="bold" color="%s">%s</span>' % (
            color, _('No Bibliography Entries')))
        box.pack_start(label, expand=True, fill=False, padding=0)

        self.show_all()
