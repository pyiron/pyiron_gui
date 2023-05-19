# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
import ipywidgets as widgets
import nbconvert
import nbformat
import numpy as np
import ipydatagrid
import plotly.express as px
from plotly import graph_objects as go

import os
import posixpath

import pandas
from IPython.core.display import display, HTML
from functools import singledispatch
from matplotlib import pyplot as plt

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base import HasGroups, FileDataTemplate, FileData
from pyiron_gui.utils.decorators import clickable

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Sep 30, 2021"


@singledispatch
def PyironWrapper(py_obj, project, rel_path=""):
    return BaseWrapper(py_obj, project, rel_path=rel_path)


@PyironWrapper.register
def _(py_obj: Atoms, project, rel_path=""):
    return AtomsWrapper(py_obj, project, rel_path=rel_path)


@PyironWrapper.register
def _(py_obj: Murnaghan, project, rel_path=""):
    return MurnaghanWrapper(py_obj, project, rel_path=rel_path)


class BaseWrapper(HasGroups):

    """Simple wrapper for pyiron objects which extends for basic pyiron functionality (list_nodes ...)"""

    def __init__(self, pyi_obj, project, rel_path=""):
        self._wrapped_object = pyi_obj
        self._project = project
        self._rel_path = rel_path
        self._name = None

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        if hasattr(self._wrapped_object, "project"):
            return self._wrapped_object.project
        return self._project

    @property
    def path(self):
        if hasattr(self._wrapped_object, "path"):
            return self._wrapped_object.path
        if hasattr(self.project, "path"):
            return posixpath.join(self.project.path, self._rel_path)
        raise AttributeError

    def __getitem__(self, item):
        try:
            return self._wrapped_object[item]
        except (IndexError, KeyError, TypeError):
            rel_path = os.path.relpath(
                posixpath.join(self.path, item), self._project.path
            )
            if rel_path == ".":
                return self._project
            return self._project[rel_path]

    def __getattr__(self, item):
        if item in ["list_nodes", "list_groups"]:
            try:
                return getattr(self._wrapped_object, item)
            except AttributeError:
                return self._empty_list
        return getattr(self._wrapped_object, item)

    def _list_groups(self):
        if hasattr(self._wrapped_object, "list_groups"):
            return self._wrapped_object.list_groups()
        else:
            return []

    def _list_nodes(self):
        if hasattr(self._wrapped_object, "list_nodes"):
            return self._wrapped_object.list_nodes()
        else:
            return []

    def __repr__(self):
        return repr(self._wrapped_object)

    @property
    def gui(self):
        return ObjectWidget(self).gui


class AtomsWrapper(BaseWrapper):
    def __init__(self, pyi_obj, project, rel_path=""):
        super().__init__(pyi_obj, project, rel_path=rel_path)
        self._name = "structure"

    @property
    def gui(self):
        return AtomsWidget(self).gui


class MurnaghanWrapper(BaseWrapper):
    def __init__(self, pyi_obj, project, rel_path=""):
        super().__init__(pyi_obj, project, rel_path=rel_path)
        self._name = "murnaghan"

    @property
    def gui(self):
        return MurnaghanWidget(self).gui


class DisplayOutputGUI:

    """Display various kind of data in an appealing way using a ipywidgets.Output inside an ipywidgets.Vbox
    The behavior is very similar to standard ipywidgets.Output except one has to pass cls.box to get a display.
    """

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

    def display(self, obj, default_output=None, _has_groups_callback=None):
        if isinstance(obj, BaseWrapper):
            self.display(obj.gui, default_output=default_output)
        elif isinstance(obj, tuple(PyironWrapper.registry.keys())[1:]):
            self.display(PyironWrapper(obj, project=None))
        elif isinstance(obj, np.ndarray):
            self.display(NumpyWidget(obj), default_output=default_output)
        elif isinstance(obj, FileDataTemplate):
            self.display(FileDataWidget(obj, _has_groups_callback=_has_groups_callback))
        elif isinstance(obj, HasGroups) and _has_groups_callback is not None:
            _has_groups_callback(obj)
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

    def _ipython_display_(self):
        display(self.box)


class ObjectWidget:
    def __init__(self, obj):
        self._obj = obj
        self._output = widgets.Output()
        self._box = widgets.VBox()

    def refresh(self):
        self._output.clear_output()
        with self._output:
            print(" ")
            # display(self._obj)
        self._box.children = tuple([self._output])

    @property
    def gui(self):
        self.refresh()
        return self._box

    def _ipython_display_(self):
        display(self.gui)


