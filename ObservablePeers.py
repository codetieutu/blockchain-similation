class ObservablePeers(set):
    def __init__(self, *args):
        super().__init__(*args)
        self._subs = []

    def subscribe(self, cb):
        self._subs.append(cb)

    def _notify(self):
        for cb in self._subs:
            cb()

    def add(self, element):
        before = len(self)
        super().add(element)
        if len(self) != before:
            self._notify()

    def discard(self, element):
        existed = element in self
        super().discard(element)
        if existed:
            self._notify()

    def update(self, *others):
        before = len(self)
        super().update(*others)
        if len(self) != before:
            self._notify()

    def clear(self):
        if len(self) > 0:
            super().clear()
            self._notify()
