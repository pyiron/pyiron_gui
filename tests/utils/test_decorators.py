# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import unittest

import ipywidgets as widgets

from pyiron_gui.utils.decorators import _BusyCheck, clickable

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


class TestClickable(unittest.TestCase):

    @clickable
    def _decorated_function(self):
        return 5

    @staticmethod
    @clickable
    def _decorated_static_function():
        return 5

    def test_clickable_as_decorator(self):
        with self.subTest('normal'):
            self.assertEqual(self._decorated_function(), 5)
            self.assertEqual(self._decorated_function(None), 5)
        with self.subTest('staticmethod'):
            self.assertEqual(self._decorated_function(), 5)
            self.assertEqual(self._decorated_function(None), 5)

    def test_clickable(self):
        def dummy():
            return 10

        function = clickable(dummy)
        self.assertEqual(function(), 10)
        self.assertEqual(function(None), 10)

    def test_clickable_2_args(self):
        def func_with_2_args(a, b):
            return [a, b]

        self.assertRaises(ValueError, clickable, func_with_2_args)

    def test_clickable_default_args(self):
        def func_with_default_args(a, b=5):
            return [a, b]

        self.assertRaises(ValueError, clickable, func_with_default_args)

    def test_clickable_undefined_number_of_args(self):
        def func_with_undefined_number_of_args(*args):
            pass

        self.assertRaises(ValueError, clickable, func_with_undefined_number_of_args)

    def test_clickable_undefined_number_of_kwargs(self):
        def func_with_undefined_number_of_kwargs(**kwargs):
            pass

        self.assertRaises(ValueError, clickable, func_with_undefined_number_of_kwargs)

    def test_clickable_func_with_arg_and_kwargs(self):
        def func_with_arg_and_kwargs(a, *, b=5):
            return [a, b]

        function = clickable(func_with_arg_and_kwargs)
        self.assertEqual(function(2), [2, 5], msg='Normal behavior retained.')
        self.assertEqual(function(2, None), [2, 5], msg='Swallow provided extra argument.')
        self.assertEqual(function(2, b=3), [2, 3], msg='Normal behavior with keyword argument retained.')
        self.assertEqual(function(2, None, b=3), [2, 3], msg='Swallow provided extra argument with followed keyword '
                                                             'argument.')

    def test_clickable_func_with_kwargs(self):
        def func_with_kwargs(*, a=1, b=5):
            return [a, b]

        function = clickable(func_with_kwargs)
        self.assertEqual(function(), [1, 5], msg='Normal behavior without arguments.')
        self.assertEqual(function(b=3), [1, 3], msg='Normal behavior with kw-argument.')
        self.assertEqual(function(b=3, a=5), [5, 3], msg='Normal behavior with all kw-arguments.')
        self.assertEqual(function(None), [1, 5], msg='Swallow extra argument - no kw-argument.')
        self.assertEqual(function(None, b=3), [1, 3], msg='Swallow extra argument - one kw-argument.')
        self.assertEqual(function(None, b=3, a=5), [5, 3], msg='Swallow extra argument - all kw-argument.')
