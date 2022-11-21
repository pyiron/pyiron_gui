__version__ = "0.1"
__all__ = []

# desired API
from pyiron_gui.project.project import activate_gui
from pyiron_gui.project.project_browser import (
    ProjectBrowser,
    DataContainerGUI,
    HasGroupsBrowser,
)

# monkey patching
import pyiron_gui.monkey_patching


from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
