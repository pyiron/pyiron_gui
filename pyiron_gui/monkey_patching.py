# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

"""Adding gui functionality to pyiron classes via monkey patching on import of pyiron_gui. """
import warnings
from typing import Union

from pyiron_gui.project.project_browser import (
    ProjectBrowser,
    HasGroupsBrowser,
    DataContainerGUI,
)
from pyiron_base.interfaces.has_groups import HasGroups
from pyiron_base import Project
from pyiron_base import DataContainer

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "July 06, 2022"


def _safe_monkey_patch_method(cls, method_name, func):
    method = getattr(cls, method_name, None)
    if method is not None and (
        method.__module__ != func.__module__ or method.__name__ != func.__name__
    ):
        warnings.warn(
            f"Class {cls.__name__} already has attribute {method_name} - Aborting monkey patch of gui elements."
            f"Method {method} in {method.__module__} with name {method.__name__} planned to replaced by {func} in "
            f"{func.__module__} with name {func.__name__}"
        )
        return False
    else:
        setattr(cls, method_name, func)
        return True


def _safe_monkey_patch_property(cls, property_name, prop):
    method = getattr(cls, property_name, None)
    if method is not None and (
        method.fget.__module__ != prop.fget.__module__
        or method.fget.__name__ != prop.fget.__name__
    ):
        warnings.warn(
            f"Class {cls.__name__} already has attribute {property_name} - Aborting monkey patch of gui elements."
            f"Method {method} in {method.__module__} with name {method.__name__} planned to replaced by {prop} in "
            f"{prop.__module__} with name {prop.__name__}"
        )
        return False
    else:
        setattr(cls, property_name, prop)
        return True


def safe_monkey_patch(
    cls: type,
    func_or_property_name: str,
    func_or_property,
    attr_name: Union[str, None] = None,
    attr_val=None,
):
    attribute_or_bound_method = getattr(cls, func_or_property_name, None)
    if hasattr(cls, func_or_property_name) and type(func_or_property) != type(
        attribute_or_bound_method
    ):
        warnings.warn(
            f"Class {cls.__name__} already has attribute {func_or_property_name} - Aborting monkey patch "
            f"of gui elements. type(attribute_or_bound_method) = {type(attribute_or_bound_method)} "
            f"{attribute_or_bound_method}, type(func_or_property) = {type(func_or_property)}."
        )
        return

    if callable(func_or_property):
        success = _safe_monkey_patch_method(
            cls, func_or_property_name, func_or_property
        )
        if success and attr_name is not None:
            setattr(cls, attr_name, attr_val)
    elif isinstance(func_or_property, property):
        success = _safe_monkey_patch_property(
            cls, func_or_property_name, func_or_property
        )
        if success and attr_name is not None:
            setattr(cls, attr_name, attr_val)
    else:
        warnings.warn(
            f"{func_or_property_name} not added since provided func_or_property ({func_or_property} "
            f"is neither callable nor property"
        )


def _datacontainer_gui(self, box=None, refresh=False):
    if self._datacontainer_gui is None or refresh:
        self._datacontainer_gui = DataContainerGUI(self, box=box)
    return self._datacontainer_gui


safe_monkey_patch(DataContainer, "gui", _datacontainer_gui, "_datacontainer_gui", None)


def _pyiron_base_project_browser(self):
    if self._project_browser is None:
        self._project_browser = ProjectBrowser(
            project=self, show_files=False, Vbox=None
        )
    return self._project_browser


safe_monkey_patch(
    Project, "browser", property(_pyiron_base_project_browser), "_project_browser", None
)


def _has_groups_gui(self, box=None, refresh=False):
    if self._has_groups_browser is None or refresh:
        self._has_groups_browser = HasGroupsBrowser(self, box=box)
    return self._has_groups_browser


safe_monkey_patch(HasGroups, "gui", _has_groups_gui, "_has_groups_browser", None)
