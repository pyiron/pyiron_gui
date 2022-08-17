# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

"""Adding gui functionality to pyiron classes via monkey patching on import of pyiron_gui. """
import warnings

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


def safe_monkey_patch(cls, attr_name, func):
    bound_method = getattr(cls, attr_name) if hasattr(cls, attr_name) else None

    if bound_method is not None and (bound_method.__module__ != func.__module__ or bound_method.__name__ != func.__name__):
        warnings.warn(
            f"Class {cls.__name__} already has attribute {attr_name} - Aborting monkey path of gui elements."
        )
    else:
        setattr(cls, attr_name, func)


def _has_groups_gui(self, box=None, refresh=False):
    if self._has_groups_browser is None or refresh:
        self._has_groups_browser = HasGroupsBrowser(self, box=box)
    return self._has_groups_browser


safe_monkey_patch(HasGroups, "_has_groups_browser", None)
safe_monkey_patch(HasGroups, "gui", _has_groups_gui)


def _datacontainer_gui(self, box=None, refresh=False):
    if self._datacontainer_gui is None or refresh:
        self._datacontainer_gui = DataContainerGUI(self, box=box)
    return self._datacontainer_browser


safe_monkey_patch(DataContainer, "_datacontainer_gui", None)
safe_monkey_patch(DataContainer, "gui", _datacontainer_gui)


def _pyiron_base_project_browser(self):
    if self._project_browser is None:
        self._project_browser = ProjectBrowser(
            project=self, show_files=False, Vbox=None
        )
    return self._project_browser


safe_monkey_patch(Project, "_project_browser", None)
safe_monkey_patch(Project, "browser", property(_pyiron_base_project_browser))
