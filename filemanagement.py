import heapq
import logging


class iFilemanagementError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class DistanceError(iFilemanagementError):
    pass


class FileError(iFilemanagementError):
    pass


class FileSetError(iFilemanagementError):
    pass


class DistanceSetError(iFilemanagementError):
    pass


class File(object):
    def __init__(self, path, commit=0):
        try:
            self.path = path
            self.faults = 0
            self.changes = 0
            self.last_found = commit
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during initialization of file")

    def __str__(self):
        return self.path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == "":
            raise ValueError("Path of a File cannot be empty")
        self._path = value

    @property
    def faults(self):
        return self._faults

    @faults.setter
    def faults(self, value):
        if value < 0:
            raise ValueError("A File cannot have negative number of faults")
        self._faults = value

    @property
    def changes(self):
        return self._changes

    @changes.setter
    def changes(self, value):
        if value < 0:
            raise ValueError(
                "Number of changes cannot be negative for %s" %
                (value,))
        self._changes = value

    @property
    def last_found(self):
        return self._last_found

    @last_found.setter
    def last_found(self, value):
        if value < 0:
            raise ValueError("Last-found Commit number cannot be negative")
        self._last_found = value

    def changed(self, commit):
        try:
            self.changes += 1
            self.last_found = commit
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during calling change() on file")

    def fault(self, commit):
        try:
            self.changes += 1
            self.last_found = commit
            self.faults += 1
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during calling fault() on file")

    def reset(self):
        self.changes = 0
        self.last_found = 0
        self.faults = 0


class FileSet:
    def __init__(self):
        self.files = {}

    def get_file(self, file_path):
        if file_path not in self.files:
            try:
                f = File(file_path)
            except FileError as fe:
                logging.warning(fe)
                raise FileSetError("Error during calling get_file()")
            self.files[file_path] = f
            return f
        else:
            return self.files[file_path]

    def get_multiple(self, files):
        return_list = [self.get_file(path) for path in files]

        return return_list

    def reset(self):
        for file_ in self.files:
            self.files[file_].reset()


class Distance(object):
    def __init__(self, file1_in, file2_in):
        # storing the file with longer path as the first one
        self.files = {
                'file1': file1_in,
                'file2': file2_in
            }
        self.occurrence_list = []

    def reset(self):
        del self.occurrence_list
        self.occurrence_list = []

    def increase_occurrence(self, commit):
        if commit < 0:
            raise DistanceError("commit cannot be negative")

        if len(self.occurrence_list) == 0:
            self.occurrence_list.append(commit)
            return

        if commit not in self.occurrence_list:
            if commit < self.occurrence_list[-1]:
                for i in range(len(self.occurrence_list)):
                    if self.occurrence_list[i] > commit:
                        self.occurrence_list.insert(i, commit)
                        break
            else:
                self.occurrence_list.append(commit)

    def get_distance(self, commit=None):
        """hash or int? if hash, how to know if between which commits is
        the current one is there an order of commits in github? -> check this
        If int, how to trace back the int of a parent commit?
        """
        try:
            occurrence = self.get_occurrence(commit)
            return 1.0/float(occurrence)
        except ZeroDivisionError as zde:
            logging.warning(zde)
            raise DistanceError(
                "Division by zero occurred during get_distance()." +
                "The occurrence is 0")

    def get_occurrence(self, commit=None):
        # Getting the occurence for a commit number in linear time
        if commit is None:
            return len(self.occurrence_list)

        counter = 0
        for commit_num in self.occurrence_list:
            if commit_num > commit:
                return counter
            elif commit_num == commit:
                return counter + 1
            else:
                counter += 1

        return counter

    def get_other_file(self, file_in):
        if self.files['file1'].path == file_in.path:
            return self.files['file2']
        elif self.files['file2'].path == file_in.path:
            return self.files['file1']
        else:
            raise DistanceError(
                'The file with path: %s is not in this Distance object'
                % (file_in,))


class DistanceSet(object):
    def __init__(self):
        self.distance_set = set()
        self.distance_dict = {}

    def _get_distance_key(self, file1, file2):
        if file1.path > file2.path:
            return file1.path + file2.path
        elif file1.path < file2.path:
            return file2.path + file2.path
        else:
            raise DistanceSetError(
                "_get_distance_key() arguments should be distinct files")

    def _get_or_create_distance(self, file1, file2):
        key = self._get_distance_key(file1, file2)

        if key in self.distance_dict:
            return (self.distance_dict[key], False)
        else:
            try:
                distance = Distance(file1, file2)
                self.distance_set.add(distance)
                self.distance_dict[key] = distance

                return (distance, True)
            except DistanceError as de:
                logging.warning(de)
                raise DistanceSetError(
                    "Error during _get_or_create_distance()")

    def _get_occurrences_for_file(self, file_, commit=None):
        ds_for_file = filter(
            lambda x: file_ in x.files.itervalues(), self.distance_set)

        distances = []

        for distance in ds_for_file:
            occurrence = distance.get_occurrence(commit)
            if occurrence > 0:
                try:
                    distances.append(
                        (-occurrence, distance.get_other_file(file_)))
                except DistanceError as de:
                    logging.warning(de)
                    raise DistanceSetError(
                        "Error during _get_occurrences_for_file()")

        heapq.heapify(distances)

        return distances

    def get_occurrence(self, file1, file2, commit=None):
        distance, created = self._get_or_create_distance(file1, file2)

        return distance.get_occurrence(commit)

    def add_occurrence(self, file1, file2, commit):
        distance, created = self._get_or_create_distance(file1, file2)

        try:
            distance.increase_occurrence(commit)
        except DistanceError as de:
            logging.warning(de)
            raise DistanceSetError("Error during add_occurrence()")

    def get_closest_files(self, file_, number, commit=None):
        distance_heap = self._get_occurrences_for_file(file_, commit)
        if len(distance_heap) < number:
            number = len(distance_heap)

        files = [heapq.heappop(distance_heap)[1] for i in range(number)]

        return files

    def reset(self):
        for distance in self.distance_set:
            distance.reset()
