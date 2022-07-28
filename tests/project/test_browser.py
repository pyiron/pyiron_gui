# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import unittest
from os import remove
from os.path import join

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

from pyiron_base._tests import TestWithProject
from pyiron_base import DataContainer, Project
from pyiron_gui import activate_gui
from pyiron_gui.project.project_browser import (ProjectBrowser, HasGroupsBrowser, ColorScheme,
                                                HasGroupsBrowserWithHistoryPath, HasGroupBrowserWithOutput,
                                                DataContainerGUI)
from pyiron_gui.wrapper.wrapper import PyironWrapper
from tests.toy_job_run import ToyJob

TEST_DATA_CONTAINER = DataContainer(
    {
        "A": 10,
        "B": {
            'B1': {'a': 1, 'b': 2, 'c': '3', 'd': True, 'e': False, 'f': None, 'g': 2.5},
            'B2': {'h': 1, 'i': 2, 'j': '3', 'k': True, 'l': False, 'm': None, 'n': 2.5},
            'B3': 5,
            'B4': False
        },
        "C": [],
        "D": 1,
        "E": {
            'some_node': 'some_node',
            'NAME': 'name',
            'TYPE': 'type',
            'VERSION': 'version',
            'HDF_VERSION': 'hdf_version'
        }
    }
)


class TestActivateGUI(TestWithProject):

    def test_projects_load_file(self):
        img_file = join(self.project.path, 'some.tiff')
        plt.imsave(img_file,
                   np.array([[0, 100, 255], [100, 0,   0], [50, 50,  255], [255, 0,  255]], dtype=np.uint8))
        tiff_img = self.project['some.tiff']
        self.assertEqual(type(tiff_img).__name__, 'TiffImageFile')
        remove(img_file)

    def test_activate_gui(self):
        gui_pr = activate_gui(self.project)
        self.assertIsInstance(gui_pr, Project,
                              msg="activate_gui should return a Project inherited from a pyiron_base Project.")
        for attribute in object.__dir__(self.project):
            self.assertTrue(hasattr(gui_pr, attribute),
                            msg=f"GuiProject does not have the {attribute} attribute from the Project.")
        self.assertTrue(hasattr(gui_pr, 'browser'), msg="GuiProject does not have the added browser attribute.")
        self.assertIsInstance(gui_pr.browser, ProjectBrowser,
                              msg='The browser attribute should return a ProjectBrowser')


class TestColorScheme(unittest.TestCase):
    valid_color_definitions = ('blue', '#060482', '#A80')

    def setUp(self):
        self.color_dict = {'some': 'red', 'color': 'blue', 'definitions': '#FF0000'}
        self.color_scheme = ColorScheme(self.color_dict)

    def test___init__(self):
        with self.subTest('setUp'):
            self.assertEqual(self.color_scheme._color_dict, {'some': 'red', 'color': 'blue', 'definitions': '#FF0000'})
        with self.subTest('empty'):
            color_scheme = ColorScheme()
            self.assertEqual(color_scheme._color_dict, {})
        with self.subTest('Not a color'):
            self.assertRaises(ValueError, ColorScheme, {'a': 'a'})
        with self.subTest('Not an identifier'):
            self.assertRaises(ValueError, ColorScheme, {'1a': 'red'})

    def test___getitem__(self):
        self.assertEqual(self.color_scheme['some'], 'red')
        self.assertEqual(self.color_scheme['color'], 'blue')
        self.assertEqual(self.color_scheme['definitions'], '#FF0000')
        with self.assertRaises(KeyError):
            _ = self.color_scheme['NoSuchKey']

    def test___setitem__(self):
        self.color_scheme['some'] = 'black'
        self.assertEqual(self.color_scheme._color_dict, {'some': 'black', 'color': 'blue', 'definitions': '#FF0000'})

        with self.assertRaises(ValueError):
            self.color_scheme['some'] = 'NotAColor'

        with self.assertRaises(ValueError):
            self.color_scheme['NotAKey'] = 'blue'

    def test_add_colors(self):
        self.color_scheme.add_colors({'nice': 'yellow'})
        self.assertEqual(self.color_scheme._color_dict, {'some': 'red', 'color': 'blue', 'definitions': '#FF0000',
                                                         'nice': 'yellow'})

    def test_values(self):
        self.assertEqual(list(self.color_scheme.values()), list(self.color_dict.values()))

    def test_keys(self):
        self.assertEqual(list(self.color_scheme.keys()), list(self.color_dict.keys()))

    def test_items(self):
        color_dict = {}
        for key, value in self.color_scheme.items():
            color_dict[key] = value
        self.assertEqual(color_dict, self.color_dict)


class TestHasGroupsBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_container = TEST_DATA_CONTAINER.copy()

    def setUp(self):
        self.browser = HasGroupsBrowser(self.data_container)

    def test_color(self):
        self.assertIsInstance(self.browser.color, ColorScheme)
        self.assertEqual(self.browser.color["control"], "#FF0000")
        self.assertEqual(self.browser.color["group"], '#9999FF')
        self.assertEqual(self.browser.color['file_chosen'], '#FFBBBB')
        self.assertEqual(self.browser.color['file'], '#DDDDDD')

    def test___init__(self):
        browser = self.browser
        self.assertIs(browser.project, self.data_container)
        self.assertEqual(browser.groups, ['B', 'C', 'E'])
        self.assertEqual(browser.nodes, ['A', 'D'])
        self.assertIsNone(browser.data)

    def test__on_click_group_B(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.assertEqual(self.browser.groups, ['B1', 'B2'])
        self.assertEqual(self.browser.nodes, ['B3', 'B4'])

    def test__on_click_group_E(self):
        self.browser._on_click_group(widgets.Button(description='E'))
        self.assertEqual(self.browser.groups, [])
        self.assertEqual(self.browser.nodes, ['some_node'])

        self.browser._node_filter = []
        self.assertEqual(self.browser.nodes, ['some_node', 'NAME', 'TYPE', 'VERSION', 'HDF_VERSION'])

    def test__on_click_node(self):
        with self.subTest('select D'):
            self.browser._on_click_node(widgets.Button(description='D'))
            self.assertEqual(self.browser._clicked_nodes, ['D'])
            self.assertEqual(self.browser.data, 1)

        with self.subTest('select A'):
            self.browser._on_click_node(widgets.Button(description='A'))
            self.assertEqual(self.browser._clicked_nodes, ['A'])
            self.assertEqual(self.browser.data, 10)

        with self.subTest('unselect A'):
            self.browser._on_click_node(widgets.Button(description='A'))
            self.assertEqual(self.browser._clicked_nodes, [])
            self.assertIsNone(self.browser.data)

    def test_copy(self):
        self.test__on_click_group_B()
        cp = self.browser.copy()
        self.assertEqual(cp.groups, ['B1', 'B2'])
        self.assertEqual(cp.nodes, ['B3', 'B4'])
        self.assertFalse(cp._history is self.browser._history)

        cp._go_back()
        self.assertEqual(cp.groups, ['B', 'C', 'E'])
        self.assertEqual(cp.nodes, ['A', 'D'])
        self.assertEqual(self.browser.groups, ['B1', 'B2'])
        self.assertEqual(self.browser.nodes, ['B3', 'B4'])

    def test_project(self):
        self.assertIs(self.browser.project, self.data_container)
        dc = TEST_DATA_CONTAINER.copy()
        self.browser.project = dc
        self.assertIs(self.browser.project, dc)

        self.browser._go_back()
        self.assertIs(self.browser.project, self.data_container)

        self.browser._go_forward()
        self.assertIs(self.browser.project, dc)

    def test_navigation(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.browser._on_click_group(widgets.Button(description='B1'))
        self.assertEqual(self.browser.groups, [])
        self.assertEqual(self.browser.nodes, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

        with self.subTest('Go back'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])

        with self.subTest('Go forward'):
            self.browser._go_forward()
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

        with self.subTest('Go back again'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])

        with self.subTest('Open other group'):
            self.browser._on_click_group(widgets.Button(description='B2'))
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['h', 'i', 'j', 'k', 'l', 'm', 'n'])

        with self.subTest('Go back 3'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])

        with self.subTest('Go forward to new group'):
            self.browser._go_forward()
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['h', 'i', 'j', 'k', 'l', 'm', 'n'])


class TestHasGroupsBrowserWithHistoryPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_container = TEST_DATA_CONTAINER.copy()

    def setUp(self):
        self.browser = HasGroupsBrowserWithHistoryPath(self.data_container)

    def test_navigation(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.browser._on_click_group(widgets.Button(description='B1'))
        self.assertEqual(self.browser.groups, [])
        self.assertEqual(self.browser.nodes, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
        self.assertEqual(self.browser.path_list, ['/', 'B', 'B1'])

        with self.subTest('Go back'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])
            self.assertEqual(self.browser.path_list, ['/', 'B'])

        with self.subTest('Go forward'):
            self.browser._go_forward()
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            self.assertEqual(self.browser.path_list, ['/', 'B', 'B1'])

        with self.subTest('Go back again'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])
            self.assertEqual(self.browser.path_list, ['/', 'B'])

        with self.subTest('Open other group'):
            self.browser._on_click_group(widgets.Button(description='B2'))
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['h', 'i', 'j', 'k', 'l', 'm', 'n'])
            self.assertEqual(self.browser.path_list, ['/', 'B', 'B2'])

        with self.subTest('Go back 3'):
            self.browser._go_back()
            self.assertEqual(self.browser.groups, ['B1', 'B2'])
            self.assertEqual(self.browser.nodes, ['B3', 'B4'])
            self.assertEqual(self.browser.path_list, ['/', 'B'])

        with self.subTest('Go forward to new group'):
            self.browser._go_forward()
            self.assertEqual(self.browser.groups, [])
            self.assertEqual(self.browser.nodes, ['h', 'i', 'j', 'k', 'l', 'm', 'n'])
            self.assertEqual(self.browser.path_list, ['/', 'B', 'B2'])

    def test_home_button(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.browser._on_click_group(widgets.Button(description='B1'))
        self.browser._load_history(0)
        self.assertIs(self.browser.project, self.data_container)


class TestHasGroupsBrowserWithOutput(TestWithProject):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        job = cls.project.create_job(ToyJob, 'testjob')
        job.run()
        hdf = cls.project.create_hdf(cls.project.path, 'test_hdf.h5')
        hdf['key'] = 'value'
        Project(cls.project.path + 'sub')
        with open(cls.project.path+'text.txt', 'w') as f:
            f.write('some text')

    def setUp(self):
        self.browser = HasGroupBrowserWithOutput(self.project)

    def test_nodes(self):
        self.assertEqual(self.browser.nodes, ['testjob'])

    def test_groups(self):
        self.assertEqual(self.browser.groups, ['sub'])

    def test__on_click_file(self):
        browser = self.browser.copy()
        with self.subTest('init'):
            self.assertEqual(browser._clicked_nodes, [])
        with self.subTest("select"):
            browser._select_node('text.txt')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['text.txt'])
            self.assertEqual(browser.data, ["some text"])
        with self.subTest('de-select'):
            browser._select_node('text.txt')
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")
        with self.subTest("re-select"):
            browser._select_node('text.txt')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['text.txt'])
            self.assertEqual(browser.data, ["some text"])
        with self.subTest("invalid node"):
            browser._select_node('NotAFileName.dat')
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")
            
    @unittest.skip()
    def test__update_project(self):
        browser = self.browser.copy()
        browser._update_project('testjob')
        self.assertIsInstance(browser.project._wrapped_object, ToyJob,
                              msg=f"Any pyiron object with 'TYPE' in list_nodes() should be wrapped.")
        self.assertFalse(browser._node_as_group)

        browser._select_node('text.txt')
        self.assertTrue(browser._data is None, msg="This file should not be present in the ToyJob.")


