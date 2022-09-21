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
from traitlets import TraitError

from pyiron_base import Project as BaseProject
from pyiron_base import HasGroups
from pyiron_base import FileData
from pyiron_gui.widgets.widgets import WrapingHBox
from pyiron_gui.wrapper.widgets import ObjectWidget, NumpyWidget
from pyiron_gui.wrapper.wrapper import PyironWrapper, BaseWrapper
from pyiron_gui.utils.decorators import busy_check, clickable

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Feb 02, 2021"


class DisplayOutputGUI:

    """Display various kind of data in an appealing way using a ipywidgets.Output inside an ipywidgets.Vbox
    The behavior is very similar to standard ipywidgets.Output except one has to pass cls.box to get a display."""

    def __init__(self, *args, **kwargs):
        self.box = widgets.VBox(*args, **kwargs)
        self.output = widgets.Output(layout=widgets.Layout(width="99%"))
        self._display_obj = None
        self._debug = False
        self.refresh()

    def refresh(self):
        self.box.children = (self.output,)

    def __enter__(self):
        """Use context manager on the widgets.Output widget"""
        self.refresh()
        return self.output.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Use context manager on the widgets.Output widget"""
        self.output.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, item):
        """Forward unknown attributes to the widgets.Output widget"""
        return self.output.__getattribute__(item)

    def clear_output(self, *args, **kwargs):
        self.output.clear_output(*args, **kwargs)
        self.refresh()

    def display(self, obj, default_output=None):
        if isinstance(obj, BaseWrapper):
            self.display(obj.gui, default_output=default_output)
        elif isinstance(obj, tuple(PyironWrapper.registry.keys())[1:]):
            self.display(PyironWrapper(obj, project=None))
        elif isinstance(obj, np.ndarray):
            self.display(NumpyWidget(obj), default_output=default_output)
        else:
            self._display_obj = obj
            self._display(default_output)

    def _display(self, default_output):
        if isinstance(self._display_obj, widgets.DOMWidget):
            self.box.children = (self._display_obj,)
        elif isinstance(self._display_obj, ObjectWidget):
            self.box.children = (self._display_obj.gui,)
        else:
            with self.output:
                if self._display_obj is None and default_output is None:
                    raise TypeError("Given 'obj' is of 'NoneType'.")
                elif self._display_obj is None:
                    print(default_output)
                else:
                    plt.ioff()
                    display(self._output_conv())

    def _output_conv(self):
        obj = self._display_obj

        eol = os.linesep
        if self._debug:
            print("node: ", type(obj))

        if hasattr(obj, "_repr_html_"):
            return obj  # ._repr_html_()
        elif isinstance(obj, FileData):
            return obj.data
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, nbformat.notebooknode.NotebookNode):
            html_exporter = nbconvert.HTMLExporter()
            # html_exporter.template_name = "basic"
            html_exporter.template_name = "classic"
            (html_output, resources) = html_exporter.from_notebook_node(obj)
            return HTML(html_output)
        elif isinstance(obj, dict):
            dic = {"": list(obj.keys()), " ": list(obj.values())}
            return pandas.DataFrame(dic)
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, list) and all([isinstance(el, str) for el in obj]):
            max_length = 2000  # performance of widget above is extremely poor
            if len(obj) < max_length:
                return str("".join(obj))
            else:
                return str(
                    "".join(obj[:max_length])
                    + eol
                    + " .... file too long: skipped ...."
                )
        elif isinstance(obj, list):
            return pandas.DataFrame(obj, columns=["list"])
        elif str(type(obj)).split(".")[0] == "<class 'PIL":
            try:
                data_cp = obj.copy()
                data_cp.thumbnail((800, 800))
                data_cp = data_cp.convert("RGB")
            except:
                data_cp = obj
            return data_cp
        else:
            return obj


class ColorScheme:
    def __init__(self, color_dict=None):
        self._color_traitlet = widgets.Color(None, allow_none=False)
        self._color_dict = {}
        if color_dict is not None:
            self.add_colors(color_dict)

    def __getitem__(self, item):
        if item in self._color_dict:
            return self._color_dict[item]
        else:
            raise KeyError(item)

    def __setitem__(self, key, value):
        if key in self._color_dict:
            self._color_dict[key] = self._validate_color(value)
        else:
            raise ValueError(
                f"Unknown key '{key}'; expected one of {list(self._color_dict.keys())}"
            )

    def add_colors(self, color_dict):
        for key, value in color_dict.items():
            if isinstance(key, str) and key.isidentifier():
                self._color_dict[key] = self._validate_color(value)
            else:
                raise ValueError(f"No valid key '{key}'")

    def _validate_color(self, color):
        try:
            self._color_traitlet.validate(None, color)
        except TraitError as e:
            raise ValueError("Unknown color definition") from e
        else:
            return color

    def keys(self):
        return self._color_dict.keys()

    def values(self):
        return self._color_dict.values()

    def items(self):
        return self._color_dict.items()


class HasGroupsBrowser(HasGroups):
    """Browser for a HasGroups subclass.

    Implements :class:`.HasGroups`.  Groups and nodes are the obtained from the browsed HasGroup-object

    Args:
        project: A :class:`.HasGroups` subclass
        box(widget/None): The ipywidgets.Box in which the Browser is displayed. A new VBox is used if None.

    Attributes:
        project: The currently displayed :class:`.HasGroups` subclass.
        data: The object representing the currently clicked node.

    Methods:
        gui: Returns the Box in which the Browser is displayed
        refresh: Refresh all widgets.
    """

    def __init__(self, project, box=None):
        if box is None or box == "VBox":
            self._box = widgets.VBox()
        elif box == "HBox":
            self._box = widgets.HBox()
        else:
            self._box = box
        self._body_box = widgets.VBox(layout=widgets.Layout(width="100%"))

        if not isinstance(project, HasGroups):
            raise TypeError()
        self._project = project
        self._data = None
        self._history = [project]
        self._history_idx = 0
        self._clicked_nodes = []

        self._file_ext_filter = [".h5", ".db"]
        self._node_filter = ["NAME", "TYPE", "VERSION", "HDF_VERSION"]
        self._show_all = False
        self._show_files = True
        self._fix_position = False
        self._item_layout = widgets.Layout(
            width="min-content",
            height="30px",
            min_height="24px",
            display="flex",
            align_items="center",
            justify_content="flex-start",
        )
        self._control_layout = self._item_layout
        self._color = ColorScheme(
            {
                "control": "#FF0000",
                "group": "#9999FF",
                "file_chosen": "#FFBBBB",
                "file": "#DDDDDD",
            }
        )

    @property
    def data(self):
        return self._data

    def __copy__(self):
        new = self.__class__(project=self.project)
        new._file_ext_filter = self._file_ext_filter
        new._node_filter = self._node_filter
        new._show_all = self._show_all
        new._show_files = self._show_files
        new._fix_position = self._fix_position
        new._history = self._history.copy()
        new._history_idx = self._history_idx
        return new

    def copy(self):
        """Copy of the browser using a new Vbox."""
        return self.__copy__()

    def __getitem__(self, item):
        return self.project[item]

    @property
    def groups(self):
        return self.list_groups()

    def _list_groups(self):
        return self.project.list_groups()

    @property
    def nodes(self):
        return self.list_nodes()

    def _list_nodes(self):
        if self._show_all:
            return self.project.list_nodes()
        else:
            return [
                node
                for node in self.project.list_nodes()
                if node not in self._node_filter
            ]

    @property
    def files(self):
        return self._list_files()

    def _list_files(self):
        if hasattr(self.project, "list_files"):
            if self._show_all:
                return self.project.list_files()
            elif self._node_as_group and self._show_files:
                return [
                    file
                    for file in self.project.list_files()
                    if not file.endswith(tuple(self._file_ext_filter))
                ]
        return []

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, new_project):
        if self._fix_position:
            raise RuntimeError("Not allowed to change the current group.")
        if not isinstance(new_project, HasGroups):
            raise TypeError
        self._set_project(new_project)
        self._history_idx += 1
        self._history = self._history[: self._history_idx]
        self._history.append(self.project)
        self.refresh()

    def _set_project(self, new_project):
        self._project = new_project
        self._data = None
        self._clicked_nodes = []

    @property
    def _node_as_group(self):
        return isinstance(self.project, BaseProject)

    @property
    def color(self):
        return self._color

    def _load_history(self, hist_idx=None):
        if hist_idx is not None:
            self._history_idx = hist_idx
        self._set_project(self._history[self._history_idx])
        self.refresh()

    @clickable
    def _go_back(self):
        self._history_idx -= 1
        self._load_history()

    @clickable
    def _go_forward(self):
        self._history_idx += 1
        self._load_history()

    def _gen_control_buttons(self, layout=None):
        if layout is None:
            layout = self._control_layout
        back_button = widgets.Button(description="", icon="arrow-left", layout=layout)
        back_button.style.button_color = self.color["control"]
        back_button.on_click(self._go_back)
        if self._history_idx == 0:
            back_button.disabled = True

        forward_button = widgets.Button(
            description="", icon="arrow-right", layout=layout
        )
        forward_button.style.button_color = self.color["control"]
        forward_button.on_click(self._go_forward)
        if self._history_idx == len(self._history) - 1:
            forward_button.disabled = True
        return [back_button, forward_button]

    def _update_project(self, group_name):
        self.project = self.project[group_name]

    @busy_check()
    def _on_click_group(self, b):
        self._update_project(b.description)

    def _gen_group_buttons(self, groups=None):
        if groups is None:
            groups = self.groups + self.nodes if self._node_as_group else self.groups
        button_list = []
        for group in groups:
            button = widgets.Button(
                description=str(group), icon="folder", layout=self._item_layout
            )
            button.style.button_color = self.color["group"]
            button.on_click(self._on_click_group)
            if self._fix_position:
                button.disabled = True
            button_list.append(button)
        return button_list

    @busy_check()
    def _on_click_node(self, b):
        self._select_node(b.description)
        self._update_body_box()

    def _select_node(self, node):
        if node in self._clicked_nodes:
            self._clicked_nodes.remove(node)
            self._data = None
        else:
            self._clicked_nodes = [node]
            try:
                self._data = self.project[node]
            except (KeyError, IOError, ValueError):
                self._clicked_nodes.remove(node)
                self._data = None

    def _gen_node_buttons(self, nodes=None):
        if nodes is None:
            nodes = self.files if self._node_as_group else self.files + self.nodes
        node_list = []
        for node in nodes:
            button = widgets.Button(
                description=str(node), icon="file-o", layout=self._item_layout
            )
            if node in self._clicked_nodes:
                button.style.button_color = self.color["file_chosen"]
            else:
                button.style.button_color = self.color["file"]
            button.on_click(self._on_click_node)
            node_list.append(button)
        return node_list

    def _update_body_box(self, body_box=None):
        if body_box is None:
            body_box = self._body_box
        if self._fix_position:
            body_box.children = [
                WrapingHBox(self._gen_group_buttons()),
                WrapingHBox(self._gen_node_buttons()),
            ]
        else:
            body_box.children = [
                widgets.HBox(self._gen_control_buttons()),
                WrapingHBox(self._gen_group_buttons()),
                WrapingHBox(self._gen_node_buttons()),
            ]

    def _gen_box_children(self):
        self._update_body_box()
        return [self._body_box]

    def refresh(self):
        """Refresh the project browser."""
        self._box.children = tuple(self._gen_box_children())

    def gui(self):
        """Return the VBox containing the browser."""
        self.refresh()
        return self._box

    def _ipython_display_(self):
        """Function used by Ipython to display the object."""
        display(self.gui())


class HasGroupsBrowserWithHistoryPath(HasGroupsBrowser):
    """Extends the :class:.HasGroupsBrowser with a path derived from the history.

    Attributes: (only additional ones listed)
        path_list(list): list of clicked groups to get to the current project.
    """

    def __init__(self, project, box=None):
        self._pathbox = widgets.HBox(
            layout=widgets.Layout(width="100%", justify_content="flex-start")
        )
        super().__init__(project=project, box=box)
        self._color.add_colors({"path": "#DDDDAA", "home": "#999999"})
        self._path_list = ["/"]

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, new_project):
        if self._fix_position:
            raise RuntimeError("Not allowed to change the current group.")
        if not isinstance(new_project, HasGroups):
            raise TypeError
        self._project = new_project
        self._history_idx += 1
        self._history = self._history[: self._history_idx]
        self._path_list = self._path_list[: self._history_idx]
        self._history.append(self.project)
        self.refresh()

    def _update_project(self, group_name):
        super()._update_project(group_name)
        self._path_list.append(group_name)
        self.refresh()

    @property
    def path_list(self):
        return self._path_list[: self._history_idx + 1]

    def _update_pathbox(self, box=None):
        @busy_check()
        def on_click(b):
            self._load_history(b.idx)

        if box is None:
            box = self._pathbox

        # Home button
        button = widgets.Button(icon="home", tooltip="/", layout=self._control_layout)
        button.style.button_color = self.color["home"]
        button.idx = 0
        button.on_click(on_click)

        buttons = [button]
        # Path buttons
        for idx, path in enumerate(self.path_list):
            if idx == 0:
                continue
            button = widgets.Button(
                description=path + "/", tooltip=path, layout=self._control_layout
            )
            button.style.button_color = self.color["path"]
            button.idx = idx
            button.on_click(on_click)
            buttons.append(button)

        box.children = tuple(buttons)

    def _update_body_box(self, body_box=None):
        if body_box is None:
            body_box = self._body_box
        body_box.children = [
            WrapingHBox(self._gen_group_buttons()),
            WrapingHBox(self._gen_node_buttons()),
        ]

    def _gen_box_children(self):
        box_children = super()._gen_box_children()
        self._update_pathbox(self._pathbox)
        return [
            widgets.HBox(self._gen_control_buttons() + [self._pathbox])
        ] + box_children


class HasGroupBrowserWithOutput(HasGroupsBrowser):
    """Extends the :class:.HasGroupsBrowser with an output window to display the currently clicked node."""

    def __init__(self, project, box=None):
        self._output = DisplayOutputGUI(
            layout=widgets.Layout(width="50%", height="100%")
        )
        super().__init__(project=project, box=box)
        self._body_box = widgets.VBox(
            layout=widgets.Layout(
                width="50%", height="100%", justify_content="flex-start"
            )
        )

    def _clear_output(self):
        self._output.clear_output(True)
        with self._output:
            print("")

    def _gen_box_children(self):
        if isinstance(self.project, BaseWrapper):
            self._output.display(self.project)

        self._update_body_box(self._body_box)
        body = widgets.HBox(
            [self._body_box, self._output.box],
            layout=widgets.Layout(min_height="100px", max_height="800px"),
        )
        return [body]

    def _update_project_worker(self, rel_path):
        new_project = self.project[rel_path]
        if "TYPE" in new_project.list_nodes():
            try:
                new_project2 = PyironWrapper(
                    new_project.to_object(), self.project, rel_path
                )
            except ValueError:  # to_object() (may?) fail with an ValueError for GenericParameters
                pass
            else:
                new_project = new_project2
                self._output.display(new_project)
        self.project = new_project

    def _update_project(self, group_name):
        self._clear_output()
        self._update_project_worker(group_name)

    def _select_node(self, node):
        self._clear_output()
        super()._select_node(node)
        if node in self._clicked_nodes:
            self._output.display(self.data, default_output=[node])


class ProjectBrowser(HasGroupBrowserWithOutput):

    """
    Project Browser Widget

    Allows to browse files/nodes/groups in the Project based file system.
    Selected files may be received from this ProjectBrowser widget by the data attribute.
    """

    def __init__(self, project, Vbox=None, fix_path=False, show_files=True):
        """
        ProjectBrowser to browse the project file system.

        Args:
            project: Any pyiron project to browse.
            Vbox(:class:`ipython.widget.VBox`/None): Widget used to display the browser (Constructed if None).
            fix_path (bool): If True the path in the file system cannot be changed.
            show_files(bool): If True files (from project.list_files()) are displayed.
        """
        self.pathbox = widgets.HBox(
            layout=widgets.Layout(width="100%", justify_content="flex-start")
        )
        self.optionbox = widgets.HBox()
        self.path_string_box = widgets.Text(
            description="(rel) Path", layout=widgets.Layout(width="min-content")
        )
        super().__init__(project=project, box=Vbox)
        self._item_layout = widgets.Layout(
            width="80%",
            height="30px",
            min_height="24px",
            display="flex",
            align_items="center",
            justify_content="flex-start",
        )
        self._show_files = show_files
        self._initial_project_path = self.path
        self._color.add_colors({"path": "#DDDDAA", "home": "#999999"})

        self._fix_position = fix_path
        self._hide_path = True

    @property
    def _initial_project(self):
        return self._history[0]

    @_initial_project.setter
    def _initial_project(self, project):
        if not isinstance(project, HasGroups):
            raise TypeError
        self._history.insert(0, project)
        self._history_idx += 1

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
        return self._fix_position

    @fix_path.setter
    def fix_path(self, fix_path):
        self._fix_position = fix_path
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
        new = self.__class__(
            project=self.project,
            show_files=self._show_files,
            fix_path=self.fix_path,
            Vbox=None,
        )
        new._hide_path = self._hide_path
        new._initial_project = self._initial_project
        return new

    def copy(self):
        """Copy of the browser using a new Vbox."""
        return self.__copy__()

    @property
    def path(self):
        """Path of the project."""
        return self.project.path

    @property
    def _project_root_path(self):
        try:
            return self.project.root_path
        except AttributeError:
            pass
        try:
            return self.project.project.root_path
        except AttributeError:
            return None

    def _gen_box_children(self):
        body = super()._gen_box_children()
        self.path_string_box = self.path_string_box.__class__(
            description="(rel) Path", value=""
        )
        self._update_optionbox(self.optionbox)
        self._update_pathbox(self.pathbox)
        return [self.optionbox, self.pathbox] + body

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
            self._fix_position = fix_path
        if show_files is not None:
            self._show_files = show_files
        if hide_path is not None:
            self._hide_path = hide_path
        self.refresh()

    def _update_optionbox(self, optionbox):
        set_path_button = widgets.Button(
            description="Set Path", tooltip="Sets current path to provided string."
        )
        set_path_button.on_click(self._set_pathbox_path)
        if self.fix_path:
            set_path_button.disabled = True
            children = [set_path_button, self.path_string_box]
        else:
            children = self._gen_control_buttons() + [
                set_path_button,
                self.path_string_box,
            ]

        button = widgets.Button(
            description="Reset selection", layout=widgets.Layout(width="min-content")
        )
        button.on_click(self._reset_data)
        children.append(button)

        optionbox.children = tuple(children)

    @busy_check()
    @clickable
    def _set_pathbox_path(self):
        if self.fix_path:
            return
        if len(self.path_string_box.value) == 0:
            with self._output:
                print("No path given")
            return
        path = self.path_string_box.value
        self._update_project(path)

    @busy_check()
    @clickable
    def _reset_data(self):
        self._clickedFiles = []
        self._data = None
        self._update_body_box(self._body_box)

    @property
    def data(self):
        if self._data is not None:
            return self._data
        elif isinstance(self.project, BaseWrapper):
            return self.project._wrapped_object
        else:
            return None

    def _update_project_worker(self, rel_path):
        old_project = self.project
        try:
            super(ProjectBrowser, self)._update_project_worker(rel_path)
        except (ValueError, AttributeError):
            self.path_string_box = self.path_string_box.__class__(
                description="(rel) Path", value=""
            )
            with self._output:
                print("No valid path")
            return
        else:
            if self.project is None:
                self.project = old_project

    def _update_project(self, path):
        self._clear_output()
        if isinstance(path, str):
            if os.path.isabs(path):
                path = os.path.relpath(path, self.path)
            if path == ".":
                self.refresh()
                return
            self._update_project_worker(path)
        else:
            self.project = path

    def _gen_pathbox_path_list(self):
        """Internal helper function to generate a list of paths from the current path."""
        path_list = list()
        tmppath = posixpath.abspath(self.path)
        if tmppath[-1] == "/":
            tmppath = tmppath[:-1]
        tmppath_old = tmppath + "/"
        while tmppath != tmppath_old:
            tmppath_old = tmppath
            [tmppath, _] = os.path.split(tmppath)
            path_list.append(tmppath_old)
        path_list.reverse()
        return path_list

    def _update_pathbox(self, box):
        @busy_check()
        def on_click(b):
            self._update_project(b.path)

        buttons = []
        len_root_path = (
            len(self._project_root_path[:-1])
            if self._project_root_path is not None
            else 0
        )

        # Home button
        button = widgets.Button(
            icon="home",
            tooltip=self._initial_project_path,
            layout=widgets.Layout(width="auto"),
        )
        button.style.button_color = self.color["home"]
        button.path = self._initial_project
        if self.fix_path:
            button.disabled = True
        button.on_click(on_click)
        buttons.append(button)

        # Path buttons
        for path in self._gen_pathbox_path_list():
            _, current_dir = os.path.split(path)
            button = widgets.Button(
                description=current_dir + "/",
                tooltip=current_dir,
                layout=widgets.Layout(width="auto"),
            )
            button.style.button_color = self.color["path"]
            button.path = path
            button.on_click(on_click)
            if self.fix_path or len(path) < len_root_path - 1:
                button.disabled = True
                if self._hide_path:
                    button.layout.display = "none"
            buttons.append(button)

        box.children = tuple(buttons)

    def _update_body_box(self, body_box=None):
        if body_box is None:
            body_box = self._body_box
        body_box.children = tuple(self._gen_group_buttons() + self._gen_node_buttons())


class DataContainerGUI(HasGroupsBrowserWithHistoryPath, HasGroupBrowserWithOutput):
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, val):
        if (
            len(self._clicked_nodes) > 0
            and self._clicked_nodes[0] in self.project.list_nodes()
        ):
            node = self._clicked_nodes[0]
            self.project[node] = val
            self._clicked_nodes = []
            self._select_node(node)
        else:
            raise ValueError("No node selected.")
