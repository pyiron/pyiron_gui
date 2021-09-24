# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
import functools
import ipywidgets as widgets

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


class _BusyCheck:
    def __init__(self):
        self._busy = False
        self._widget_state = {}
        self.widgets_to_deactivate = tuple([widgets.Button])

    @property
    def busy(self):
        return self._busy

    @busy.setter
    def busy(self, value):
        if value:
            for key, val in self._widgets.items():
                if isinstance(val, self.widgets_to_deactivate):
                    self._widget_state[key] = val.disabled
                    val.disabled = True
        else:
            wid = self._widgets
            for key, val in self._widget_state.items():
                wid[key].disabled = val
        self._busy = value

    @property
    def _widgets(self):
        return widgets.Widget.widgets

    def _busy_check(self, busy=True):
        """Function to disable widget interaction while another update is ongoing."""
        if self.busy and busy:
            print("I am busy right now!")
            return True
        else:
            self.busy = busy

    def _decorator_function(self, function):
        @functools.wraps(function)
        def decorated(*args, **kwargs):
            if self._busy_check():
                return
            try:
                function(*args, **kwargs)
            finally:
                self._busy_check(False)
        return decorated

    def __call__(self):
        return self._decorator_function


busy_check = _BusyCheck()

