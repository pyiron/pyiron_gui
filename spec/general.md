# Spec for pyiron_gui

pyiron_gui is inteded to act as a very thin layer on top of the overall pyiron framework and provide conveniant graphical user interface (GUI) elements for specific tasks/classes.
In a later stage, these might be combined to allow for a full-gui version (with most probably limited functionality) of pyiron.

The individual GUI elements are based on ipywidgets. 
Each element is constructed in a box (`ipywidgets.Vbox`) and this box could be provided to another element to update its content with the new element. 
This allows to construct an 'update-able window' which can be used to display (also switch) between different GUI elements.