class AtomsWidget(ObjectWidget):
    def __init__(self, atoms_object):
        super().__init__(atoms_object)
        self._ngl_widget = None
        self._apply_button = widgets.Button(description="Apply")
        self._apply_button.on_click(self._on_click_apply_button)
        self._header = widgets.HBox()
        self._options = {
            "particle_size": 1.0,
            "camera": "orthographic",
            "reset_view": False,
            "axes": True,
            "cell": True,
        }
        self._init_option_widgets()

    def _on_click_apply_button(self, b):
        self.refresh()

    def refresh(self):
        self._update_header()
        self._update_box()

    def _update_header(self):
        self._header.children = tuple([self._option_representation, self._apply_button])

    def _update_box(self):
        self._update_ngl_widget()
        self._output.clear_output()
        with self._output:
            display(self._ngl_widget)
        self._box.children = tuple([self._header, self._output])

    def _init_option_widgets(self):
        self._option_widgets = {
            "camera": widgets.Dropdown(
                options=["perspective", "orthographic"],
                value=self._options["camera"],
                layout=widgets.Layout(width="min-content"),
                description_tooltip="Camera mode",
            ),
            "particle_size": widgets.FloatSlider(
                value=self._options["particle_size"],
                min=0.1,
                max=5.0,
                step=0.1,
                readout_format=".1f",
                description="atom size",
                layout=widgets.Layout(width="60%"),
            ),
            "cell": widgets.Checkbox(
                description="cell",
                indent=False,
                value=self._options["cell"],
                description_tooltip="Show cell if checked",
            ),
            "axes": widgets.Checkbox(
                description="axes",
                indent=False,
                value=self._options["axes"],
                description_tooltip="Show axes if checked",
            ),
            "reset_view": widgets.Checkbox(
                description="reset view",
                indent=False,
                value=self._options["reset_view"],
                description_tooltip="Reset view if checked",
            ),
        }
        self.refresh()

    @property
    def _option_representation(self):
        """ipywidet to change the options for the self_representation"""
        widget_list = list(self._option_widgets.values())
        return widgets.VBox(
            [widgets.HBox(widget_list[0:2]), widgets.HBox(widget_list[2:])]
        )

    def _parse_option_widgets(self):
        for key in self._options.keys():
            self._options[key] = self._option_widgets[key].value

    def _update_ngl_widget(self):
        self._parse_option_widgets()
        if self._ngl_widget is not None:
            orient = self._ngl_widget.get_state()["_camera_orientation"]
        else:
            orient = []

        self._ngl_widget = self._obj.plot3d(
            mode="NGLview",
            show_cell=self._options["cell"],
            show_axes=self._options["axes"],
            camera=self._options["camera"],
            spacefill=True,
            particle_size=self._options["particle_size"],
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
            opacity=1.0,
        )
        if not self._options["reset_view"] and len(orient) == 16:
            # len(orient)=16 if set; c.f. pyiron_atomistics.atomistics.structure._visualize._get_flattened_orientation
            self._ngl_widget.control.orient(orient)


