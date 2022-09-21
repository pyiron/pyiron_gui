# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import os
import posixpath
from functools import singledispatch

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base import HasGroups
from pyiron_gui.wrapper.widgets import ObjectWidget, AtomsWidget, MurnaghanWidget

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
