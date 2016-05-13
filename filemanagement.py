"""
Filemanagement module used by Repository.

It handles the backend for Fixcache file management.
"""
import heapq
import logging
import helper_functions
from helper_functions import DeprecatedError
import random


class IFilemanagementError(Exception):
    """FilemanagementError interface."""

    def __init__(self, value):
        """Overwrite default init."""
        self.value = value

    def __str__(self):
        """Overwrite default string repr."""
        return repr(self.value)


class DistanceError(IFilemanagementError):
    """Simple distanceerror."""

    pass


class FileError(IFilemanagementError):
    """Simple fileerror."""

    pass


class FileSetError(IFilemanagementError):
    """Error used by the FileSet class."""

    pass


class DistanceSetError(IFilemanagementError):
    """Error used by the DistanceSet class."""

    pass


class File(object):
    """File object used by the FileSet class.

    Represents a file in the fixcache algorithms backend.
    """

    def __init__(self, path, commit=0, line_count=0):
        """File initialization."""
        try:
            self.path = path
            self.faults = 0
            self.changes = 0
            self.last_found = commit
            self.line_count = line_count
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during initialization of file")

    def __str__(self):
        """File string representation."""
        return self.path

    @property
    def path(self):
        """The absolute path to a File in the repository."""
        return self._path

    @path.setter
    def path(self, value):
        if value == "":
            raise ValueError("Path of a File cannot be empty")
        self._path = value

    @property
    def line_count(self):
        """The line count of a file. This value evolves."""
        return self._line_count

    @line_count.setter
    def line_count(self, value):
        self._line_count = value

    @property
    def faults(self):
        """The number of faults for a file. This value evolves."""
        return self._faults

    @faults.setter
    def faults(self, value):
        if value < 0:
            raise ValueError("A File cannot have negative number of faults")
        self._faults = value

    @property
    def changes(self):
        """The number of changes for a file. This value evolves."""
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
        """The last commit number when the file was found."""
        return self._last_found

    @last_found.setter
    def last_found(self, value):
        if value < 0:
            raise ValueError("Last-found Commit number cannot be negative")
        self._last_found = value

    def changed(self, commit):
        """Called when file was changed."""
        try:
            self.changes += 1
            self.last_found = commit
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during calling change() on file")

    def fault(self, commit):
        """Called when file had a fault."""
        try:
            self.faults += 1
        except ValueError as ve:
            logging.warning(ve)
            raise FileError("Error during calling fault() on file")

    def reset(self, line_count=0):
        """Reset the given file, called when analysis restarted."""
        self.changes = 0
        self.last_found = 0
        self.faults = 0
        self.line_count = line_count


class FileSet:
    """FileSet object, an abstract view of files used by Fixcache."""

    def __init__(self):
        """Initialization of the class."""
        self.files = {}

    def get_or_create_file(self, file_path, commit_num=0, line_count=0):
        """Return the file by file path. If not present, create one."""
        created = True
        if file_path not in self.files:
            try:
                f = File(file_path, commit=commit_num, line_count=line_count)
            except FileError as fe:
                logging.warning(fe)
                raise FileSetError("Error during calling get_file()")
            self.files[file_path] = f
            f.changed(commit_num)
            return (created, f)
        else:
            created = False
            return (created, self.files[file_path])

    def get_multiple(self, files):
        """Return multiple files by a list of file paths."""
        raise DeprecatedError
        return_list = [self.get_or_create_file(path)[1] for path in files]

        return return_list

    def reset(self):
        """Reset all the files in the set."""
        for file_ in self.files:
            file_.reset()

    def file_in(self, file_):
        """Check whether a file is present in the set."""
        return file_ in self.files

    def get_and_update_multiple(self, git_stat, commit_num):
        """Receive git stat as an input, returns the file objects."""
        files = []
        for path in git_stat:
            created, file_ = self.get_or_create_file(
                file_path=path, commit_num=commit_num)
            line_change = (git_stat[path]['insertions'] -
                           git_stat[path]['deletions'])
            file_.line_count += line_change
            if created:
                files.append(('created', file_))
            else:
                if file_.line_count == 0:
                    files.append(('deleted', file_))
                else:
                    files.append(('changed', file_))
                    file_.changed(commit_num)

        return files

    def get_existing_multiple(self, git_stat):
        """Return files from git_stat, only returns files which exist.

        Used by windowed repository only.
        """
        files = []
        for path in git_stat:
            if path in self.files:
                file_ = self.files[path]
                files.append(file_)

        return files

    def remove_files(self, files):
        """Remove several files from FileSet object."""
        for file_ in files:
            if file_.path in self.files:
                del self.files[file_.path]

    def changed_several(self, files, commit):
        """Change several files in FileSet object."""
        for file_ in files:
            file_.changed(commit)

    def get_random(self, size):
        """Get random subset of files."""
        if size > len(self.files):
            size = len(self.files)

        return random.sample(self.files, size)


