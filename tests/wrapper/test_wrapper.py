# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import io
import os
import unittest
import unittest.mock

import ipywidgets as widgets
import matplotlib.pyplot as plt
import nbformat
import numpy as np

from pyiron_atomistics import Atoms
from pyiron_atomistics.atomistics.master.murnaghan import Murnaghan
from pyiron_base._tests import TestWithProject, TestWithCleanProject
from pyiron_gui.wrapper.widgets import AtomsWidget, MurnaghanWidget, NumpyWidget, DisplayOutputGUI
from pyiron_gui.wrapper.wrapper import PyironWrapper, BaseWrapper, AtomsWrapper, MurnaghanWrapper


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

    def test_gui(self):
        self.assertIsInstance(self.pw_str.gui, widgets.VBox)


class TestAtomsWrapper(TestWithProject):

    def setUp(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        self.pw_atoms = AtomsWrapper(fe, self.project)

    def test___init__(self):
        self.assertIsInstance(self.pw_atoms._wrapped_object, Atoms)

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

    def test_gui(self):
        # No nglview on github CI, thus:
        try:
            self.assertIsInstance(self.pw_atoms.gui, widgets.VBox)
        except ImportError:
            pass


class TestAtomsWidget(TestWithProject):
    def setUp(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        self.pw_atoms = AtomsWidget(AtomsWrapper(fe, self.project))

    def test_gui(self):
        self.assertIs(self.pw_atoms._ngl_widget, None)
        # No nglview on github CI, thus:
        try:
            self.pw_atoms.refresh()
        except ImportError:
            pass
        else:
            plot = self.pw_atoms._ngl_widget
            self.assertEqual(type(plot).__name__, 'NGLWidget')
            # Needed to populate the _camera_orientation:
            plot.display()
            widget_state_orient_init = plot.get_state()['_camera_orientation']

            plot.control.translate([1., 0, 0])
            widget_state_orient = plot.get_state()['_camera_orientation']
            self.pw_atoms.refresh()
            replot = self.pw_atoms._ngl_widget
            self.assertFalse(plot is replot)
            self.assertEqual(widget_state_orient, replot.get_state()['_camera_orientation'])

            self.pw_atoms._option_widgets['reset_view'].value = True
            self.pw_atoms.refresh()
            self.assertEqual(widget_state_orient_init, self.pw_atoms._ngl_widget.get_state()['_camera_orientation'])

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

    def test_path(self):
        self.assertEqual(self.pw_murn.path, self.project.path + 'murn')

    def test_list_nodes(self):
        msg = "Each object in the PyironWrapper should have list_nodes()"
        self.assertEqual(self.pw_murn.list_nodes(), [], msg=msg)

    def test_name(self):
        self.assertEqual(self.pw_murn.name, 'murnaghan')

    def test_project(self):
        self.assertFalse(self.pw_murn.project is self.project, msg="murn.project should be a copy of the project")
        self.assertEqual(self.pw_murn.project.path, self.project.path)

    def test_gui(self):
        self.assertIsInstance(self.pw_murn.gui, widgets.VBox)


class TestMurnaghanWidget(TestWithCleanProject):

    def setUp(self):
        fe = Atoms(cell=[4, 4, 4], elements=['Fe', 'Fe'], positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        ref_job = self.project.create.job.Lammps('ref')
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
        self.pw_murn = MurnaghanWidget(MurnaghanWrapper(murn, self.project))

    def test_option_representation(self):
        self.assertEqual('polynomial', self.pw_murn._options['fit_type'])
        self.assertEqual(3, self.pw_murn._options['fit_order'])

    def test_gui(self):
        with self.subTest(msg='polynomial with fit_order=3'):
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertAlmostEqual(-90.71969974284912, self.pw_murn._obj.equilibrium_energy)
            self.assertAlmostEqual(448.1341230545222, self.pw_murn._obj.equilibrium_volume)

        with self.subTest(msg='polynomial with fit_order=2'):
            self.pw_murn._option_widgets['fit_order'].value = 2
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertTrue(np.isclose(-90.76380033222287, self.pw_murn._obj.equilibrium_energy))
            self.assertTrue(np.isclose(449.1529040727273, self.pw_murn._obj.equilibrium_volume))

        with self.subTest(msg='birchmurnaghan'):
            self.pw_murn._option_widgets['fit_type'].value = 'birchmurnaghan'
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertTrue(np.isclose(-90.72005405262217, self.pw_murn._obj.equilibrium_energy))
            self.assertTrue(np.isclose(448.41909755611437, self.pw_murn._obj.equilibrium_volume))

        with self.subTest(msg='murnaghan'):
            self.pw_murn._option_widgets['fit_type'].value = 'murnaghan'
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertAlmostEqual(-90.72018572197015, self.pw_murn._obj.equilibrium_energy)
            self.assertAlmostEqual(448.4556825322108, self.pw_murn._obj.equilibrium_volume)

        with self.subTest(msg='vinet'):
            self.pw_murn._option_widgets['fit_type'].value = 'vinet'
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertAlmostEqual(-90.72000006839492, self.pw_murn._obj.equilibrium_energy)
            self.assertAlmostEqual(448.40333840970357, self.pw_murn._obj.equilibrium_volume)

        with self.subTest(msg='pouriertarantola'):
            self.pw_murn._option_widgets['fit_type'].value = 'pouriertarantola'
            self.pw_murn._on_click_apply_button("NoButtonSinceNotNeeded")
            self.assertAlmostEqual(-90.71996235760845, self.pw_murn._obj.equilibrium_energy)
            self.assertAlmostEqual(448.3876577969001, self.pw_murn._obj.equilibrium_volume)


class TestNumpyWidget(unittest.TestCase):

    def setUp(self):
        self.np_1d_wid = NumpyWidget(np.arange(10))
        self.np_2d_wid = NumpyWidget(np.reshape(np.arange(30), (10, 3)))
        self.np_3d_wid = NumpyWidget(np.reshape(np.arange(600), (10, 20, 3)))
        self.np_4d_wid = NumpyWidget(np.reshape(np.arange(2000), (10, 10, 10, 2)))

    def test___init__(self):
        with self.subTest(msg="1D"):
            self.assertIs(self.np_1d_wid._plot_options, None, msg='1D array should not have plot options')
            self.assertEqual(self.np_1d_wid._replot_button.description, 'Replot',
                             msg="Without plot options, there is only a 'Replot'.")
            header = self.np_1d_wid._header
            hbox_children = header.children[0].children
            self.assertIs(hbox_children[0], self.np_1d_wid._show_data_button)
            self.assertIs(hbox_children[1], self.np_1d_wid._replot_button)
        with self.subTest(msg="2D"):
            self.assertIs(self.np_2d_wid._plot_options, None, msg='2D array should not have plot options')
            self.assertEqual(self.np_2d_wid._replot_button.description, 'Replot',
                             msg="Without plot options, there is only a 'Replot'.")
            header = self.np_2d_wid._header
            hbox_children = header.children[0].children
            self.assertIs(hbox_children[0], self.np_2d_wid._show_data_button)
            self.assertIs(hbox_children[1], self.np_2d_wid._replot_button)
        with self.subTest(msg="3D"):
            self.assertEqual(self.np_3d_wid._plot_options['dim'].value, (0, 1),
                             msg="The first two dimensions should be plot by default")
            self.assertEqual(len(self.np_3d_wid._plot_options['idx']), 1,
                             msg='For a 3D array, there is one additional index to choose')
            self.assertEqual(self.np_3d_wid._plot_options['idx'][0].value, 0,
                             msg='The default index to plot should be 0')
            self.assertEqual(self.np_3d_wid._replot_button.description, 'Apply',
                             msg="With plot options, these can be applied.")
        with self.subTest(msg="4D"):
            self.assertEqual(self.np_4d_wid._plot_options['dim'].value, (0, 1),
                             msg="The first two dimensions should be plot by default")
            self.assertEqual(len(self.np_4d_wid._plot_options['idx']), 2,
                             msg='For a 3D array, there are two additional index to choose')
            self.assertEqual(self.np_4d_wid._plot_options['idx'][0].value, 0,
                             msg='The default index to plot should be 0')
            self.assertEqual(self.np_4d_wid._plot_options['idx'][1].value, 0,
                             msg='The default index to plot should be 0')
            self.assertEqual(self.np_4d_wid._replot_button.description, 'Apply',
                             msg="With plot options, these can be applied.")

    def test__option_representation(self):
        with self.subTest(msg='1D'):
            option_w = self.np_1d_wid._option_representation
            self.assertEqual(len(option_w.children), 0, msg='No plot options for 1D array')

        with self.subTest(msg='2D'):
            option_w = self.np_2d_wid._option_representation
            self.assertEqual(len(option_w.children), 0, msg='No plot options for 2D array')

        with self.subTest(msg='3D'):
            option_w = self.np_3d_wid._option_representation
            self.assertEqual(len(option_w.children), 2, msg='Dim and index plot options for 3D array')
            index_hbox = option_w.children[1]
            self.assertEqual(len(index_hbox.children), 1, msg='One index to choose for a 3D array')

        with self.subTest(msg='4D'):
            option_w = self.np_4d_wid._option_representation
            self.assertEqual(len(option_w.children), 2, msg='Dim and index plot options for 4D array')
            index_hbox = option_w.children[1]
            self.assertEqual(len(index_hbox.children), 2, msg='Two index to choose for a 4D array')

    def test__click_show_data_button(self):
        # use a fake_out since everything directed to the widgets.Output() is redirected to sys.stdout in the tests
        with unittest.mock.patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.np_1d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.assertTrue('[0 1 2 3 4 5 6 7 8 9]' in fake_out.getvalue())
        self.assertEqual(self.np_1d_wid._header.children, tuple([self.np_1d_wid._show_plot_button]))

        with self.subTest('2D'):
            self.np_2d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.assertEqual(self.np_2d_wid._header.children, tuple([self.np_2d_wid._show_plot_button]))

        with self.subTest('3D'):
            self.np_3d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.assertEqual(self.np_3d_wid._header.children, tuple([self.np_3d_wid._show_plot_button]))

        with self.subTest('4D'):
            self.np_4d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.assertEqual(self.np_4d_wid._header.children, tuple([self.np_4d_wid._show_plot_button]))

    def test__click_replot_button(self):
        with self.subTest('1D'):
            self.np_1d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.np_1d_wid._click_replot_button('NoButtonSinceNotUsed')
            header = self.np_1d_wid._header
            hbox_children = header.children[0].children
            self.assertIs(hbox_children[0], self.np_1d_wid._show_data_button)
            self.assertIs(hbox_children[1], self.np_1d_wid._replot_button)

        with self.subTest('2D'):
            self.np_2d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.np_2d_wid._click_replot_button('NoButtonSinceNotUsed')
            header = self.np_2d_wid._header
            hbox_children = header.children[0].children
            self.assertIs(hbox_children[0], self.np_2d_wid._show_data_button)
            self.assertIs(hbox_children[1], self.np_2d_wid._replot_button)

        with self.subTest('3D'):
            self.np_3d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.np_3d_wid._click_replot_button('NoButtonSinceNotUsed')
            header_children = self.np_3d_wid._header.children
            self.assertIsInstance(header_children[0], widgets.VBox)
            self.assertIsInstance(header_children[1], widgets.VBox)
            buttons = header_children[1].children
            self.assertIs(buttons[0], self.np_3d_wid._show_data_button)
            self.assertIs(buttons[1], self.np_3d_wid._replot_button)

        with self.subTest('4D'):
            self.np_4d_wid._click_show_data_button('NoButtonSinceNotUsed')
            self.np_4d_wid._click_replot_button('NoButtonSinceNotUsed')
            header_children = self.np_4d_wid._header.children
            self.assertIsInstance(header_children[0], widgets.VBox)
            self.assertIsInstance(header_children[1], widgets.VBox)
            buttons = header_children[1].children
            self.assertIs(buttons[0], self.np_4d_wid._show_data_button)
            self.assertIs(buttons[1], self.np_4d_wid._replot_button)

    def test__plot_array(self):
        """Only testing additional/special cases here"""
        with self.subTest("2D with len=1"):
            self.np_1d_wid._plot_array()
            plotted_array_1d = self.np_1d_wid._ax.lines[0].get_xydata()

            np_2d_wid_len_1 = NumpyWidget(np.reshape(np.arange(10), (1, 10)))
            plotted_array_2d = np_2d_wid_len_1._ax.lines[0].get_xydata()
            self.assertTrue(np.allclose(plotted_array_1d, plotted_array_2d),
                            msg="2D arrays with len=1 should behave as a 1D array")

        with self.subTest("3D without _plot_options"):
            plotted_array_init = self.np_3d_wid._ax.lines[0].get_xydata()
            self.np_3d_wid._plot_options = None
            self.np_3d_wid._plot_array()
            self.assertTrue(np.allclose(self.np_3d_wid._ax.lines[0].get_xydata(), plotted_array_init))

        with self.subTest(msg="Trigger 'Error'"):
            with unittest.mock.patch('sys.stdout', new=io.StringIO()) as fake_out:
                self.np_4d_wid._plot_options['dim'].value = [0]
                self.np_4d_wid._plot_array()
                self.assertTrue('Error: You need to select exactly two dimensions.' in fake_out.getvalue())


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
            self.assertIsInstance(self.output._display_obj, widgets.VBox)
        except ImportError:
            print("No nglview installed, test skipped")

    def test_display_numpy_array(self):
        array = np.array([[[[1, 0, 0]]]])
        self.output.display(array)
        self.assertIsInstance(self.output._display_obj, NumpyWidget)

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
        self.output._display_obj = nb
        ret = self.output._output_conv()
        self.assertEqual(type(ret).__name__, 'HTML')

    def test__output_conv_dict(self):
        self.output._display_obj = {'some': "dict"}
        ret = self.output._output_conv()
        self.assertEqual(type(ret).__name__, 'DataFrame')

    def test__output_conv_number(self):
        self.output._debug = True
        self.output._display_obj = 1
        self.assertEqual(self.output._output_conv(), '1')
        self.output._display_obj = 1.0
        self.assertEqual(self.output._output_conv(), '1.0')

    def test__output_conv_list_of_str(self):
        self.output._display_obj = ['1', '2']
        ret = self.output._output_conv()
        self.assertEqual(ret, '12')
        to_long_list_of_str = [str(i) for i in range(2100)]
        self.output._display_obj = to_long_list_of_str
        ret = self.output._output_conv()
        self.assertEqual(ret, ''.join(to_long_list_of_str[:2000]) +
                         os.linesep + ' .... file too long: skipped ....')

    def test__output_conv_list(self):
        self.output._display_obj = [1, 2, 3]
        ret = self.output._output_conv()
        self.assertEqual(type(ret).__name__, 'DataFrame')

    def test__output_conv_image(self):
        img_file = os.path.join(self.project.path, 'some.tiff')
        plt.imsave(img_file,
                   np.array([[0, 100, 255], [100, 0,   0], [50, 50,  255], [255, 0,  255]], dtype=np.uint8))
        tiff_img = self.project['some.tiff']
        self.assertEqual(type(tiff_img).__name__, 'TiffImageFile')
        self.output._display_obj = tiff_img
        ret = self.output._output_conv()
        self.assertEqual(type(ret).__name__, 'Image')
        del tiff_img
        os.remove(img_file)

    def test__output_conv__repr_html_(self):
        class AnyClass:
            def _repr_html_(self):
                pass
        self.output._display_obj = AnyClass()
        self.assertIsInstance(self.output._output_conv(), AnyClass)

    def test__output_conv__else(self):
        class AnyClass:
            pass
        self.output._display_obj = AnyClass()
        self.assertIsInstance(self.output._output_conv(), AnyClass)