class TestProjectBrowser(TestWithProject):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        job = cls.project.create_job(ToyJob, 'testjob')
        job.run()
        hdf = cls.project.create_hdf(cls.project.path, 'test_hdf.h5')
        hdf['key'] = 'value'
        Project(cls.project.path + 'sub')
        with open(cls.project.path+'text.txt', 'w') as f:
            f.write('some text')

    def setUp(self):
        self.browser = ProjectBrowser(project=self.project, show_files=False)

    def test_init_browser(self):
        self.assertTrue(self.browser.project is self.project)
        self.assertEqual(self.browser.path, self.project.path)
        self.assertFalse(self.browser.show_files)
        self.assertTrue(self.browser.hide_path)
        self.assertFalse(self.browser.fix_path)
        self.assertTrue(self.browser._node_as_group)

        vbox = widgets.VBox()
        browser = ProjectBrowser(project=self.project, Vbox=vbox)
        self.assertTrue(browser.box is vbox and browser.project is self.project)
        browser.refresh()
        self.assertTrue(len(browser.box.children) > 0)

    def test_copy(self):
        browser = self.browser.copy()
        self.assertTrue(browser.project is self.browser.project)
        self.assertEqual(browser.path, self.browser.path)
        self.assertFalse(browser._box is self.browser.box)
        self.assertEqual(browser.fix_path, self.browser.fix_path)

    def test_configure(self):
        browser = self.browser
        vbox = widgets.VBox()

        browser.configure(show_files=True)
        self.assertTrue(browser.show_files)
        self.assertTrue(browser.hide_path)
        self.assertFalse(browser.fix_path)

        browser.configure(fix_path=True)
        self.assertTrue(browser.show_files)
        self.assertTrue(browser.hide_path)
        self.assertTrue(browser.fix_path)

        browser.configure(hide_path=True)
        self.assertTrue(browser.show_files)
        self.assertTrue(browser.hide_path)
        self.assertTrue(browser.fix_path)

        browser.configure(hide_path=False)
        self.assertTrue(browser.show_files)
        self.assertFalse(browser.hide_path)
        self.assertTrue(browser.fix_path)

        browser.configure(show_files=False, fix_path=False, hide_path=True, Vbox=vbox)
        self.assertFalse(browser.show_files)
        self.assertTrue(browser.hide_path)
        self.assertFalse(browser.fix_path)
        self.assertTrue(browser.box is vbox)

    def test_files(self):
        browser = self.browser.copy()
        self.assertEqual(browser.files, [])
        browser.show_files = True
        self.assertEqual(len(browser.files), 1)
        self.assertFalse('testjob.h5' in browser.files)
        self.assertFalse('test_hdf.h5' in browser.files)
        self.assertTrue('text.txt' in browser.files)
        browser._file_ext_filter = []
        browser.refresh()
        self.assertEqual(len(browser.files), 3)
        self.assertTrue('testjob.h5' in browser.files)
        self.assertTrue('test_hdf.h5' in browser.files)
        self.assertTrue('text.txt' in browser.files)

    def test_nodes(self):
        self.assertEqual(self.browser.nodes, ['testjob'])

    def test_dirs(self):
        self.assertEqual(self.browser.groups, ['sub'])

    def test__on_click_file(self):
        browser = self.browser.copy()
        with self.subTest('init'):
            self.assertEqual(browser._clicked_nodes, [])
        with self.subTest("select"):
            browser._select_node('text.txt')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['text.txt'])
            self.assertEqual(browser.data, ["some text"])
        with self.subTest('de-select'):
            browser._select_node('text.txt')
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")
        with self.subTest("re-select"):
            browser._select_node('text.txt')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['text.txt'])
            self.assertEqual(browser.data, ["some text"])
        with self.subTest("invalid node"):
            browser._select_node('NotAFileName.dat')
            self.assertEqual(browser._clicked_nodes, [])
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")

    def test_data(self):
        browser = self.browser.copy()
        browser._data = "some text"
        self.assertEqual(browser.data, "some text")
        browser._data = None
        self.assertTrue(browser.data is None)
        str_obj = "Some string"
        browser._project = PyironWrapper(str_obj, project=self.project)
        self.assertIs(browser.data, str_obj)

    def test_gen_pathbox_path_list(self):
        class DummyProj:
            def __init__(self, path):
                self.path = path

        self.browser._project = DummyProj('/some/path')
        self.assertEqual(['/', '/some', '/some/path'], self.browser._gen_pathbox_path_list())

        self.browser._project = DummyProj('/some/path/')
        self.assertEqual(['/', '/some', '/some/path'], self.browser._gen_pathbox_path_list())

    @unittest.skip()
    def test__update_project(self):
        browser = self.browser.copy()
        path = join(browser.path, 'testjob')
        browser._update_project(path)
        self.assertIsInstance(browser.project._wrapped_object, ToyJob,
                              msg=f"Any pyiron object with 'TYPE' in list_nodes() should be wrapped.")
        self.assertFalse(browser._node_as_group)
        self.assertEqual(browser.path, path)

        browser._select_node('text.txt')
        self.assertTrue(browser._data is None, msg="This file should not be present in the ToyJob.")

        browser._update_project(path)
        self.assertEqual(browser.path, path)

        browser._update_project(self.project)
        self.assertEqual(browser.path, self.project.path)
        self.assertIs(browser.project, self.project)

        browser._update_project("NotExistingPath")
        self.assertEqual(browser.path, self.project.path)
        self.assertIs(browser.project, self.project)

    def test_gui(self):
        self.browser.gui()

    def test_box(self):
        Vbox = widgets.VBox()
        self.browser.box = Vbox
        self.assertTrue(self.browser.box is Vbox)
        self.assertTrue(len(self.browser.box.children) > 0)

    def test_fix_path(self):
        self.assertFalse(self.browser.fix_path)
        self.browser.fix_path = True
        self.assertTrue(self.browser.fix_path)

    def test_hide_path(self):
        self.assertTrue(self.browser.hide_path)
        self.browser.hide_path = False
        self.assertFalse(self.browser.hide_path)

    def test__click_option_button(self):
        reset_button = widgets.Button(description="Reset selection")
        set_path_button = widgets.Button(description="Set Path")

        self.browser._select_node('text.txt')
        self.browser._reset_data(reset_button)
        self.assertIs(self.browser.data, None)
        self.assertEqual(self.browser._clickedFiles, [])

        self.browser._set_pathbox_path(set_path_button)

        self.browser.fix_path = True
        self.browser.path_string_box.value = "sub"
        self.browser._set_pathbox_path(set_path_button)
        self.assertEqual(self.browser.path, self.project.path)

        self.browser.fix_path = False
        self.browser.path_string_box.value = "sub"
        self.browser._set_pathbox_path(set_path_button)
        self.assertEqual(self.browser.path, join(self.project.path, 'sub/'))
        self.assertEqual(self.browser.path_string_box.value, "")

        self.browser.path_string_box.value = self.project.path
        self.browser._set_pathbox_path(set_path_button)
        self.assertEqual(self.browser.path, self.project.path)
        self.assertEqual(self.browser.path_string_box.value, "")

    def test_color(self):
        color_keys = self.browser.color.keys()
        for key in ['group', 'file', 'file_chosen', 'path', 'home']:
            with self.subTest(key):
                self.assertTrue(key in color_keys)
                color = self.browser.color[key]
                self.assertEqual(len(color), 7)
                self.assertEqual(color[0], '#')
                self.assertTrue(0 <= int(color[1:3], base=16) <= 255)
                self.assertTrue(0 <= int(color[3:5], base=16) <= 255)
                self.assertTrue(0 <= int(color[5:7], base=16) <= 255)