class Distance(object):
    """An abstract view of the distance object.

    Stores two file pointers to two files, and their co-occurrence.
    """

    def __init__(self, file1_in, file2_in):
        """Initialization."""
        self.files = {
            'file1': file1_in,
            'file2': file2_in
        }
        self.occurrence_list = []

    def reset(self):
        """Reset the distance between two files."""
        del self.occurrence_list
        self.occurrence_list = []

    def increase_occurrence(self, commit):
        """Increse the occurrence.

        Called when two files are present together in a commit.
        """
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
        """Return the distance which is 1/occurrence."""
        raise DeprecatedError
        try:
            occurrence = self.get_occurrence(commit)
            return 1.0 / float(occurrence)
        except ZeroDivisionError as zde:
            logging.warning(zde)
            raise DistanceError(
                "Division by zero occurred during get_distance()." +
                "The occurrence is 0")

    def get_occurrence(self, commit=None):
        """Return the occurence for a commit number in linear time."""
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
        """Given a file path return the other file in the distance."""
        if self.files['file1'].path == file_in.path:
            return self.files['file2']
        elif self.files['file2'].path == file_in.path:
            return self.files['file1']
        else:
            raise DistanceError(
                'The file with path: %s is not in this Distance object'
                % (file_in,))


class DistanceSet(object):
    """An abstract view of the set of distances used by Fixcache."""

    def __init__(self):
        """Initialization."""
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

    def _get_distances_for_files(self, file_):
        distances_for_file = filter(
            lambda x: file_ in x.files.itervalues(), self.distance_set)

        return distances_for_file

    def _get_and_sort_occurrences_for_file(self, file_, commit=None):
        raise DeprecatedError
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
        """Return the occurrence between two files."""
        distance, created = self._get_or_create_distance(file1, file2)

        return distance.get_occurrence(commit)

    def add_occurrence(self, file1, file2, commit):
        """Add occurrence between two files."""
        distance, created = self._get_or_create_distance(file1, file2)

        try:
            distance.increase_occurrence(commit)
        except DistanceError as de:
            logging.warning(de)
            raise DistanceSetError("Error during add_occurrence()")

    def get_closest_files(self, file_, number, commit=None):
        """Given a file returns the closest files."""
        ds = self._get_distances_for_files(file_)

        closest_files = helper_functions.get_top_elements(
            [(x.get_occurrence(commit), x.get_other_file(file_)) for x in ds],
            number)

        return [x[1] for x in closest_files]

    def reset(self):
        """Reset the distance set object."""
        for distance in self.distance_set:
            distance.reset()

    def remove_files(self, files):
        """Remove distances associated with a file."""
        for file_ in files:
            file_distances = self._get_distances_for_files(file_)
            for distance in file_distances:
                distance_key = self._get_distance_key(
                    distance.files['file1'], distance.files['file2'])
                self.distance_set.discard(distance)
                del self.distance_dict[distance_key]
                del distance
