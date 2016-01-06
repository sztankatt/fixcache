#! /usr/bin/env python
import unittest
from fixcache import filemanagement


class FilemanagementTestCase(unittest.TestCase):
    def setUp(self):
        self.file1 = filemanagement.File('patha')
        self.file2 = filemanagement.File('pathb')
        self.file3 = filemanagement.File('pathc')
        self.file4 = filemanagement.File('patha')
        self.distance = filemanagement.Distance(self.file1, self.file2, 0)

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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(FilemanagementTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
