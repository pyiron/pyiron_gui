# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import ipywidgets as widgets
import numpy as np
from IPython.core.display import display
from matplotlib import pyplot as plt

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
