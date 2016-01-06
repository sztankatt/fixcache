import filemanagement


class Cache():
    hit = 0
    miss = 1

    def __init__(self, size):
        self.size = size
        self.element_num = 0
        self.file_set = set()

    def _remove(self):
        pass

    def add(self, file_):
        if file_ in self.file_set:
            return hit
        else:
