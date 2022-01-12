# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
import ipywidgets as widgets

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Sep 24, 2021"


def WrapingHBox(*args, **kwargs):
    """Construct a Box widget with similar properties as the normal HBox but with wrapping behavior."""
    box = widgets.Box(*args, **kwargs)
    box.layout.display = "flex"
    box.layout.align_items = "stretch"
    box.layout.flex_flow = "row wrap"
    return box
