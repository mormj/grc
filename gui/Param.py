"""
Copyright 2007-2011 Free Software Foundation, Inc.
This file is part of GNU Radio

GNU Radio Companion is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

GNU Radio Companion is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import os

from gi.repository import Gtk, Gdk

from . import Colors, Utils, Constants
from .Element import Element

from ..core.Param import Param as _Param


class InputParam(Gtk.HBox):
    """The base class for an input parameter inside the input parameters dialog."""
    expand = False

    def __init__(self, param, changed_callback=None, editing_callback=None):
        Gtk.HBox.__init__(self)

        self.param = param
        self._changed_callback = changed_callback
        self._editing_callback = editing_callback

        self.label = Gtk.Label()
        self.label.set_size_request(150, -1)
        self.label.show()
        self.pack_start(self.label, False, False, 0)

        self.tp = None
        self._have_pending_changes = False

        self.connect('show', self._update_gui)

    def set_color(self, color):
        pass

    def set_tooltip_text(self, text):
        pass

    def get_text(self):
        raise NotImplementedError()

    def _update_gui(self, *args):
        """
        Set the markup, color, tooltip, show/hide.
        """
        self.label.set_markup(self.param.format_label_markup(self._have_pending_changes))

        # fixme: find a non-deprecated way to change colors
        # self.set_color(Colors.PARAM_ENTRY_COLORS.get(
        #     self.param.get_type(), Colors.PARAM_ENTRY_DEFAULT_COLOR)
        # )

        self.set_tooltip_text(self.param.format_tooltip_text())

        if self.param.get_hide() == 'all':
            self.hide()
        else:
            self.show_all()

    def _mark_changed(self, *args):
        """
        Mark this param as modified on change, but validate only on focus-lost
        """
        self._have_pending_changes = True
        self._update_gui()
        if self._editing_callback:
            self._editing_callback(self, None)

    def _apply_change(self, *args):
        """
        Handle a gui change by setting the new param value,
        calling the callback (if applicable), and updating.
        """
        #set the new value
        self.param.set_value(self.get_text())
        #call the callback
        if self._changed_callback:
            self._changed_callback(self, None)
        else:
            self.param.validate()
        #gui update
        self._have_pending_changes = False
        self._update_gui()

    def _handle_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Return and event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            self._apply_change(widget, event)
            return True
        return False

    def apply_pending_changes(self):
        if self._have_pending_changes:
            self._apply_change()


class EntryParam(InputParam):
    """Provide an entry box for strings and numbers."""

    def __init__(self, *args, **kwargs):
        InputParam.__init__(self, *args, **kwargs)
        self._input = Gtk.Entry()
        self._input.set_text(self.param.get_value())
        self._input.connect('changed', self._mark_changed)
        self._input.connect('focus-out-event', self._apply_change)
        self._input.connect('key-press-event', self._handle_key_press)
        self.pack_start(self._input, True, True, 0)

    def get_text(self):
        return self._input.get_text()

    def set_color(self, color):
        self._input.override_background_color(Gtk.StateType.NORMAL, color)

    def set_tooltip_text(self, text):
        self._input.set_tooltip_text(text)


class MultiLineEntryParam(InputParam):
    """Provide an multi-line box for strings."""
    expand = True

    def __init__(self, *args, **kwargs):
        InputParam.__init__(self, *args, **kwargs)
        self._buffer = Gtk.TextBuffer()
        self._buffer.set_text(self.param.get_value())
        self._buffer.connect('changed', self._mark_changed)

        self._view = Gtk.TextView()
        self._view.set_buffer(self._buffer)
        self._view.connect('focus-out-event', self._apply_change)
        self._view.connect('key-press-event', self._handle_key_press)
        # fixme: add border to TextView

        self._sw = Gtk.ScrolledWindow()
        self._sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._sw.add_with_viewport(self._view)

        self.pack_start(self._sw, True, True, True)

    def get_text(self):
        buf = self._buffer
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(),
                            include_hidden_chars=False)
        return text.strip()

    def set_color(self, color):
        self._view.override_background_color(Gtk.StateType.NORMAL, color)

    def set_tooltip_text(self, text):
        self._view.set_tooltip_text(text)


# try:
#     import gtksourceview
#     lang_manager = gtksourceview.SourceLanguagesManager()
#     py_lang = lang_manager.get_language_from_mime_type('text/x-python')
#
#     class PythonEditorParam(InputParam):
#         expand = True
#
#         def __init__(self, *args, **kwargs):
#             InputParam.__init__(self, *args, **kwargs)
#
#             buf = self._buffer = gtksourceview.SourceBuffer()
#             buf.set_language(py_lang)
#             buf.set_highlight(True)
#             buf.set_text(self.param.get_value())
#             buf.connect('changed', self._mark_changed)
#
#             view = self._view = gtksourceview.SourceView(self._buffer)
#             view.connect('focus-out-event', self._apply_change)
#             view.connect('key-press-event', self._handle_key_press)
#             view.set_tabs_width(4)
#             view.set_insert_spaces_instead_of_tabs(True)
#             view.set_auto_indent(True)
#             view.set_border_width(2)
#
#             scroll = Gtk.ScrolledWindow()
#             scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
#             scroll.add_with_viewport(view)
#             self.pack_start(scroll, True)
#
#         def get_text(self):
#             buf = self._buffer
#             return buf.get_text(buf.get_start_iter(),
#                                 buf.get_end_iter()).strip()
#
# except ImportError:
#     print "Package 'gtksourceview' not found. No Syntax highlighting."
#     PythonEditorParam = MultiLineEntryParam

class PythonEditorParam(InputParam):

    def __init__(self, *args, **kwargs):
        InputParam.__init__(self, *args, **kwargs)
        button = self._button = Gtk.Button('Open in Editor')
        button.connect('clicked', self.open_editor)
        self.pack_start(button, True)

    def open_editor(self, widget=None):
        flowgraph = self.param.get_parent().get_parent()
        flowgraph.install_external_editor(self.param)

    def get_text(self):
        pass  # we never update the value from here

    def _apply_change(self, *args):
        pass


class EnumParam(InputParam):
    """Provide an entry box for Enum types with a drop down menu."""

    def __init__(self, *args, **kwargs):
        InputParam.__init__(self, *args, **kwargs)
        self._input = Gtk.ComboBoxText()
        for option in self.param.get_options(): self._input.append_text(option.get_name())
        self._input.set_active(self.param.get_option_keys().index(self.param.get_value()))
        self._input.connect('changed', self._editing_callback)
        self._input.connect('changed', self._apply_change)
        self.pack_start(self._input, False, False, 0)

    def get_text(self):
        return self.param.get_option_keys()[self._input.get_active()]

    def set_tooltip_text(self, text):
        self._input.set_tooltip_text(text)


class EnumEntryParam(InputParam):
    """Provide an entry box and drop down menu for Raw Enum types."""

    def __init__(self, *args, **kwargs):
        InputParam.__init__(self, *args, **kwargs)
        self._input = Gtk.ComboBoxText.new_with_entry()
        for option in self.param.get_options():
            self._input.append_text(option.get_name())

        value = self.param.get_value()
        try:
            active_index = self.param.get_option_keys().index(value)
            self._input.set_active(active_index)
        except ValueError:
            self._input.set_active(-1)
            self._input.get_child().set_text(value)

        self._input.connect('changed', self._apply_change)
        self._input.get_child().connect('changed', self._mark_changed)
        self._input.get_child().connect('focus-out-event', self._apply_change)
        self._input.get_child().connect('key-press-event', self._handle_key_press)
        self.pack_start(self._input, False, False, 0)

    @property
    def has_custom_value(self):
        return self._input.get_active() == -1

    def get_text(self):
        if self._input.get_active() == -1: return self._input.get_child().get_text()
        return self.param.get_option_keys()[self._input.get_active()]

    def set_tooltip_text(self, text):
        if self.has_custom_value:  # custom entry
            self._input.get_child().set_tooltip_text(text)
        else:
            self._input.set_tooltip_text(text)

    def set_color(self, color):
        self._input.get_child().modify_base(
            Gtk.StateType.NORMAL,
            color if not self.has_custom_value else Colors.PARAM_ENTRY_ENUM_CUSTOM_COLOR
        )


class FileParam(EntryParam):
    """Provide an entry box for filename and a button to browse for a file."""

    def __init__(self, *args, **kwargs):
        EntryParam.__init__(self, *args, **kwargs)
        input = Gtk.Button('...')
        input.connect('clicked', self._handle_clicked)
        self.pack_start(input, False, False, 0)

    def _handle_clicked(self, widget=None):
        """
        If the button was clicked, open a file dialog in open/save format.
        Replace the text in the entry with the new filename from the file dialog.
        """
        #get the paths
        file_path = self.param.is_valid() and self.param.get_evaluated() or ''
        (dirname, basename) = os.path.isfile(file_path) and os.path.split(file_path) or (file_path, '')
        # check for qss theme default directory
        if self.param.get_key() == 'qt_qss_theme':
            dirname = os.path.dirname(dirname)  # trim filename
            if not os.path.exists(dirname):
               platform = self.param.get_parent().get_parent().get_parent()
               dirname = os.path.join(platform.config.install_prefix,
                                      '/share/gnuradio/themes')
        if not os.path.exists(dirname):
            dirname = os.getcwd()  # fix bad paths

        #build the dialog
        if self.param.get_type() == 'file_open':
            file_dialog = Gtk.FileChooserDialog('Open a Data File...', None,
                Gtk.FileChooserAction.OPEN, ('gtk-cancel',Gtk.ResponseType.CANCEL,'gtk-open',Gtk.ResponseType.OK))
        elif self.param.get_type() == 'file_save':
            file_dialog = Gtk.FileChooserDialog('Save a Data File...', None,
                Gtk.FileChooserAction.SAVE, ('gtk-cancel',Gtk.ResponseType.CANCEL, 'gtk-save',Gtk.ResponseType.OK))
            file_dialog.set_do_overwrite_confirmation(True)
            file_dialog.set_current_name(basename) #show the current filename
        else:
            raise ValueError("Can't open file chooser dialog for type " + repr(self.param.get_type()))
        file_dialog.set_current_folder(dirname) #current directory
        file_dialog.set_select_multiple(False)
        file_dialog.set_local_only(True)
        if Gtk.ResponseType.OK == file_dialog.run(): #run the dialog
            file_path = file_dialog.get_filename() #get the file path
            self._input.set_text(file_path)
            self._editing_callback()
            self._apply_change()
        file_dialog.destroy()  # destroy the dialog


class Param(Element, _Param):
    """The graphical parameter."""

    def __init__(self, **kwargs):
        Element.__init__(self)
        _Param.__init__(self, **kwargs)

    def get_input(self, *args, **kwargs):
        """
        Get the graphical gtk class to represent this parameter.
        An enum requires and combo parameter.
        A non-enum with options gets a combined entry/combo parameter.
        All others get a standard entry parameter.

        Returns:
            gtk input class
        """
        if self.get_type() in ('file_open', 'file_save'):
            input_widget = FileParam(self, *args, **kwargs)

        elif self.is_enum():
            input_widget = EnumParam(self, *args, **kwargs)

        elif self.get_options():
            input_widget = EnumEntryParam(self, *args, **kwargs)

        elif self.get_type() == '_multiline':
            input_widget = MultiLineEntryParam(self, *args, **kwargs)

        elif self.get_type() == '_multiline_python_external':
            input_widget = PythonEditorParam(self, *args, **kwargs)

        else:
            input_widget = EntryParam(self, *args, **kwargs)

        return input_widget

    def format_label_markup(self, have_pending_changes=False):
        block = self.get_parent()
        has_callback = \
            hasattr(block, 'get_callbacks') and \
            any(self.get_key() in callback for callback in block._callbacks)

        return '<span underline="{line}" foreground="{color}" font_desc="Sans 9">{label}</span>'.format(
            line='low' if has_callback else 'none',
            color='blue' if have_pending_changes else
            'black' if self.is_valid() else
            'red',
            label=Utils.encode(self.get_name())
        )

    def format_tooltip_text(self):
        errors = self.get_error_messages()
        tooltip_lines = ['Key: ' + self.get_key(), 'Type: ' + self.get_type()]
        if self.is_valid():
            value = str(self.get_evaluated())
            if len(value) > 100:
                value = '{}...{}'.format(value[:50], value[-50:])
            tooltip_lines.append('Value: ' + value)
        elif len(errors) == 1:
            tooltip_lines.append('Error: ' + errors[0])
        elif len(errors) > 1:
            tooltip_lines.append('Error:')
            tooltip_lines.extend(' * ' + msg for msg in errors)
        return '\n'.join(tooltip_lines)

    def format_block_surface_markup(self):
        """
        Get the markup for this param.

        Returns:
            a pango markup string
        """
        return '<span foreground="{color}" font_desc="{font}"><b>{label}:</b> {value}</span>'.format(
            color='black' if self.is_valid() else 'red', font=Constants.PARAM_FONT,
            label=Utils.encode(self.get_name()), value=Utils.encode(repr(self).replace('\n', ' '))
        )
