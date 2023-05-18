import unittest

from statetree import StateTree


class StateTreeTests(unittest.TestCase):
    def test_new_empty_tree_is_clean(self):
        tree = StateTree()
        self.assertEqual(dict(), tree.dictionary)
        self.assertFalse(tree.changed)

    def test_setting_item_dirties_tree(self):
        tree = StateTree()
        tree["foo"] = "bar"
        self.assertEqual({"foo": "bar"}, tree.dictionary)
        self.assertTrue(tree.changed)

    def test_setting_an_equivalent_value_does_not_dirty_tree(self):
        tree = StateTree({"foo": "bar"})
        tree["foo"] = "bar"
        self.assertFalse(tree.changed)

    def test_setting_nested_item_dirties_parent(self):
        tree = StateTree({"foo": {"bar": "baz"}})
        tree["foo"]["bar"] = "changed"
        self.assertEqual({"foo": {"bar": "changed"}}, tree.dictionary)
        self.assertTrue(tree.changed)

    def test_dirtying_sets_changed_status(self):
        tree = StateTree()
        tree.dirty()
        self.assertTrue(tree.changed)

    def test_cleaning_removes_changed_status(self):
        tree = StateTree()
        tree.dirty()
        tree.clean()
        self.assertFalse(tree.changed)
