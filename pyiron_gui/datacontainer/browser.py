# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import os

import ipywidgets as widgets
from IPython.core.display import display

from pyiron_gui.project.project_browser import DisplayOutputGUI

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Jul 14, 2021"


class DataContainerBrowser:

    """
        DataContainer Browser Widget

        Allows to browse nodes/groups in the DataContainer.
    """
    def __init__(self,
                 data_container,
                 Vbox=None,
                 ):
        """
        DataContainerBrowser to browse a DataContainer.

        Args:
            data_container: A DataContainer to browse.
            Vbox(:class:`ipython.widget.VBox`/None): Widget used to display the browser (Constructed if None).
        """
        self._data_container = data_container
        self._current_data_container = data_container
        self._path = ''
        self._initial_path = self.path
        self._color = {
            "dir": '#9999FF',
            'path': '#DDDDAA',
            'home': '#999999',
            'file_chosen': '#FFBBBB',
            'file': '#DDDDDD',
        }

        if Vbox is None:
            self._box = widgets.VBox()
        else:
            self._box = Vbox
        self._busy = False
        self.output = DisplayOutputGUI(layout=widgets.Layout(width='50%', height='100%'))
        self._clicked_data = []
        self._data = None
        self.pathbox = widgets.HBox(layout=widgets.Layout(width='100%', justify_content='flex-start'))
        self.optionbox = widgets.HBox()
        self.filebox = widgets.VBox(layout=widgets.Layout(width='50%', height='100%', justify_content='flex-start'))
        self.path_string_box = widgets.Text(description="(rel) Path",
                                            layout=widgets.Layout(width='min-content')
                                            )
        self.refresh()

    @property
    def color(self):
        return self._color

    @property
    def box(self):
        return self._box

    @box.setter
    def box(self, Vbox):
        self._box = Vbox
        self.refresh()

    def __copy__(self):
        """Copy of the browser using a new Vbox."""
        new = self.__class__(data_container=self._data_container, Vbox=None)
        return new

    def copy(self):
        """Copy of the browser using a new Vbox."""
        return self.__copy__()

    @property
    def data_container(self):
        return self._current_data_container

    @property
    def path(self):
        """Path within the DataContainer."""
        return self._path

    @property
    def abs_path(self):
        """Path of the DataContainer starting with '/'."""
        return '/' + self._path

    def _busy_check(self, busy=True):
        """Function to disable widget interaction while another update is ongoing."""
        if self._busy and busy:
            return True
        else:
            self._busy = busy

    def _update_files(self):
        self.nodes = self.data_container.list_nodes()
        self.dirs = self.data_container.list_groups()

    def gui(self):
        """Return the VBox containing the browser."""
        self.refresh()
        return self.box

    def refresh(self):
        """Refresh the project browser."""
        self._refresh()
        self._refresh()

    def _refresh(self):
        self.output.clear_output(True)

        self._update_files()
        body = widgets.HBox([self.filebox, self.output.box],
                            layout=widgets.Layout(
                                min_height='100px',
                                max_height='800px'
                            ))
        self.path_string_box = self.path_string_box.__class__(description="(rel) Path", value='')
        self._update_optionbox(self.optionbox)
        self._update_filebox(self.filebox)
        self._update_pathbox(self.pathbox)
        self.box.children = tuple([self.optionbox, self.pathbox, body])

    def _update_optionbox(self, optionbox):

        def click_option_button(b):
            if self._busy_check():
                return
            self._click_option_button(b)
            self._busy_check(False)

        set_path_button = widgets.Button(description='Set Path', tooltip="Sets current path to provided string.")
        set_path_button.on_click(click_option_button)
        children = [set_path_button, self.path_string_box]

        button = widgets.Button(description="Reset selection", layout=widgets.Layout(width='min-content'))
        button.on_click(click_option_button)
        children.append(button)

        optionbox.children = tuple(children)

    def _click_option_button(self, b):
        self.output.clear_output(True)
        with self.output:
            print('')
        if b.description == 'Set Path':
            path = self.abs_path
            if len(self.path_string_box.value) == 0:
                with self.output:
                    print('No path given')
                return
            elif not os.path.isabs(self.path_string_box.value):
                path = path + '/' + self.path_string_box.value
            else:
                path = self.path_string_box.value
            self._update_project(path)
        if b.description == 'Reset selection':
            self._clicked_data = []
            self._data = None
            self._update_filebox(self.filebox)

    @property
    def data(self):
        if self._data is not None:
            return self._data_container[self._data]
        else:
            return None

    @data.setter
    def data(self, value):
        if self._data is not None:
            self._data_container[self._data] = value
            self._clicked_data = []
            self.refresh()
            with self.output:
                print("WARNING: Data changed!")
        else:
            raise RuntimeError("No data selected to change.")

    def _update_project_worker(self, path):
        if path == '/' or path == "":
            self._path = ""
            self._current_data_container = self._data_container
            return
        elif path[0] == '/':
            path = path[1:]
        try:
            new_project = self._data_container[path]
            # Check if the new_project implements list_nodes()
            if 'TYPE' in new_project.list_nodes():
                pass
        except (ValueError, AttributeError, KeyError):
            self.path_string_box = self.path_string_box.__class__(description="(rel) Path", value='')
            with self.output:
                print("No valid path")
            return
        else:
            if new_project is not None:
                self._path = path
                self._current_data_container = new_project

    def _update_project(self, path):
        if isinstance(path, str):
            rel_path = os.path.relpath(path, self.abs_path)
            if rel_path == '.':
                self.refresh()
                return
            self._update_project_worker(path)
        else:
            self._current_data_container = path
            self._path = ''
        self.output.clear_output(True)
        self.refresh()

    def _gen_pathbox_path_list(self):
        """Internal helper function to generate a list of paths from the current path."""
        path_list = list()
        tmppath = self.abs_path
        if tmppath[-1] == '/':
            tmppath = tmppath[:-1]
        tmppath_old = tmppath + '/'
        while tmppath != tmppath_old:
            tmppath_old = tmppath
            [tmppath, _] = os.path.split(tmppath)
            path_list.append(tmppath_old)
        path_list.reverse()
        return path_list

    def _update_pathbox(self, box):

        def on_click(b):
            if self._busy_check():
                return
            self._update_project(b.path)
            self._busy_check(False)

        buttons = []

        # Home button
        button = widgets.Button(icon="home",
                                tooltip='/',
                                layout=widgets.Layout(width='auto'))
        button.style.button_color = self.color['home']
        button.path = self._data_container
        button.on_click(on_click)
        buttons.append(button)

        # Path buttons
        for path in self._gen_pathbox_path_list():
            _, current_dir = os.path.split(path)
            button = widgets.Button(description=current_dir + '/',
                                    tooltip=current_dir,
                                    layout=widgets.Layout(width='auto'))
            button.style.button_color = self.color['path']
            button.path = path
            button.on_click(on_click)
            buttons.append(button)

        box.children = tuple(buttons)

    def _on_click_file(self, filename):
        filepath = os.path.join(self.path, filename)
        self.output.clear_output(True)
        try:
            data = self.data_container[filename]
        except(KeyError, IOError):
            data = None

        self.output.display(data, default_output="None")

        if filepath in self._clicked_data:
            self._data = None
            self._clicked_data.remove(filepath)
        else:
            self._data = filepath
            self._clicked_data = [filepath]

    def _update_filebox(self, filebox):

        # item layout definition
        item_layout = widgets.Layout(width='80%',
                                     height='30px',
                                     min_height='24px',
                                     display='flex',
                                     align_items="center",
                                     justify_content='flex-start')

        def on_click_group(b):
            if self._busy_check():
                return
            path = os.path.join(self.path, b.description)
            self._update_project(path)
            self._busy_check(False)

        def on_click_file(b):
            if self._busy_check():
                return
            self._on_click_file(b.description)
            self._update_filebox(filebox)
            self._busy_check(False)

        def gen_dir_button(dirname):
            button = widgets.Button(description=dirname,
                                    icon="folder",
                                    layout=item_layout)
            button.style.button_color = self.color["dir"]
            button.on_click(on_click_group)
            return button

        def gen_file_button(filename):
            button = widgets.Button(description=filename,
                                    icon="file-o",
                                    layout=item_layout)
            if os.path.join(self.path, filename) in self._clicked_data:
                button.style.button_color = self.color["file_chosen"]
            else:
                button.style.button_color = self.color["file"]
            button.on_click(on_click_file)
            return button

        buttons = [gen_dir_button(name) for name in self.dirs]
        buttons += [gen_file_button(str(name)) for name in self.nodes]

        filebox.children = tuple(buttons)

    def _ipython_display_(self):
        """Function used by Ipython to display the object."""
        display(self.gui())
