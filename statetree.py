class StateTree:
    """A dictionary-like object that tracks when values have been changed."""

    def __init__(self, dictionary: dict = None, parent: "StateTree" = None) -> None:
        """Create a new state tree.

        If a dictionary is supplied, its values will be initialized with it and
        the tree will be marked as clean.

        If a parent is supplied, the parent will be marked as dirty when this
        tree is modified.

        """
        self._dictionary = dictionary if dictionary else dict()
        self._parent = parent
        self._changed = False

    def dirty(self):
        """Mark the tree as dirty.

        This is done automatically whenever an item is updated.

        """
        self._changed = True
        if self._parent:
            self._parent.dirty()

    def clean(self):
        """Mark the tree as clean.

        Use this method to reset the changed status of the tree once after
        you've reacted to it being updated.

        """
        self._changed = False

    @property
    def changed(self):
        """Returns whether the tree has been modified since the last time it was
        marked as clean."""
        return self._changed

    @property
    def dictionary(self):
        """Returns the underlying dictionary."""
        return self._dictionary

    def __getitem__(self, *args, **kwargs):
        """Get the value stored in a key in the tree.

        If the value is a dictionary, returns a StateTree object instead that
        will notify the parent if a change is made.

        """
        o = self._dictionary.__getitem__(*args, **kwargs)
        if isinstance(o, dict):
            return StateTree(o, parent=self)
        else:
            return o

    def __setitem__(self, key, value):
        """Update the value of a key in the tree.

        Marks the tree as changed if the key is new or the new value differs
        from the current value.

        """
        if key not in self._dictionary or value != self._dictionary[key]:
            self.dirty()
        self._dictionary[key] = value

    def __repr__(self):
        return "<StateTree{}{} {}>".format(
            "^" if self._parent else "",
            "*" if self._changed else "",
            repr(self._dictionary),
        )