class MurnaghanWidget(ObjectWidget):
    def __init__(self, murnaghan_object):
        super().__init__(murnaghan_object)
        self._option_widgets = None
        self._header = widgets.HBox()
        self._apply_button = widgets.Button(description="Apply")
        self._apply_button.on_click(self._on_click_apply_button)
        self._options = {
            "fit_type": self._obj.input["fit_type"],
            "fit_order": 3,  # self._murnaghan_object.input['fit_order']
        }
        self._init_option_widgets()

    def _on_click_apply_button(self, b):
        self.refresh()

    def refresh(self):
        self._update_header()
        self._update_box()

    def _update_header(self):
        self._header.children = tuple([self._option_representation, self._apply_button])

    def _init_option_widgets(self):
        self._option_widgets = {
            "fit_type": widgets.Dropdown(
                value=self._options["fit_type"],
                options=[
                    "polynomial",
                    "birch",
                    "birchmurnaghan",
                    "murnaghan",
                    "pouriertarantola",
                    "vinet",
                ],
                description="Fit type",
                description_tooltip="Type of the energy-volume curve fit.",
            ),
            "fit_order": widgets.IntText(
                value=self._options["fit_order"],
                description="Fit order",
                description_tooltip="Order of the polynomial for 'polynomial' fits, "
                "ignored otherwise",
            ),
        }

        self._on_change_fit_type({"new": self._options["fit_type"]})

        self._option_widgets["fit_type"].observe(
            self._on_change_fit_type, names="value"
        )

    def _on_change_fit_type(self, change):
        if change["new"] != "polynomial":
            self._option_widgets["fit_order"].disabled = True
            self._option_widgets["fit_order"].layout.display = "none"
        else:
            self._option_widgets["fit_order"].disabled = False
            self._option_widgets["fit_order"].layout.display = None

    @property
    def _option_representation(self):
        """ipywidet to change the options for the self_representation"""
        return widgets.VBox(
            [self._option_widgets["fit_type"], self._option_widgets["fit_order"]]
        )

    def _parse_option_widgets(self):
        for key in self._options.keys():
            self._options[key] = self._option_widgets[key].value

    def _update_box(self):
        self._output.clear_output()
        with self._output:
            plt.ioff()
            self._parse_option_widgets()

            if self._options["fit_type"] == "polynomial" and (
                self._obj.input["fit_type"] != "polynomial"
                or self._obj.input["fit_order"] != self._options["fit_order"]
            ):
                self._obj.fit_polynomial(fit_order=self._options["fit_order"])
            elif self._options["fit_type"] == "birchmurnaghan" and (
                self._obj.input["fit_type"] != self._options["fit_type"]
            ):
                self._obj.fit_birch_murnaghan()
            elif self._options["fit_type"] == "murnaghan" and (
                self._obj.input["fit_type"] != self._options["fit_type"]
            ):
                self._obj.fit_murnaghan()
            elif self._options["fit_type"] == "vinet" and (
                self._obj.input["fit_type"] != self._options["fit_type"]
            ):
                self._obj.fit_vinet()
            elif self._obj.input["fit_type"] != self._options["fit_type"]:
                self._obj._fit_eos_general(fittype=self._options["fit_type"])

            self._obj.plot()

        self._box.children = tuple([self._header, self._output])


class FileDataWidget(ObjectWidget):
    def __init__(self, file_data, _has_groups_callback=None, _auto_callback=False):
        super().__init__(file_data)
        self._callback = _has_groups_callback
        self._output = DisplayOutputGUI()
        self.mode = "meta"
        self._show_data_button = widgets.Button(description="Show data")
        self._show_data_button.on_click(self._show_data)
        self._show_metadata_button = widgets.Button(description="Show metadata")
        self._show_metadata_button.on_click(self._show_metadata)
        self._header = widgets.HBox(
            [self._show_metadata_button, self._show_data_button]
        )
        self._show_metadata()
        self._data_ = None
        self._data_has_groups = False
        self._auto_callback = _auto_callback

    def _load_and_callback(self, button: widgets.Button =None):
        if callable(self._callback):
            self._callback(self._data)
        elif button is not None:
            button.disabled = True

    @property
    def _data(self):
        if self._data_ is None:
            self._data_ = self._obj.data
            if isinstance(self._data_, HasGroups):
                self._data_has_groups = True
            if self._data_has_groups and self._auto_callback:
                self._callback(self._data_)
            elif self._data_has_groups:
                load_button = widgets.Button(description="Load job")
                load_button.on_click(self._load_and_callback, True)
                self._header.children = tuple([self._show_metadata_button, self._show_data_button, load_button])
        return self._data_

    @clickable
    def _show_data(self):
        self._output.clear_output()
        self._output.display(self._data)
        self._show_data_button.disabled = True
        self._show_metadata_button.disabled = False

    @clickable
    def _show_metadata(self):
        self._output.clear_output()
        self._output.display(self._obj.metadata)
        self._show_data_button.disabled = False
        self._show_metadata_button.disabled = True

    def refresh(self):
        self._box.children = tuple([self._header, self._output.box])


