__version__ = "0.1"
__all__ = []

from pyiron_gui.project.project import activate_gui
from pyiron_gui.project.project_browser import ProjectBrowser, DataContainerGUI

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
