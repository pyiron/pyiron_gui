# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from pyiron_base import Project as BaseProject
from pyiron_gui.project.project_browser import ProjectBrowser

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


def activate_gui(project_instance):
    """
    Activate GUI elements for a provided pyiron Project instance

        Args:
            project_instance: Instantiated pyiron Project
        Returns:
            GUIProject: Instantiated pyiron Project with added GUI functionality.
    """

    class GUIProject(project_instance.__class__):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._project_browser = None

        @property
        def browser(self):
            """Provides a browser to inspect the data system of the project."""
            if self._project_browser is None:
                self._project_browser = ProjectBrowser(
                    project=self, show_files=False, Vbox=None
                )
            return self._project_browser

    if not isinstance(project_instance, BaseProject):
        raise ValueError("Only pyiron Projects support a GUI extension.")

    # This is the same as the copy() method on a pyiron_base Project using the class of the project_instance instead
    new = GUIProject(
        path=project_instance.path,
        user=project_instance.user,
        sql_query=project_instance.sql_query,
    )
    new._filter = project_instance._filter
    new._inspect_mode = project_instance._inspect_mode
    return new
