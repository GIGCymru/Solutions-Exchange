"""Tests for the data quality report."""

import json
import os
import tempfile
import unittest

from data_quality_report import build_report, load_repositories


def repo(**overrides):
    base = {
        'full_name': 'GIGCymru/example',
        'description': 'A useful solution',
        'license': {'key': 'mit'},
        'topics': ['nhs'],
        'language': 'Python',
    }
    base.update(overrides)
    return base


class TestBuildReport(unittest.TestCase):
    def test_counts_missing_metadata(self):
        report = build_report([
            repo(),
            repo(full_name='GIGCymru/no-desc', description=''),
            repo(full_name='GIGCymru/no-licence', license=None),
            repo(full_name='GIGCymru/no-topics', topics=[]),
        ])

        self.assertEqual(report['total_repositories'], 4)
        self.assertEqual(report['counts']['missing_description'], 1)
        self.assertEqual(report['counts']['missing_licence'], 1)
        self.assertEqual(report['counts']['missing_topics'], 1)
        self.assertEqual(report['offenders']['missing_description'], ['GIGCymru/no-desc'])

    def test_whitespace_description_counts_as_missing(self):
        report = build_report([repo(description='   ')])

        self.assertEqual(report['counts']['missing_description'], 1)

    def test_fully_described_requires_description_licence_and_topics(self):
        report = build_report([repo(), repo(full_name='GIGCymru/partial', topics=[])])

        self.assertEqual(report['fully_described'], 1)
        self.assertEqual(report['fully_described_percentage'], 50.0)

    def test_contact_comes_from_solution_metadata(self):
        report = build_report([
            repo(solution_metadata={'contact': 'digital@wales.nhs.uk'}),
            repo(full_name='GIGCymru/no-contact'),
        ])

        self.assertEqual(report['counts']['missing_contact'], 1)

    def test_empty_dataset_does_not_divide_by_zero(self):
        report = build_report([])

        self.assertEqual(report['total_repositories'], 0)
        self.assertEqual(report['fully_described_percentage'], 0.0)
        self.assertEqual(report['percentages']['missing_topics'], 0.0)


class TestLoadRepositories(unittest.TestCase):
    def test_rejects_non_list_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'repositories.json')
            with open(path, 'w', encoding='utf-8') as handle:
                json.dump({'repositories': []}, handle)

            with self.assertRaisesRegex(ValueError, 'list of repositories'):
                load_repositories(path)


if __name__ == '__main__':
    unittest.main()
