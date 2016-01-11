#! /usr/bin/env python
import unittest
from fixcache import filemanagement
from fixcache import cache


class FilemanagementTestCase(unittest.TestCase):
    def setUp(self):
        self.file1 = filemanagement.File('patha')
        self.file2 = filemanagement.File('pathb')
        self.file3 = filemanagement.File('pathc')
        self.file4 = filemanagement.File('pathd')
        self.file5 = filemanagement.File('pathe')
        self.distance = filemanagement.Distance(self.file1, self.file2, 0)

    def test_file_operations(self):
        self.file1.changed(10)
        self.file1.changed(15)
        self.file2.changed(32)
        self.file2.fault(33)

        self.assertEqual(self.file1.last_found, 15)
        self.assertEqual(self.file1.changes, 3)
        self.assertEqual(self.file1.faults, 0)
        self.assertEqual(self.file2.faults, 1)
        self.assertEqual(self.file2.changes, 3)

    def test_file_in_list(self):
        self.file_list = [self.file1, self.file3]

        self.assertEqual(self.file1 in self.file_list, True)
        self.assertEqual(self.file2 in self.file_list, False)

    def test_distance_init(self):
        f = self.distance.get_other_file(self.file1)

        self.assertEqual(f == self.file2, True)
        with self.assertRaises(filemanagement.DistanceError):
            self.distance.get_other_file(self.file3)

    def test_distance_evolution(self):
        self.assertEqual(self.distance.get_occurrence(0), 1)
        self.assertEqual(self.distance.get_distance(0), 1.0)

        self.distance.increase_occurrence(15)
        self.distance.increase_occurrence(54)

        self.assertEqual(self.distance.get_occurrence(15), 2)
        self.assertEqual(self.distance.get_occurrence(60), 3)

        self.distance.increase_occurrence(15)

        self.assertEqual(self.distance.get_occurrence(), 3)

        self.distance.increase_occurrence(13)

        self.assertEqual(self.distance.get_occurrence(), 4)
        self.assertEqual(self.distance.occurrence_list[1], 13)
        self.assertEqual(self.distance.occurrence_list, [0, 13, 15, 54])

    def test_distance_set(self):
        ds = filemanagement.DistanceSet()

        self.assertEqual(ds.get_occurrence(self.file1, self.file2), 1)

        ds.add_occurrence(self.file1, self.file2, 20)
        ds.add_occurrence(self.file1, self.file2, 31)
        ds.add_occurrence(self.file1, self.file2, 32)

        self.assertEqual(ds.get_occurrence(self.file1, self.file2), 4)

        ds.add_occurrence(self.file1, self.file2, 13)
        ds.add_occurrence(self.file1, self.file3, 1)
        ds.add_occurrence(self.file1, self.file3, 5)
        ds.add_occurrence(self.file1, self.file4, 1)

        self.assertEqual(ds.get_closest_files(self.file1, 1)[0], self.file2)
        self.assertEqual(ds.get_closest_files(self.file1, 8),
                         [self.file2, self.file3, self.file4])


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.file1 = filemanagement.File('patha')
        self.file2 = filemanagement.File('pathb')
        self.file3 = filemanagement.File('pathc')
        self.file4 = filemanagement.File('pathd')
        self.file5 = filemanagement.File('pathe')
        self.cache = cache.SimpleCache(4)
        self.cache.add(self.file1)
        self.cache.add(self.file2)

    def test_cache_init(self):
        with self.assertRaises(ValueError):
            cache.SimpleCache(0)
        with self.assertRaises(ValueError):
            cache.SimpleCache(-1)

        self.assertEqual(self.cache.hit, True)
        self.assertEqual(self.cache.miss, False)

        self.assertEqual(self.cache.size, 4)

    def test_cache_add(self):
        self.assertEqual(self.cache.file_in(self.file1), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file3), self.cache.miss)

    def test_cache_add_multiple(self):
        self.file1.changed(1)
        self.file2.changed(2)
        self.file3.changed(3)
        self.file4.changed(4)
        self.file5.changed(5)
        self.cache.add_multiple([self.file3, self.file4, self.file5])

        self.assertEqual(self.cache.file_in(self.file4), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file5), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file2), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file3), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file1), self.cache.miss)

    def _add_files(self):
        self.file1.changed(50)
        self.file2.changed(30)
        self.file3.fault(32)
        self.file4.fault(15)
        self.file4.changed(21)

        self.cache.add_multiple([self.file4, self.file3])

    def test_cache__remove(self):
        self._add_files()

        self.assertEqual(self.cache._remove(), self.file4)
        self.assertEqual(self.cache._remove(), self.file2)
        self.assertEqual(self.cache._remove(), self.file3)
        self.assertEqual(self.cache._remove(), self.file1)

        self.assertEqual(self.cache._get_free_space(), 4)
        self.assertEqual(self.cache._remove(), None)

        self.cache.add(self.file3)

        self.assertEqual(self.cache._remove(), self.file3)

    def test_cache__remove_multiple(self):
        self._add_files()
        self.cache._remove_multiple(5)

        self.assertEqual(self.cache._get_free_space(), 4)

        self._add_files()

        self.assertEqual(self.cache._get_free_space(), 2)

        self.cache.add(self.file2)
        self.cache._remove_multiple(2)

        self.assertEqual(self.cache.file_in(self.file3), self.cache.hit)
        self.assertEqual(self.cache.file_in(self.file2), self.cache.miss)
        self.assertEqual(self.cache._get_free_space(), 3)

if __name__ == '__main__':
    s1 = unittest.TestLoader().loadTestsFromTestCase(FilemanagementTestCase)
    s2 = unittest.TestLoader().loadTestsFromTestCase(CacheTestCase)
    suite = unittest.TestSuite([s1, s2])
    unittest.TextTestRunner(verbosity=2).run(suite)
