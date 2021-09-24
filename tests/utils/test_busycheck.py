# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import unittest

import ipywidgets as widgets

from pyiron_gui.utils.busy_check import _BusyCheck

busy_check = _BusyCheck()


class TestBusyCheck(unittest.TestCase):

    def setUp(self):
        self.function_run_counter = 0

    @busy_check()
    def _busy_function(self):
        self.assertTrue(busy_check.busy)
        self.function_run_counter += 1

    def test_busy_check_decorator(self):
        self.assertFalse(busy_check.busy)
        self._busy_function()
        self.assertFalse(busy_check.busy)
        self.assertEqual(self.function_run_counter, 1)
        self._busy_function()
        self.assertFalse(busy_check.busy)
        self.assertEqual(self.function_run_counter, 2)

    @busy_check()
    def test_busy_check_while_busy(self):
        self.assertTrue(busy_check.busy)
        self._busy_function()
        self.assertTrue(busy_check.busy)
        self.assertEqual(self.function_run_counter, 0)

    def test__busy_check(self):
        self.assertFalse(busy_check.busy)
        busy_check._busy_check()
        self.assertTrue(busy_check.busy)
        self.assertTrue(busy_check._busy_check())
        self.assertTrue(busy_check.busy)
        busy_check._busy_check(False)
        self.assertFalse(busy_check.busy)

    def test_widget_deactivation(self):
        button = widgets.Button(description="Button")
        self.assertFalse(button.disabled)
        busy_check.busy = True
        self.assertTrue(button.disabled)
        busy_check.busy = False
        self.assertFalse(button.disabled)