class TestDataContainerGui(TestHasGroupsBrowserWithHistoryPath):
    """The DataContainerGUI should be able to pass all tests on the BrowserWithHistoryPath."""
    def setUp(self):
        self.browser = DataContainerGUI(project=self.data_container)

    def test__on_click_file(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.browser._on_click_group(widgets.Button(description='B1'))
        browser = self.browser
        with self.subTest('init'):
            self.assertEqual(browser._clicked_nodes, [])
        with self.subTest("select"):
            browser._select_node('a')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['a'])
            self.assertEqual(browser.data, 1)
        with self.subTest('de-select'):
            browser._select_node('a')
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")
        with self.subTest("re-select"):
            browser._select_node('a')
            browser.refresh()
            self.assertEqual(browser._clicked_nodes, ['a'])
            self.assertEqual(browser.data, 1)
        with self.subTest("invalid node"):
            browser._select_node('NotAFileName.dat')
            self.assertIsNone(browser.data, msg=f"Expected browser.data to be None, but got {browser.data}")

    def test_data(self):
        self.browser._on_click_group(widgets.Button(description='B'))
        self.browser._on_click_group(widgets.Button(description='B1'))
        with self.subTest('get_data'):
            self.browser._select_node('a')
            self.browser.refresh()
            self.assertEqual(self.browser._clicked_nodes, ['a'])
            self.assertEqual(self.browser.data, 1)
        with self.subTest('set_data'):
            self.browser.data = 2
            self.assertEqual(self.browser._clicked_nodes, ['a'])
            self.assertEqual(self.browser.data, 2)
        with self.subTest('set_data no node selected'):
            self.browser._select_node('a')
            self.assertEqual(self.browser._clicked_nodes, [])
            self.assertEqual(self.browser.data, None)
            with self.assertRaises(ValueError):
                self.browser.data = 3
            self.assertEqual(self.browser.data, None)


if __name__ == '__main__':
    unittest.main()
