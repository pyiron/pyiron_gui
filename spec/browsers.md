# Browsers for pyiron objects

### HasGroupsBrowser

Every pyiron object implementing [`HasGroups`](https://github.com/pyiron/pyiron_base/blob/master/specs/has_groups.md) has a hierachical structure which can be used to 
visualize these objects. To do so, there is a `HasGroupsBrowser` which provides a button for each `group` and each `node`. 
In addition, a 'go-forward' and a 'go-backward' button are present. These three groups - control buttons (red), group buttons (blue), and node buttons (gray, normal/pink if clicked) - 
are displayed in one line each with overflow to the next line:

![HasGroupsBrowser_short](https://user-images.githubusercontent.com/70580458/142241674-f45a77ed-510b-4dd1-a15f-8cb524faf800.png)

The colors of the individual groups may be changed by the `HasGroupsBrowser.color` attribute, e.g. `HasGroupsBrowser(has_groups_obj).color['control']='blue'` 
accepting color definitions as understood by `ipywidgets` (e.g. 'blue', 'red', '#000', '#FF0000', etc.).

If a button is clicked, the following things happen dependent on the type of the button:
- control button: Go back (forward) in history. These buttons are only active if there is a previous (future) point of history.
- group buttons: Switch to the chosen group and update the browser to show the nodes and groups of this chosen group. 
The chosen group will be appended to the history and represents the current head of the history, i.e. all potentially 'more future' points in history before the 'click' are ignored.
- node buttons: Select the clicked node. The color of the chosen node changes (by default from gray to pink) and the data of the node (`has_groups_obj[node]`) is now
available via the `HasGroupsBrowser.data` attribute.

### HasGroupsBrowserWithHistoryPath

The `HasGroupsBrowserWithHistoryPath` is an extention to the `HasGroupsBrowser`, which adds path control buttons on the first line:

![HasGroupsBrowserWithHistoryPath](https://user-images.githubusercontent.com/70580458/143093862-0fb0616e-379b-470c-a5a6-da3af76786cc.png)

Here, the home button is the 0th place in history, i.e. the `HasGroups` object the overall browser started with. Each additional button is a group visited before. 
Clicking on a path button takes the browser back to that specific point in history (similar to clicking the go back button several times until reaching this point). 
The functionality on click on any of the other buttons is retained. 

### HasGroupsBrowserWithOutput

The `HasGroupsBrowserWithOutput` extends the `HasGroupBrowser` with an output window on the right side:

![HasGroupsBrowserWithOutput](https://user-images.githubusercontent.com/70580458/143096435-82b54d52-461a-4b91-977b-f301dd10c7a9.png)

The functionality is the same as the standard `HasGroupsBrowser` but the data received from `HasGroups['node']` is passed to a [`DisplayOutputGUI`](display_output_gui.md) to be displayed. In this example, the display of a numpy array is shown.

### DataContainerGUI

The `DataContainerGUI` is a combination of the `HasGroupsBrowserWithOutput` and the `HasGroupsBrowserWithHistoryPath`:

![DataContainerGUI](https://user-images.githubusercontent.com/70580458/143097849-ab13608d-84fd-48f7-b2bb-2433f9b03e6e.png)

In addition to the combined functionality, this object allows to change the data stored in the clicked group by `DataContainerGUI.data = new_data_object`.

### ProjectBrowser

The `ProjectBrowser` extends the `HasGroupsBrowserWithOutput` by a path derived from _the_ pyiron `Project`.
