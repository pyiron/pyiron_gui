# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import os

import matplotlib.pyplot as plt
import nbformat
import numpy as np

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base._tests import TestWithProject
from pyiron_gui.project.project_browser import PyironWrapper, DisplayOutputGUI


class TestPyironWrapper(TestWithProject):

    def setUp(self):
        self.pw_str = PyironWrapper("string_obj.ext", self.project)
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        self.pw_atoms = PyironWrapper(fe, self.project)
        ref_job = self.project.create.job.Lammps('ref')
        murn = ref_job.create_job('Murnaghan', 'murn')
        self.pw_murn = PyironWrapper(murn, self.project.open('sub'))

    def test___init__(self):
        self.assertEqual(self.pw_str._wrapped_object, "string_obj.ext")
        self.assertIsInstance(self.pw_atoms._wrapped_object, Atoms)
        self.assertIsInstance(self.pw_murn._wrapped_object, Murnaghan)

    def test_has_self_representation(self):
        self.assertFalse(self.pw_str.has_self_representation)
        self.assertTrue(self.pw_atoms.has_self_representation)
        self.assertTrue(self.pw_murn.has_self_representation)

    def test_path(self):
        self.assertEqual(self.pw_str.path, self.project.path)
        self.assertEqual(self.pw_atoms.path, self.project.path)
        self.assertEqual(self.pw_murn.path, self.project.path + 'murn')

    def test_list_nodes(self):
        msg = "Each object in the PyironWrapper should have list_nodes()"
        self.assertEqual(self.pw_str.list_nodes(), [], msg=msg)
        self.assertEqual(self.pw_atoms.list_nodes(), [], msg=msg)
        self.assertEqual(self.pw_murn.list_nodes(), [], msg=msg)

    def test___getattr__(self):
        self.assertTrue(self.pw_str.endswith('.ext'), msg="Unknown attributes should be passed to the wrapped object.")

    def test_name(self):
        self.assertIs(self.pw_str.name, None,
                      msg='str does not have a defined self representation, thus should be None')
        self.assertEqual(self.pw_atoms.name, 'structure')
        self.assertEqual(self.pw_murn.name, 'murnaghan')

    def test___repr__(self):
        self.assertEqual(repr(self.pw_str), "'string_obj.ext'")

    def test_project(self):
        self.assertIs(self.pw_str.project, self.project,
                      msg='A sting does not have a project and pw should return the project')
        self.assertIs(self.pw_atoms.project, self.project,
                      msg='Atoms does not have a project; should return pw._project')
        self.assertFalse(self.pw_murn.project is self.project, msg="murn.project should be a copy of the project")
        self.assertEqual(self.pw_murn.project.path, self.project.path)

    def test___getitem__(self):
        self.assertEqual(self.pw_str[0], 's', msg='Get item should return the appropriate item from the wrapped object')
        self.assertIs(self.pw_str['.'], self.project,
                      msg="For a TypeError of the wrapped object a path like item is assumed.")

    def test_self_representation(self):
        self.assertIs(self.pw_str.self_representation(), None)
        self.assertRaises(KeyError, self.pw_murn.self_representation)
        try:
            plot = self.pw_atoms.self_representation()
            self.assertEqual(type(plot).__name__, 'NGLWidget')
        except ImportError:
            pass


class TestDisplayOutputGUI(TestWithProject):

    def setUp(self):
        self.output = DisplayOutputGUI()

    def test___getattr__(self):
        self.output.append_stdout('Hi')

    def test_display_None(self):
        self.assertRaises(TypeError, self.output.display, None)
        self.output.display(None, default_output="None")

    def test_display_str(self):
        self.output.display("This")

    def test_display_pyiron_wrapped_atoms(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        pw_fe = PyironWrapper(fe, self.project)
        try:
            self.output.display(pw_fe)
            self.assertEqual(len(self.output.header.children), 2)
        except ImportError:
            pass

    def test__output_conv_ipynb(self):
        nb_cell = nbformat.NotebookNode(
            {
                'cell_type': 'markdown',
                'metadata': {},
                'source': "## Test"
            }
        )
        nb = nbformat.NotebookNode(
            {
                'cells': [nb_cell],
                'metadata': {},
                'nbformat': 4,
                'nbformat_minor': 4
            }
        )
        ret = self.output._output_conv(nb)
        self.assertEqual(type(ret).__name__, 'HTML')

    def test__output_conv_dict(self):
        ret = self.output._output_conv({'some': "dict"})
        self.assertEqual(type(ret).__name__, 'DataFrame')

    def test__output_conv_number(self):
        self.assertEqual(self.output._output_conv(1), '1')
        self.assertEqual(self.output._output_conv(1.0), '1.0')

    def test__output_conv_list_of_str(self):
        ret = self.output._output_conv(['1', '2'])
        self.assertEqual(ret, '12')
        to_long_list_of_str = [str(i) for i in range(2100)]
        ret = self.output._output_conv(to_long_list_of_str)
        self.assertEqual(ret, ''.join(to_long_list_of_str[:2000]) +
                         os.linesep + ' .... file too long: skipped ....')

    def test__output_conv_list(self):
        ret = self.output._output_conv([1, 2, 3])
        self.assertEqual(type(ret).__name__, 'DataFrame')

    def test__output_conv_image(self):
        img_file = os.path.join(self.project.path, 'some.tiff')
        plt.imsave(img_file,
                   np.array([[0, 100, 255], [100, 0,   0], [50, 50,  255], [255, 0,  255]], dtype=np.uint8))
        tiff_img = self.project['some.tiff']
        self.assertEqual(type(tiff_img).__name__, 'TiffImageFile')
        ret = self.output._output_conv(tiff_img)
        self.assertEqual(type(ret).__name__, 'Image')
        del tiff_img
        os.remove(img_file)

    def test__plot_array(self):
        ret = self.output._plot_array(np.array([1, 2, 3]))
        self.assertEqual(type(ret).__name__, 'Figure')

        ret = self.output._plot_array(np.array([[1, 2], [2, 3]]))
        self.assertEqual(type(ret).__name__, 'Figure')

        ret = self.output._plot_array(
            np.array(
                [[
                    [1, 2, 3],
                    [2, 3, 4]
                ]]
            )
        )
        self.assertEqual(type(ret).__name__, 'Figure')

        ret = self.output._plot_array(
            np.array(
                [[[
                    [1, 2, 3],
                    [2, 3, 4]
                ]]]
            )
        )
        self.assertEqual(type(ret).__name__, 'Figure')
