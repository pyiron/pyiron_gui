# Browsers for pyiron objects

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