class NumpyWidget(ObjectWidget):
    def __init__(self, numpy_array):
        super().__init__(numpy_array)
        self._fig = None
        self._ax = None
        self._plot_options = None
        self._init_plot_option_widgets()

        self._header = widgets.HBox()

        self._show_plot_button = widgets.Button(description="Show plot")
        self._show_plot_button.on_click(self._click_replot_button)
        self._show_plot_button.tooltip = "Show plot representation"

        self._replot_button = widgets.Button()
        if self._obj.ndim < 3:
            self._replot_button.description = "Replot"
        else:
            self._replot_button.description = "Apply"
        self._replot_button.on_click(self._click_replot_button)

        self._show_data_button = widgets.Button(description="Show data")
        self._show_data_button.on_click(self._click_show_data_button)
        self._show_data_button.tooltip = "Show data representation"

        self._plot_array()
        self._show_plot()

    def _click_show_data_button(self, b):
        self._show_data_only()

    def _show_data_only(self):
        self._header.children = tuple([self._show_plot_button])
        self._output.clear_output()
        with self._output:
            display(self._obj)
        self.refresh()

    def _click_replot_button(self, b):
        self._plot_array()
        self._show_plot()

    def _show_plot(self):
        if self._obj.ndim >= 3:
            self._header.children = tuple(
                [
                    self._option_representation,
                    widgets.VBox([self._show_data_button, self._replot_button]),
                ]
            )
        else:
            self._header.children = tuple(
                [widgets.HBox([self._show_data_button, self._replot_button])]
            )
        self.refresh()

    def refresh(self):
        self._box.children = tuple([self._header, self._output])

    @property
    def _option_representation(self):
        """Return ipywidget.Vbox to change plot options"""
        box = widgets.VBox()
        if self._obj.ndim >= 3:
            box.children = tuple(
                [
                    widgets.HBox([self._plot_options["dim"]]),
                    widgets.HBox(self._plot_options["idx"]),
                ]
            )
        return box

    def _init_plot_option_widgets(self):
        if self._obj.ndim < 3:
            return
        numpy_array = self._obj
        shape = numpy_array.shape
        fixed_idx_list = []
        dim_widget = widgets.SelectMultiple(
            description="Plot-Dim",
            value=[0, 1],
            options=range(numpy_array.ndim),
            rows=3,
            description_tooltip="Plot dimensions of the array "
            "(exactly 2 choices required)",
        )

        for dim in range(numpy_array.ndim - 2):
            fixed_idx_list.append(
                widgets.IntText(
                    description=f"Fixed index {dim}",
                    value=0,
                    layout=widgets.Layout(width="60%"),
                    description_tooltip=f"Fixed index of the {dim}th not chosen "
                    f"dimension; the shape of the array is {shape}.",
                )
            )
        if numpy_array.ndim == 3:
            fixed_idx_list[0].description = "Fixed index"
            fixed_idx_list[0].description_tooltip = (
                f"Fixed index of the not chosen dimension; the shape of the "
                f"array is {shape}"
            )

        self._plot_options = {"dim": dim_widget, "idx": fixed_idx_list}

    def _plot_array(self):
        plt.ioff()
        val = self._obj
        if self._fig is None:
            self._fig, self._ax = plt.subplots()
        else:
            self._ax.clear()

        if val.ndim == 1:
            self._ax.plot(val)
        elif val.ndim == 2:
            if len(val) == 1:
                self._ax.plot(val[0])
            else:
                self._ax.plot(val)
        elif self._plot_options is None:
            slc = [0 for _ in range(val.ndim)]
            slc[0] = slice(None)
            slc[1] = slice(None)
            self._ax.plot(val[tuple(slc)])
        else:
            if len(self._plot_options["dim"].value) != 2:
                print(f"Error: You need to select exactly two dimensions.")
                return
            slc = [None for i in range(val.ndim)]
            i = 0
            for index in range(val.ndim):
                if index in self._plot_options["dim"].value:
                    slc[index] = slice(None)
                else:
                    slc[index] = self._plot_options["idx"][i].value
                    i += 1
            self._ax.plot(val[tuple(slc)])

        self._ax.relim()
        self._ax.autoscale_view()

        self._output.clear_output()
        with self._output:
            display(self._ax.figure)


