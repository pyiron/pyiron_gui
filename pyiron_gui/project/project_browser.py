# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import os
import posixpath

import ipywidgets as widgets
import matplotlib.pyplot as plt
import nbconvert
import nbformat
import numpy as np
import pandas
from IPython.core.display import display, HTML

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base import Project as BaseProject
from pyiron_base.generic.filedata import FileData

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Feb 02, 2021"


class PyironWrapper:

    _with_self_representation = {
        "structure": Atoms,
        "murnaghan": Murnaghan
    }

    def __new__(cls, pyi_obj, project, rel_path=""):
        if isinstance(pyi_obj, Atoms):
            return AtomsWrapper(pyi_obj, project, rel_path=rel_path)
        elif isinstance(pyi_obj, Murnaghan):
            return MurnaghanWrapper(pyi_obj, project, rel_path=rel_path)
        else:
            return BaseWrapper(pyi_obj, project, rel_path="")


class BaseWrapper:

    """Simple wrapper for pyiron objects which extends for basic pyiron functionality (list_nodes ...)"""

    def __init__(self, pyi_obj, project, rel_path=""):
        self._wrapped_object = pyi_obj
        self._project = project
        if not hasattr(pyi_obj, 'path'):
            self._path = self._project.path
        self._rel_path = rel_path
        # print("init:" + self.path)
        self._type = None

    @property
    def has_self_representation(self):
        return self._type is not None

    @staticmethod
    def _empty_list():
        return []

    @property
    def name(self):
        return self._type

    @property
    def project(self):
        if hasattr(self._wrapped_object, 'project'):
            return self._wrapped_object.project
        return self._project

    @property
    def path(self):
        if hasattr(self._wrapped_object, 'path'):
            return self._wrapped_object.path
        if hasattr(self.project, 'path'):
            return posixpath.join(self.project.path, self._rel_path)
        raise AttributeError

    def __getitem__(self, item):
        try:
            return self._wrapped_object[item]
        except (IndexError, KeyError, TypeError):
            rel_path = os.path.relpath(posixpath.join(self.path, item), self._project.path)
            if rel_path == '.':
                return self._project
            return self._project[rel_path]

    def __getattr__(self, item):
        if item in ['list_nodes', 'list_groups']:
            try:
                return getattr(self._wrapped_object, item)
            except AttributeError:
                return self._empty_list
        return getattr(self._wrapped_object, item)

    def __repr__(self):
        return repr(self._wrapped_object)

    def self_representation(self):
        """Self representation of the wrapped object if known, else None is returned."""
        return None


class AtomsWrapper(BaseWrapper):
    def __init__(self, pyi_obj, project, rel_path=""):
        super().__init__(pyi_obj, project, rel_path=rel_path)
        self._type = 'structure'
        self._ngl_widget = None
        self._options = {
            'particle_size': 1.0,
            'camera': 'orthographic',
            'reset_view': False,
            'axes': True,
            'cell': True
        }
        self._init_option_widgets()

    def _init_option_widgets(self):
        check_box_layout = widgets.Layout(width='auto', margin='0px 0px 0px -50px')
        self._option_widgets = {
            'camera': widgets.Dropdown(options=['perspective', 'orthographic'], value=self._options['camera'],
                                       layout=widgets.Layout(width='min-content'), toolip='Camera mode'),
            'particle_size': widgets.FloatSlider(value=self._options['particle_size'],
                                                 min=0.1, max=5.0, step=0.1, readout_format='.1f',
                                                 description="atom size",
                                                 layout=widgets.Layout(width='60%')),
            'cell': widgets.Checkbox(description='cell', layout=check_box_layout,
                                     value=self._options['cell'],
                                     tooltip='Show cell if checked'),
            'axes': widgets.Checkbox(description='axes', layout=check_box_layout,
                                     value=self._options['axes'],
                                     tooltip='Show axes if checked'),
            'reset_view': widgets.Checkbox(description='reset view', layout=check_box_layout,
                                           value=self._options['reset_view'], tooltip='Reset view if checked')
        }

    @property
    def option_representation(self):
        """ipywidet to change the options for the self_representation"""
        widget_list = list(self._option_widgets.values())
        return widgets.VBox([
            widgets.HBox(widget_list[0:2]),
            widgets.HBox(widget_list[2:])
        ])

    def _parse_option_widgets(self):
        for key in self._options.keys():
            self._options[key] = self._option_widgets[key].value

    def self_representation(self):
        self._parse_option_widgets()
        if self._ngl_widget is not None:
            orient = self._ngl_widget.get_state()['_camera_orientation']
        else:
            orient = []

        self._ngl_widget = self._wrapped_object.plot3d(
            mode='NGLview',
            show_cell=self._options['cell'],
            show_axes=self._options['axes'],
            camera=self._options['camera'],
            spacefill=True,
            particle_size=self._options['particle_size'],
            select_atoms=None,
            background="white",
            color_scheme=None,
            colors=None,
            scalar_field=None,
            scalar_start=None,
            scalar_end=None,
            scalar_cmap=None,
            vector_field=None,
            vector_color=None,
            magnetic_moments=False,
            view_plane=np.array([0, 0, 1]),
            distance_from_camera=1.0,
            opacity=1.0
        )
        if not self._options['reset_view'] and len(orient) == 16:
            self._ngl_widget.control.orient(orient)
        return self._ngl_widget


