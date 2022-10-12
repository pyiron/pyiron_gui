import unittest
import warnings
import sys

from pyiron_base import DataContainer, HasGroups, Project


class HasGroupsImplementation(HasGroups):
    def __getitem__(self, key):
        pass

    def _list_groups(self):
        return []

    def _list_nodes(self):
        return []


class TestMonkeyPatching(unittest.TestCase):
    def test_base_classes(self):

        with self.subTest('Before explicit pyiron_gui import'):
            if "pyiron_gui" not in sys.modules:
                self.assertFalse(hasattr(DataContainer, 'gui'))
                self.assertFalse(hasattr(HasGroups, 'gui'))
                self.assertFalse(hasattr(Project, 'browser'))
        from pyiron_gui import DataContainerGUI, ProjectBrowser, HasGroupsBrowser
        import pyiron_gui.monkey_patching
        with self.subTest('DataContainer'):
            self.assertTrue(hasattr(DataContainer, 'gui'))
            dc_gui = DataContainer().gui()
            self.assertIsInstance(dc_gui, DataContainerGUI)
        with self.subTest('Project'):
            self.assertTrue(hasattr(Project, 'browser'))
            pr_browser = Project('.').browser
            self.assertIsInstance(pr_browser, ProjectBrowser)
        with self.subTest('HasGroups'):
            self.assertTrue(hasattr(HasGroups, 'gui'))
            hg_gui = HasGroupsImplementation().gui()
            self.assertIsInstance(hg_gui, HasGroupsBrowser)

    def test_safe_monkey_patch(self):
        class ToBePatched:
            pass

        def to_be_applied(cls_instance):
            return cls_instance.v

        def not_to_be_applied(cls_instance):
            return cls_instance.v

        from pyiron_gui.monkey_patching import safe_monkey_patch

        with warnings.catch_warnings(record=True) as w:
            safe_monkey_patch(ToBePatched, 'any', to_be_applied, 'v', None)
            self.assertTrue(len(w) == 0, f"Unexpected warnings {[wi.message for wi in w]}")

        patched_instance = ToBePatched()
        self.assertIsNone(patched_instance.v)
        self.assertTrue(hasattr(patched_instance, 'any'))
        self.assertTrue(callable(patched_instance.any))
        self.assertIsNone(patched_instance.any())

        with self.subTest('Rewrite with same name and object'):
            with warnings.catch_warnings(record=True) as w:
                safe_monkey_patch(ToBePatched, 'any', to_be_applied, 'v', None)
                self.assertEqual(len(w), 0, f"Unexpected warnings {[wi.message for wi in w]}")

        with self.subTest('Not rewrite with different names'):
            with warnings.catch_warnings(record=True) as w:
                safe_monkey_patch(ToBePatched, 'any', not_to_be_applied, 'v', 'Should not be stored')
                self.assertEqual(len(w), 1)
                self.assertIs(ToBePatched.any, to_be_applied)
                self.assertIsNone(ToBePatched.v)