class DataExplorer:
    def __init__(self, df, initial_keys=None, debug=True):
        self._df = df.copy()
        self._df.columns = ["".join(index) for index in self._df.columns]
        self._header = widgets.HBox()
        self._body = widgets.VBox()
        self.debug = debug
        self._output = widgets.Output()
        self._box = widgets.VBox([self._header, self._body], width='90%')
        self._column_select = widgets.SelectMultiple(description='columns', options=self.df_keys)
        if initial_keys is not None:
            self._column_select.value = initial_keys
        else:
            self._column_select.value = self.df_keys
        self._column_select.observe(self._change_columns)
        self._init_dataframe(self._df)
        self._init_buttons()
        self._change_columns()
        self._show_df()

    def _init_dataframe(self, df):
        self._interactive_df = ipydatagrid.DataGrid(df)
        self._displayed_df = self._interactive_df.data

    def _refresh_dataframe(self, df):
        self._init_dataframe(df)
        self._update_key_dependent_buttons()
        self._show_df()

    @property
    def df_keys(self):
        return list(self._df.keys())

    @property
    def _displayed_df_keys(self):
        return list(self._displayed_df.keys())

    def _change_columns(self, event=None):
        self._refresh_dataframe(self._df[list(self._column_select.value)])

    def _update_key_dependent_buttons(self, box=None):
        if box is None:
            box = self._key_dependent_box
        self._name_select = widgets.Dropdown(description='Name', options=self._displayed_df_keys)
        self._color_select = widgets.Dropdown(description='Color', options=self._displayed_df_keys)
        if 'T' in self._displayed_df_keys:
            self._color_select.value = 'T'
        self._select = widgets.SelectMultiple(description='plot', tooltip="Choose 3!", options=self._displayed_df_keys)
        wt_pct_keys = [info for info in self._displayed_df_keys if info.startswith('wt.%')]
        if len(wt_pct_keys) >= 3:
            self._select.value = wt_pct_keys[0:3]

        self._info_select = widgets.SelectMultiple(description='info', options=self._displayed_df_keys)
        box.children = tuple([widgets.VBox([self._name_select, self._color_select]), self._select])

    def _init_buttons(self):
        df_button = widgets.Button(description='Data')
        df_button.on_click(self._show_df)
        plot_button = widgets.Button(description='Ternary Plot')
        plot_button.on_click(self._click_plot)
        self._key_dependent_box = widgets.HBox(width='50%')
        self._update_key_dependent_buttons(self._key_dependent_box)

        self._header.children = tuple([widgets.HBox(
                                            [df_button, self._column_select, plot_button,
                                            self._key_dependent_box
                                            ])
                                      ])

    def _show_df(self, _=None):
        self._body.children = tuple([self._interactive_df])

    @property
    def _current_i_df(self):
        return self._interactive_df.get_visible_data()

    def _click_plot(self, _=None):
        #a = px.scatter_ternary(self._current_i_df, a='wt.%Mg', b='wt.%Ca', c='wt.%Al',
        #                       color=self._current_i_df['T'].to_list(),
        #                       #color='T',
        #                       hover_name=self._current_i_df['ID'],
        #                       hover_data=self._current_i_df[['wt.%Fe', 'wt.%C', 'wt.%Ti']])
        if len(self._select.value) != 3:
            self._body.children = tuple([widgets.HTML("Select exactly 3 quantities!")])
            return
        info_keys = [info for info in self._displayed_df_keys if info.startswith('wt.%')]
        a, b, c = self._select.value[0:3]
        try:
            tern = px.scatter_ternary(self._current_i_df, a=a, b=b, c=c,
                                      color=self._current_i_df[self._color_select.value].to_list(),
                                      labels={'color': self._color_select.value},
                                      size=np.ones(len(self._current_i_df)) * 5,
                                      hover_name=self._current_i_df[self._name_select.value],
                                      hover_data=self._current_i_df[info_keys]
                                      )
        except Exception as e:
            error_msg = f"Error occurred: {e.__class__.__name__}({e})"
            if self.debug:
                line_sep = '\n  '
                error_msg += '<pre>'
                error_msg += f"Debug info (suppress with debug=False):" + line_sep
                error_msg += f"Plot columns {a}, {b}, {c}" + line_sep
                error_msg += f"Use column {self._name_select.value} as the name," + line_sep
                error_msg += f"           {self._color_select.value} for the color scheme" + line_sep
                error_msg += f"           {' ,'.join(info_keys)} for additional hover information." + line_sep
                error_msg += f"Pandas frame 'used':" + line_sep
                error_msg += '</pre> '
                error_msg += self._current_i_df[[a, b, c, self._name_select.value, self._color_select.value] + info_keys].to_html()
            self._body.children = tuple([widgets.HTML(error_msg)])
        else:
            self._body.children = tuple([go.FigureWidget(tern)])

    def _ipython_display_(self):
        display(self._box)