class MurnaghanWrapper(BaseWrapper):
    def __init__(self, pyi_obj, project, rel_path=""):
        super().__init__(pyi_obj, project, rel_path=rel_path)
        self._type = 'murnaghan'
        self._option_widgets = None
        self._options = {
            "fit_type": self._wrapped_object.input['fit_type'],
            "fit_order": 3  # self._wrapped_object.input['fit_order']
        }
        self._init_option_widgets()

    def _init_option_widgets(self):
        self._option_widgets = {
            "fit_type": widgets.Dropdown(value=self._options['fit_type'],
                                         options=['polynomial', 'birch', 'birchmurnaghan',
                                                  'murnaghan', 'pouriertarantola', 'vinet'],
                                         description='Fit type',
                                         description_tooltip='Type of the energy-volume curve fit.'),
            "fit_order": widgets.IntText(value=self._options['fit_order'],
                                         description='Fit order',
                                         description_tooltip="Order of the polynomial for 'polynomial' fits, "
                                                             "ignored otherwise")
        }

    @property
    def option_representation(self):
        """ipywidet to change the options for the self_representation"""
        return widgets.VBox([self._option_widgets['fit_type'], self._option_widgets['fit_order']])

    def _parse_option_widgets(self):
        for key in self._options.keys():
            self._options[key] = self._option_widgets[key].value

    def self_representation(self):
        plt.ioff()
        self._parse_option_widgets()

        if self._options['fit_type'] == "polynomial" and (
                self._wrapped_object.input['fit_type'] != "polynomial" or
                self._wrapped_object.input['fit_order'] != self._options['fit_order']
        ):
            self._wrapped_object.fit_polynomial(fit_order=self._options["fit_order"])
        elif self._options['fit_type'] != "polynomial" and (
            self._wrapped_object.input['fit_type'] != self._options['fit_type']
        ):
            self._wrapped_object._fit_eos_general(fittype=self._options['fit_type'])

        self._wrapped_object.plot()


