# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import os

import ipywidgets as widgets
import matplotlib.pyplot as plt
import nbformat
import numpy as np

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base._tests import TestWithProject
from pyiron_gui.project.project_browser import (PyironWrapper, DisplayOutputGUI, BaseWrapper, MurnaghanWrapper,
                                                AtomsWrapper)


class TestPyironWrapper(TestWithProject):

    def test___new__str(self):
        self.assertIsInstance(PyironWrapper("string_obj.ext", self.project), BaseWrapper)

    def test___new__atoms(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        self.assertIsInstance(PyironWrapper(fe, self.project), AtomsWrapper)

    def test___new__murn(self):
        ref_job = self.project.create.job.Lammps('ref')
        murn = ref_job.create_job('Murnaghan', 'murn')
        self.assertIsInstance(PyironWrapper(murn, self.project.open('sub')), MurnaghanWrapper)


class TestBaseWrapper(TestWithProject):

    def setUp(self):
        self.pw_str = BaseWrapper("string_obj.ext", self.project)
        self.pw_str_w_rel_path = BaseWrapper("string_obj.ext", self.project, rel_path="some/random/path")
        self.broken_proj_pw_str = BaseWrapper("string_obj.ext", None)

    def test___init__(self):
        self.assertEqual(self.pw_str._wrapped_object, "string_obj.ext")

    def test_has_self_representation(self):
        self.assertFalse(self.pw_str.has_self_representation)

    def test_path(self):
        self.assertEqual(self.pw_str.path, self.project.path)
        self.assertEqual(self.pw_str_w_rel_path.path, os.path.join(self.project.path, 'some/random/path'))
        with self.assertRaises(AttributeError):
            print(self.broken_proj_pw_str.path)

    def test_list_nodes(self):
        msg = "Each object in the PyironWrapper should have list_nodes()"
        self.assertEqual(self.pw_str.list_nodes(), [], msg=msg)

    def test___getattr__(self):
        self.assertTrue(self.pw_str.endswith('.ext'), msg="Unknown attributes should be passed to the wrapped object.")

    def test_name(self):
        self.assertIs(self.pw_str.name, None,
                      msg='str does not have a defined self representation, thus should be None')

    def test___repr__(self):
        self.assertEqual(repr(self.pw_str), "'string_obj.ext'")

    def test_project(self):
        self.assertIs(self.pw_str.project, self.project,
                      msg='A sting does not have a project and pw should return the project')

    def test___getitem__(self):
        self.assertEqual(self.pw_str[0], 's', msg='Get item should return the appropriate item from the wrapped object')
        self.assertIs(self.pw_str['.'], self.project,
                      msg="For a TypeError of the wrapped object a path like item is assumed.")
        super_proj = self.pw_str['..']
        self.assertEqual(os.path.normpath(super_proj.path), os.path.split(os.path.normpath(self.project.path))[0])

    def test_self_representation(self):
        self.assertIs(self.pw_str.self_representation(), None)


class TestAtomsWrapper(TestWithProject):

    def setUp(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        self.pw_atoms = AtomsWrapper(fe, self.project)

    def test___init__(self):
        self.assertIsInstance(self.pw_atoms._wrapped_object, Atoms)

    def test_has_self_representation(self):
        self.assertTrue(self.pw_atoms.has_self_representation)

    def test_path(self):
        self.assertEqual(self.pw_atoms.path, self.project.path)

    def test_list_nodes(self):
        msg = "Each object in the PyironWrapper should have list_nodes()"
        self.assertEqual(self.pw_atoms.list_nodes(), [], msg=msg)

    def test_name(self):
        self.assertEqual(self.pw_atoms.name, 'structure')

    def test_project(self):
        self.assertIs(self.pw_atoms.project, self.project,
                      msg='Atoms does not have a project; should return pw._project')

    def test_self_representation(self):
        # No nglview on github CI, thus:
        try:
            plot = self.pw_atoms.self_representation()
            self.assertEqual(type(plot).__name__, 'NGLWidget')
            # Needed to populate the _camera_orientation:
            plot.display()
            widget_state_orient_init = plot.get_state()['_camera_orientation']

            plot.control.translate([1., 0, 0])
            widget_state_orient = plot.get_state()['_camera_orientation']
            replot = self.pw_atoms.self_representation()
            self.assertEqual(widget_state_orient, replot.get_state()['_camera_orientation'])

            self.pw_atoms._option_widgets['reset_view'].value = True
            replot = self.pw_atoms.self_representation()
            self.assertEqual(widget_state_orient_init, replot.get_state()['_camera_orientation'])
        except ImportError:
            pass

    def test__parse_option_widgets(self):
        self.assertEqual(1.0, self.pw_atoms._options['particle_size'])
        self.pw_atoms._option_widgets['particle_size'].value = 2.5
        self.pw_atoms._parse_option_widgets()
        self.assertEqual(2.5, self.pw_atoms._options['particle_size'])


class TestMurnaghanWrapper(TestWithProject):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        ref_job = cls.project.create.job.Lammps('ref')
        murn = ref_job.create_job('Murnaghan', 'murn')
        murn.structure = fe
        # mock murnaghan run with data from:
        #   ref_job = pr.create.job.Lammps('Lammps')
        #   ref_job.structure = pr.create_structure('Al','fcc', 4.0).repeat(3)
        #   ref_job.potential = '1995--Angelo-J-E--Ni-Al-H--LAMMPS--ipr1'
        #   murn = ref_job.create_job(ham.job_type.Murnaghan, 'murn')
        #   murn.run()
        energies = np.array([-88.23691773, -88.96842984, -89.55374317, -90.00642629,
                             -90.33875009, -90.5618246, -90.68571886, -90.71957679,
                             -90.67170222, -90.54964935, -90.36029582])
        volume = np.array([388.79999999, 397.44, 406.08, 414.71999999,
                           423.35999999, 431.99999999, 440.63999999, 449.27999999,
                           457.92, 466.55999999, 475.19999999])
        murn._hdf5["output/volume"] = volume
        murn._hdf5["output/energy"] = energies
        murn._hdf5["output/equilibrium_volume"] = 448.4033384110422
        murn.status.finished = True
        cls.murn = murn

    def setUp(self):
        self.pw_murn = MurnaghanWrapper(self.murn, self.project)

    def test___init__(self):
        self.assertIsInstance(self.pw_murn._wrapped_object, Murnaghan)

    def test_has_self_representation(self):
        self.assertTrue(self.pw_murn.has_self_representation)

    def test_path(self):
        self.assertEqual(self.pw_murn.path, self.project.path + 'murn')

    def test_list_nodes(self):
        msg = "Each object in the PyironWrapper should have list_nodes()"
        self.assertEqual(self.pw_murn.list_nodes(), [], msg=msg)

    def test_option_representation(self):
        option_repr = self.pw_murn.option_representation
        self.assertEqual('polynomial', option_repr.children[0].value)
        self.assertEqual(3, option_repr.children[1].value)

    def test_name(self):
        self.assertEqual(self.pw_murn.name, 'murnaghan')

    def test_project(self):
        self.assertFalse(self.pw_murn.project is self.project, msg="murn.project should be a copy of the project")
        self.assertEqual(self.pw_murn.project.path, self.project.path)

    def test_self_representation(self):
        self.pw_murn.self_representation()
        self.assertTrue(np.isclose(-90.71969974284912, self.pw_murn.equilibrium_energy))
        self.assertTrue(np.isclose(448.1341230545222, self.pw_murn.equilibrium_volume))

        self.pw_murn._option_widgets['fit_order'].value = 2
        self.pw_murn.self_representation()
        self.assertTrue(np.isclose(-90.76380033222287, self.pw_murn.equilibrium_energy))
        self.assertTrue(np.isclose(449.1529040727273, self.pw_murn.equilibrium_volume))

        self.pw_murn._option_widgets['fit_type'].value = 'birchmurnaghan'
        self.pw_murn.self_representation()
        self.assertTrue(np.isclose(-90.72005405262217, self.pw_murn.equilibrium_energy))
        self.assertTrue(np.isclose(448.41909755611437, self.pw_murn.equilibrium_volume))


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

    def test_display_numpy_array(self):
        array = np.array([[[[1, 0, 0]]]])
        self.output.display(array)
        self.assertEqual(len(self.output._plot_options['idx']), 2)


    def test__plot_array_with_options(self):
        array_4d = np.array([[[[1, 0, 0]]]])
        self.output._array_plot_options(array_4d)
        self.output._plot_options["dim"].value = [0, 1, 2]
        self.output._plot_array(array_4d)

        array_3d = np.array([[[1, 0, 0]]])
        self.output._array_plot_options(array_3d)
        self.output._plot_options["dim"].value = [0, 2]
        self.output._plot_array(array_3d)

    def test__click_button(self):
        array = np.array([0, 1, 1])
        self.output.display(array)

        button = widgets.Button(description='Show data')
        button.obj = array
        self.output._click_button(button)
        self.assertEqual(button.description, 'Show plot')

        button.description = "Re-plot"
        self.output._click_button(button)

        button.description = "else"
        self.output._click_button(button)

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
        self.output._debug = True
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

    def test__output_conv__repr_html_(self):
        class AnyClass:
            def _repr_html_(self):
                pass
        self.assertIsInstance(self.output._output_conv(AnyClass()), AnyClass)

    def test__output_conv__else(self):
        class AnyClass:
            pass
        self.assertIsInstance(self.output._output_conv(AnyClass()), AnyClass)

    def test__plot_array(self):
        ret = self.output._plot_array(np.array([1, 2, 3]))
        self.assertEqual(type(ret).__name__, 'Figure')

        ret = self.output._plot_array(np.array([[1, 2], [2, 3]]))
        self.assertEqual(type(ret).__name__, 'Figure')

        ret = self.output._plot_array(np.array([[1, 2, 3]]))
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
