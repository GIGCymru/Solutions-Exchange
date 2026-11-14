"""Tests for the solution.json metadata standard."""

import unittest

from solution_metadata import (
    LIFECYCLE_STAGES,
    METADATA_PATHS,
    parse_solution_metadata,
    validate_solution_metadata,
)


class ValidateSolutionMetadataTests(unittest.TestCase):
    def test_accepts_a_minimal_valid_document(self):
        cleaned, errors = validate_solution_metadata({'contact': 'team@wales.nhs.uk'})

        self.assertEqual(errors, [])
        self.assertEqual(cleaned, {'contact': 'team@wales.nhs.uk'})

    def test_requires_a_contact(self):
        cleaned, errors = validate_solution_metadata({'summary': 'Something useful'})

        self.assertIn("missing required field 'contact'", errors)
        self.assertEqual(cleaned['summary'], 'Something useful')

    def test_rejects_a_non_object_payload(self):
        cleaned, errors = validate_solution_metadata(['not', 'an', 'object'])

        self.assertEqual(cleaned, {})
        self.assertEqual(errors, ['solution metadata must be a JSON object'])

    def test_normalises_lifecycle_and_support_case(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'lifecycle': 'Live',
            'support': 'Best-Effort',
        })

        self.assertEqual(errors, [])
        self.assertEqual(cleaned['lifecycle'], 'live')
        self.assertEqual(cleaned['support'], 'best-effort')

    def test_drops_lifecycle_values_outside_the_vocabulary(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'lifecycle': 'experimental',
        })

        self.assertNotIn('lifecycle', cleaned)
        self.assertTrue(any('experimental' in error for error in errors))

    def test_one_bad_field_does_not_discard_the_good_ones(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'benefits': 'should have been a list',
            'summary': 'Still useful',
        })

        self.assertEqual(cleaned['contact'], 'team@wales.nhs.uk')
        self.assertEqual(cleaned['summary'], 'Still useful')
        self.assertNotIn('benefits', cleaned)
        self.assertTrue(any('benefits' in error for error in errors))

    def test_reports_and_drops_unknown_fields(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'favourite_colour': 'blue',
        })

        self.assertNotIn('favourite_colour', cleaned)
        self.assertIn("unknown field 'favourite_colour'", errors)

    def test_strips_blank_entries_from_lists(self):
        cleaned, _ = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'benefits': ['Real benefit', '   ', '', 'Another benefit'],
        })

        self.assertEqual(cleaned['benefits'], ['Real benefit', 'Another benefit'])

    def test_omits_a_list_that_is_empty_after_cleaning(self):
        cleaned, _ = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'dependencies': ['  ', ''],
        })

        self.assertNotIn('dependencies', cleaned)

    def test_truncates_an_overlong_summary_but_keeps_it(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'summary': 'x' * 400,
        })

        self.assertEqual(len(cleaned['summary']), 300)
        self.assertTrue(any('summary is 400 characters' in error for error in errors))

    def test_flags_a_contact_that_is_not_an_address_or_handle(self):
        cleaned, errors = validate_solution_metadata({'contact': 'ask Dave'})

        # Still published, so a near-miss is not silently lost, but flagged.
        self.assertEqual(cleaned['contact'], 'ask Dave')
        self.assertTrue(any('contact' in error for error in errors))

    def test_treats_null_as_absent(self):
        cleaned, errors = validate_solution_metadata({
            'contact': 'team@wales.nhs.uk',
            'summary': None,
        })

        self.assertNotIn('summary', cleaned)
        self.assertEqual(errors, [])


class ParseSolutionMetadataTests(unittest.TestCase):
    def test_parses_valid_json(self):
        cleaned, errors = parse_solution_metadata('{"contact": "team@wales.nhs.uk"}')

        self.assertEqual(errors, [])
        self.assertEqual(cleaned['contact'], 'team@wales.nhs.uk')

    def test_reports_invalid_json_without_raising(self):
        cleaned, errors = parse_solution_metadata('{ not json')

        self.assertEqual(cleaned, {})
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid JSON', errors[0])


class StandardShapeTests(unittest.TestCase):
    def test_root_path_is_preferred_over_the_github_directory(self):
        self.assertEqual(METADATA_PATHS[0], 'solution.json')
        self.assertIn('.github/solution.json', METADATA_PATHS)

    def test_lifecycle_vocabulary_is_ordered_from_idea_to_retired(self):
        self.assertEqual(LIFECYCLE_STAGES[0], 'idea')
        self.assertEqual(LIFECYCLE_STAGES[-1], 'retired')


if __name__ == '__main__':
    unittest.main()