class DisplayOutputGUI:

    """Display various kind of data in an appealing way using a ipywidgets.Output inside an ipywidgets.Vbox
    The behavior is very similar to standard ipywidgets.Output except one has to pass cls.box to get a display."""
    def __init__(self, *args, **kwargs):
        self.box = widgets.VBox(*args, **kwargs)
        self.header = widgets.HBox()
        self.output = widgets.Output(layout=widgets.Layout(width='100%'))
        self._plot_options = None
        self.fig = None
        self.ax = None
        self._debug = False
        self.refresh()

    def refresh(self):
        self.box.children = (self.header, self.output)

    def __enter__(self):
        """Use context manager on the widgets.Output widget"""
        self.header = widgets.HBox()
        return self.output.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Use context manager on the widgets.Output widget"""
        self.output.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, item):
        """Forward unknown attributes to the widgets.Output widget"""
        return self.output.__getattribute__(item)

    def clear_output(self, *args, **kwargs):
        clear_button = kwargs.pop('clear_button', False)
        if clear_button:
            self.header = widgets.HBox()
        self.output.clear_output(*args, **kwargs)
        self.refresh()

    def _click_button(self, b):
        self.output.clear_output()
        if b.description == "Show data":
            b.description = "Show plot"
            b.tooltip = "Display the plotting representation"
            self.header.children = tuple([b])
            self.refresh()
            with self.output:
                display(b.obj)
        elif b.description == "Re-plot":
            with self.output:
                plt.ioff()
                display(self._plot_array(b.obj))
        else:
            self.display(obj=b.obj)

    def _update_header(self, obj):
        childs = []

        button = None
        if isinstance(obj, BaseWrapper) and hasattr(obj, 'option_representation'):
            childs.append(obj.option_representation)
            button = widgets.Button(description="Apply")
        elif isinstance(obj, BaseWrapper) and obj.has_self_representation:
            button = widgets.Button(description="Re-plot " + obj.name)
        elif isinstance(obj, np.ndarray):
            childs.append(self._array_plot_options(obj))
            button = widgets.Button(description="Re-plot")
            button.obj = obj
            button.on_click(self._click_button)
            childs.append(button)

            button = widgets.Button(description="Show data", tooltip="Display the raw data representation.")

        if button is not None:
            button.obj = obj
            button.on_click(self._click_button)
            childs.append(button)

        self.header.children = tuple(childs)

        self.refresh()

    def display(self, obj, default_output=None):
        self._update_header(obj)
        with self.output:
            if obj is None and default_output is None:
                raise TypeError("Given 'obj' is of 'NoneType'.")
            elif obj is None:
                print(default_output)
            elif isinstance(obj, BaseWrapper):
                plt.ioff()
                to_display = obj.self_representation()
                if to_display is not None:
                    display(to_display)
            elif isinstance(obj, np.ndarray):
                plt.ioff()
                display(self._plot_array(obj))
            else:
                plt.ioff()
                display(self._output_conv(obj))

    def _output_conv(self, obj):
        eol = os.linesep
        if self._debug:
            print('node: ', type(obj))

        if hasattr(obj, '_repr_html_'):
            return obj  # ._repr_html_()
        elif isinstance(obj, str):
            return (obj)
        elif isinstance(obj, nbformat.notebooknode.NotebookNode):
            html_exporter = nbconvert.HTMLExporter()
            #html_exporter.template_name = "basic"
            html_exporter.template_name = "classic"
            (html_output, resources) = html_exporter.from_notebook_node(obj)
            return HTML(html_output)
        elif isinstance(obj, dict):
            dic = {'': list(obj.keys()), ' ': list(obj.values())}
            return pandas.DataFrame(dic)
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, list) and all([isinstance(el, str) for el in obj]):
            max_length = 2000  # performance of widget above is extremely poor
            if len(obj) < max_length:
                return str(''.join(obj))
            else:
                return str(''.join(obj[:max_length]) +
                           eol + ' .... file too long: skipped ....')
        elif isinstance(obj, list):
            return pandas.DataFrame(obj, columns=['list'])
        elif str(type(obj)).split('.')[0] == "<class 'PIL":
            try:
                data_cp = obj.copy()
                data_cp.thumbnail((800, 800))
            except:
                data_cp = obj
            return data_cp
        else:
            return obj

    def _array_plot_options(self, numpy_array):
        """Return List of ipywidgets to change plot options"""
        box = widgets.VBox()
        if numpy_array.ndim >= 3:
            self._array_plot_widgets(numpy_array=numpy_array)
            box.children = tuple([
                widgets.HBox([self._plot_options['dim']]),
                widgets.HBox(self._plot_options['idx'])
            ])
        return box

    def _array_plot_widgets(self, numpy_array):
        shape = numpy_array.shape
        fixed_idx_list = []
        dim_widget = widgets.SelectMultiple(description='Plot-Dim', value=[0, 1],
                                            options=range(numpy_array.ndim),
                                            rows=3,
                                            description_tooltip='Plot dimensions of the array '
                                                                '(exactly 2 choices required)')

        for dim in range(numpy_array.ndim-2):
            fixed_idx_list.append(widgets.IntText(description=f'Fixed index {dim}', value=0,
                                                  layout=widgets.Layout(width='60%'),
                                                  description_tooltip=f'Fixed index of the {dim}th not chosen '
                                                                      f'dimension; the shape of the array is {shape}.'))
        if numpy_array.ndim == 3:
            fixed_idx_list[0].description = 'Fixed index'
            fixed_idx_list[0].description_tooltip = f'Fixed index of the not chosen dimension; the shape of the ' \
                                                    f'array is {shape}'

        self._plot_options = {'dim': dim_widget, 'idx': fixed_idx_list}

    def _plot_array(self, val):
        if self.fig is None:
            self.fig, self.ax = plt.subplots()
        else:
            self.ax.clear()

        if val.ndim == 1:
            self.ax.plot(val)
        elif val.ndim == 2:
            if len(val) == 1:
                self.ax.plot(val[0])
            else:
                self.ax.plot(val)
        elif self._plot_options is None:
            slc = [0 for i in range(val.ndim)]
            slc[0] = slice(None)
            slc[1] = slice(None)
            self.ax.plot(val[tuple(slc)])
        else:
            if len(self._plot_options['dim'].value) != 2:
                print(f"Error: You need to select exactly two dimensions.")
                return
            slc = [None for i in range(val.ndim)]
            i = 0
            for index in range(val.ndim):
                if index in self._plot_options['dim'].value:
                    slc[index] = slice(None)
                else:
                    slc[index] = self._plot_options['idx'][i].value
                    i += 1
            self.ax.plot(val[tuple(slc)])

        self.ax.relim()
        self.ax.autoscale_view()
        return self.ax.figure


class ProjectBrowser:

    """
        Project Browser Widget

        Allows to browse files/nodes/groups in the Project based file system.
        Selected files may be received from this ProjectBrowser widget by the data attribute.
    """
    def __init__(self,
                 project,
                 Vbox=None,
                 fix_path=False,
                 show_files=True
                 ):
        """
        ProjectBrowser to browse the project file system.

        Args:
            project: Any pyiron project to browse.
            Vbox(:class:`ipython.widget.VBox`/None): Widget used to display the browser (Constructed if None).
            fix_path (bool): If True the path in the file system cannot be changed.
            show_files(bool): If True files (from project.list_files()) are displayed.
        """
        self._project = project
        self._project_to_obj = None
        self._node_as_dirs = isinstance(self.project, BaseProject)
        self._is_pyiron_obj = 'pyiron' in str(type(self.project))  # ToDo: isinstace(obj, PyironObject)
        self._initial_project = self._project
        self._initial_project_path = self.path
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
        self._fix_path = fix_path
        self._busy = False
        self._show_files = show_files
        self._file_ext_filter = ['.h5', '.db']
        self._hide_path = True
        self.output = DisplayOutputGUI(layout=widgets.Layout(width='50%', height='100%'))
        self._clickedFiles = []
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

    @property
    def fix_path(self):
        return self._fix_path

    @fix_path.setter
    def fix_path(self, fix_path):
        self._fix_path = fix_path
        self.refresh()

    @property
    def show_files(self):
        return self._show_files

    @show_files.setter
    def show_files(self, show_files):
        self._show_files = show_files
        self.refresh()

    @property
    def hide_path(self):
        return self._hide_path

    @hide_path.setter
    def hide_path(self, hide_path):
        self._hide_path = hide_path
        self.refresh()

    def __copy__(self):
        """Copy of the browser using a new Vbox."""
        new = self.__class__(project=self.project, show_files=self._show_files, fix_path=self.fix_path, Vbox=None)
        new._hide_path = self._hide_path
        new._initial_project = self._initial_project
        return new

    def copy(self):
        """Copy of the browser using a new Vbox."""
        return self.__copy__()

    @property
    def project(self):
        return self._project

    @property
    def path(self):
        """Path of the project."""
        return self.project.path

    @property
    def _project_root_path(self):
        try:
            root_path = self.project.root_path
        except AttributeError:
            root_path = self.project.project.root_path
        return root_path

    def _busy_check(self, busy=True):
        """Function to disable widget interaction while another update is ongoing."""
        if self._busy and busy:
            return True
        else:
            self._busy = busy

    def _update_files(self):
        # HDF and S3 project do not have list_files
        node_filter = ['NAME', 'TYPE', 'VERSION', 'HDF_VERSION']
        self.nodes = self.project.list_nodes()
        if self._is_pyiron_obj:
            self.nodes = [node for node in self.nodes if node not in node_filter]
        self.dirs = self.project.list_groups()
        self.files = list()
        if self._show_files:
            try:
                self.files = self.project.list_files()
            except AttributeError:
                pass
        self.files = [file for file in self.files if not file.endswith(tuple(self._file_ext_filter))]

    def gui(self):
        """Return the VBox containing the browser."""
        self.refresh()
        return self.box

    def refresh(self):
        """Refresh the project browser."""
        self.output.clear_output(True)
        if hasattr(self.project, 'self_representation'):
            # print(f"has self_repr! and type of the wrapped obj = {type(self.project._wrapped_object)}")
            self.output.display(self.project)

        self._node_as_dirs = isinstance(self.project, BaseProject)
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

    def configure(self, Vbox=None, fix_path=None, show_files=None, hide_path=None):
        """
        Change configuration of the project browser.

        Args:
            Vbox(:class:`ipython.widget.VBox`/None): Widget used to display the browser.
            fix_path (bool/None): If True the path in the file system cannot be changed.
            show_files(bool/None): If True files (from project.list_files()) are displayed.
            hide_path(bool/None): If True the root_path is omitted in the path.
        """
        if Vbox is not None:
            self._box = Vbox
        if fix_path is not None:
            self._fix_path = fix_path
        if show_files is not None:
            self._show_files = show_files
        if hide_path is not None:
            self._hide_path = hide_path
        self.refresh()

    def _update_optionbox(self, optionbox):

        def click_option_button(b):
            if self._busy_check():
                return
            self._click_option_button(b)
            self._busy_check(False)

        set_path_button = widgets.Button(description='Set Path', tooltip="Sets current path to provided string.")
        set_path_button.on_click(click_option_button)
        if self.fix_path:
            set_path_button.disabled = True
        childs = [set_path_button, self.path_string_box]

        button = widgets.Button(description="Reset selection", layout=widgets.Layout(width='min-content'))
        button.on_click(click_option_button)
        childs.append(button)

        optionbox.children = tuple(childs)

    def _click_option_button(self, b):
        self.output.clear_output(True)
        with self.output:
            print('')
        if b.description == 'Set Path':
            if self.fix_path:
                return
            else:
                path = self.path
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
            self._clickedFiles = []
            self._data = None
            self._update_filebox(self.filebox)

    @property
    def data(self):
        if self._data is not None:
            return self._data
        elif isinstance(self.project, PyironWrapper):
            return self.project._wrapped_object
        else:
            return None

    def _update_project_worker(self, rel_path):
        try:
            new_project = self.project[rel_path]
            # Check if the new_project implements list_nodes()
            if 'TYPE' in new_project.list_nodes():
                try:
                    new_project2 = PyironWrapper(new_project.to_object(), self.project, rel_path)
                except ValueError:  # to_object() (may?) fail with an ValueError for GenericParameters
                    pass
                else:
                    new_project = new_project2
        except (ValueError, AttributeError):
            self.path_string_box = self.path_string_box.__class__(description="(rel) Path", value='')
            with self.output:
                print("No valid path")
            return
        else:
            if new_project is not None:
                self._project = new_project

    def _update_project(self, path):
        if isinstance(path, str):
            rel_path = os.path.relpath(path, self.path)
            if rel_path == '.':
                return
            self._update_project_worker(rel_path)
        else:
            self._project = path
        self.output.clear_output(True, clear_button=True)
        self.refresh()

    def _gen_pathbox_path_list(self):
        """Internal helper function to generate a list of paths from the current path."""
        path_list = list()
        tmppath = os.path.abspath(self.path)
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
        len_root_path = len(self._project_root_path[:-1]) if self._project_root_path is not None else 0

        # Home button
        button = widgets.Button(icon="home",
                                tooltip=self._initial_project_path,
                                layout=widgets.Layout(width='auto'))
        button.style.button_color = self.color['home']
        button.path = self._initial_project
        if self.fix_path:
            button.disabled = True
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
            if self.fix_path or len(path) < len_root_path - 1:
                button.disabled = True
                if self._hide_path:
                    button.layout.display = 'none'
            buttons.append(button)

        box.children = tuple(buttons)

    def _on_click_file(self, filename):
        filepath = os.path.join(self.path, filename)
        self.output.clear_output(True)
        try:
            data = self.project[filename]
        except(KeyError, IOError):
            data = None

        self.output.display(data, default_output=[filename])

        if filepath in self._clickedFiles:
            self._data = None
            self._clickedFiles.remove(filepath)
        else:
            if data is not None:
                self._data = FileData(data=data, file=filename, metadata={"path": filepath})
            # self._clickedFiles.append(filepath)
            self._clickedFiles = [filepath]

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
            if os.path.join(self.path, filename) in self._clickedFiles:
                button.style.button_color = self.color["file_chosen"]
            else:
                button.style.button_color = self.color["file"]
            button.on_click(on_click_file)
            return button

        dirs = self.dirs + self.nodes if self._node_as_dirs else self.dirs
        files = self.files if self._node_as_dirs else self.files + self.nodes

        buttons = [gen_dir_button(name) for name in dirs]
        buttons += [gen_file_button(name) for name in files]

        filebox.children = tuple(buttons)

    def _ipython_display_(self):
        """Function used by Ipython to display the object."""
        display(self.gui())
