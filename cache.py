import logging


class Cache(object):
    _hit = True
    _miss = False

    def __init__(self, size):
        logging.debug('Cache initialized')
        self.size = size
        self.file_set = set()

    @property
    def hit(self):
        return self._hit

    @property
    def miss(self):
        return self._miss

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if value < 1:
            raise ValueError("Cache size cannot be less than 1")
        self._size = value

    def _filled(self):
        return len(self.file_set) == self.size

    def _find_file_to_remove(self):
        raise NotImplementedError

    def _order_files(self):
        raise NotImplementedError

    def _remove_multiple(self, number=1):
        if number >= self.size:
            # empty the whole file set
            self.file_set = set()
        else:
            remove_file_set = set(self._order_files()[:number])
            self.file_set -= remove_file_set

    def _remove(self):
        len_ = len(self.file_set)

        if len_ < 0:
            return None
        elif len_ == 1:
            file_ = self.file_set.pop()
            return file_
        else:
            file_ = self._find_file_to_remove()
            self.file_set -= {file_}
            return file_

    def _get_free_space(self):
        space = self.size - len(self.file_set)

        assert space >= 0

        return space

    def _preprocess_multiple(self, files, pre_sort=True):
        files = filter(lambda x: x not in self.file_set, files)
        if pre_sort:
            files.sort(key=lambda x: x.last_found, reverse=True)
        return files

    def file_in(self, file_):
        if file_ in self.file_set:
            return self.hit
        else:
            return self.miss

    def add(self, file_):
        if self._filled():
            self._remove()

        self.file_set.add(file_)

    def add_multiple(self, files, pre_sort=True):
        files = self._preprocess_multiple(files, pre_sort)

        len_ = len(files)

        if len_ == 1:
            self.add(files[0])
        elif len_ <= self._get_free_space():
            self.file_set = self.file_set | set(files)
        elif len_ <= self.size:
            to_remove = len_ - self._get_free_space()
            self._remove_multiple(to_remove)
            self.file_set = self.file_set | set(files)
        else:
            self.file_set = set(files[:self.size])

    def remove_files(self, files):
        """Remove several files from the cache. Called for deleted files."""
        for file_ in files:
            self.file_set.discard(file_)

    def flush(self):
        del self.file_set
        self.file_set = set()

    def reset(self, size=None):
        self.flush()

        if size is not None:
            self.size = size


class SimpleCache(Cache):
    """simple cache using least recent used cache remove policy"""
    def _find_file_to_remove(self):
        file_to_remove = None
        for file_ in self.file_set:
            if file_to_remove is None:
                file_to_remove = file_
            else:
                if file_to_remove.last_found > file_.last_found:
                    file_to_remove = file_

        return file_to_remove

    def _order_files(self):
        file_list = list(self.file_set)
        file_list.sort(key=lambda x: x.last_found)

        return file_list
