"""Tests for the repository fetching pipeline, with the GitHub API mocked out."""

import json
import time

import pytest

from conftest import FakeResponse

import update_repositories
from update_repositories import GitHubAPIError, MAX_RETRIES


@pytest.fixture
def recorded_sleeps(fetcher, monkeypatch):
    """Capture how long the fetcher would have waited."""
    sleeps = []
    monkeypatch.setattr(fetcher, '_sleep', lambda seconds: sleeps.append(seconds))
    return sleeps


def patch_responses(monkeypatch, responses):
    """Make requests.get return each queued response in turn."""
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append({'url': url, 'params': params})
        return responses.pop(0)

    monkeypatch.setattr(update_repositories.requests, 'get', fake_get)
    return calls


class TestRequestWithRetry:
    def test_retries_server_error_then_succeeds(self, fetcher, monkeypatch, recorded_sleeps):
        patch_responses(monkeypatch, [
            FakeResponse(status_code=500),
            FakeResponse(status_code=200, json_data=[{'name': 'repo'}]),
        ])

        response = fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert response.status_code == 200
        assert recorded_sleeps == [update_repositories.BACKOFF_BASE_SECONDS]

    def test_waits_for_rate_limit_reset_then_succeeds(self, fetcher, monkeypatch, recorded_sleeps):
        reset_at = time.time() + 30
        patch_responses(monkeypatch, [
            FakeResponse(
                status_code=403,
                headers={'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(reset_at)},
                text='API rate limit exceeded',
            ),
            FakeResponse(status_code=200, json_data=[]),
        ])

        response = fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert response.status_code == 200
        assert len(recorded_sleeps) == 1
        # Waits until the reset moment rather than a flat backoff.
        assert 25 <= recorded_sleeps[0] <= 35

    def test_honours_retry_after_header(self, fetcher, monkeypatch, recorded_sleeps):
        patch_responses(monkeypatch, [
            FakeResponse(status_code=429, headers={'Retry-After': '12'}),
            FakeResponse(status_code=200, json_data=[]),
        ])

        fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert recorded_sleeps == [12.0]

    def test_rate_limit_wait_is_capped(self, fetcher, monkeypatch, recorded_sleeps):
        patch_responses(monkeypatch, [
            FakeResponse(status_code=429, headers={'Retry-After': '999999'}),
            FakeResponse(status_code=200, json_data=[]),
        ])

        fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert recorded_sleeps == [update_repositories.MAX_RATE_LIMIT_WAIT_SECONDS]

    def test_404_is_returned_not_raised(self, fetcher, monkeypatch):
        patch_responses(monkeypatch, [FakeResponse(status_code=404)])

        assert fetcher.request_with_retry('https://api.github.com/orgs/x/repos').status_code == 404

    def test_unexpected_status_raises_immediately(self, fetcher, monkeypatch, recorded_sleeps):
        patch_responses(monkeypatch, [FakeResponse(status_code=401, text='Bad credentials')])

        with pytest.raises(GitHubAPIError, match='401'):
            fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert recorded_sleeps == []

    def test_gives_up_after_max_retries(self, fetcher, monkeypatch, recorded_sleeps):
        patch_responses(monkeypatch, [FakeResponse(status_code=500)] * (MAX_RETRIES + 1))

        with pytest.raises(GitHubAPIError, match='giving up'):
            fetcher.request_with_retry('https://api.github.com/orgs/x/repos')

        assert len(recorded_sleeps) == MAX_RETRIES

    def test_retries_connection_errors(self, fetcher, monkeypatch, recorded_sleeps):
        attempts = []

        def flaky_get(url, headers=None, params=None, timeout=None):
            attempts.append(url)
            if len(attempts) == 1:
                raise update_repositories.requests.exceptions.ConnectionError('boom')
            return FakeResponse(status_code=200, json_data=[])

        monkeypatch.setattr(update_repositories.requests, 'get', flaky_get)

        assert fetcher.request_with_retry('https://api.github.com/orgs/x/repos').status_code == 200
        assert len(attempts) == 2


class TestFetchOrganizationRepositories:
    def test_paginates_and_filters_by_visibility(self, fetcher, monkeypatch):
        page_one = [
            {'name': 'public-repo', 'visibility': 'public'},
            {'name': 'internal-repo', 'visibility': 'internal'},
            {'name': 'private-repo', 'visibility': 'private'},
        ]
        calls = patch_responses(monkeypatch, [
            FakeResponse(status_code=200, json_data=page_one),
            FakeResponse(status_code=200, json_data=[]),
        ])

        repos = fetcher.fetch_organization_repositories('GIGCymru')

        assert [r['name'] for r in repos] == ['public-repo', 'internal-repo']
        assert [c['params']['page'] for c in calls] == [1, 2]

    def test_missing_organization_returns_empty(self, fetcher, monkeypatch):
        patch_responses(monkeypatch, [FakeResponse(status_code=404)])

        assert fetcher.fetch_organization_repositories('does-not-exist') == []


class TestPartialFetchProtection:
    def test_failed_organization_aborts_the_run(self, fetcher, monkeypatch):
        fetcher.organizations = ['org-a', 'org-b']

        def fail_second(organization):
            if organization == 'org-b':
                raise GitHubAPIError('server error')
            return [{'name': 'repo', 'visibility': 'public'}]

        monkeypatch.setattr(fetcher, 'fetch_organization_repositories', fail_second)

        with pytest.raises(GitHubAPIError, match='org-b'):
            fetcher.fetch_all_repositories()

    def test_run_returns_false_when_fetch_fails(self, fetcher, monkeypatch, tmp_path):
        fetcher.output_file = str(tmp_path / 'repositories.json')
        monkeypatch.setattr(
            fetcher, 'fetch_all_repositories',
            lambda: (_ for _ in ()).throw(GitHubAPIError('nope')),
        )

        assert fetcher.run() is False
        assert not (tmp_path / 'repositories.json').exists()


class TestResultSizeGuard:
    def _write_existing(self, tmp_path, count):
        path = tmp_path / 'repositories.json'
        path.write_text(json.dumps([{'name': f'repo-{i}'} for i in range(count)]))
        return str(path)

    def test_rejects_large_drop_in_repository_count(self, fetcher, tmp_path, monkeypatch):
        monkeypatch.delenv('ALLOW_DATA_SHRINK', raising=False)
        fetcher.output_file = self._write_existing(tmp_path, 100)

        with pytest.raises(GitHubAPIError, match='already published'):
            fetcher.check_result_size([{'name': 'only-one'}])

    def test_allows_small_fluctuations(self, fetcher, tmp_path, monkeypatch):
        monkeypatch.delenv('ALLOW_DATA_SHRINK', raising=False)
        fetcher.output_file = self._write_existing(tmp_path, 100)

        fetcher.check_result_size([{'name': f'repo-{i}'} for i in range(95)])

    def test_override_allows_shrink(self, fetcher, tmp_path, monkeypatch):
        monkeypatch.setenv('ALLOW_DATA_SHRINK', '1')
        fetcher.output_file = self._write_existing(tmp_path, 100)

        fetcher.check_result_size([{'name': 'only-one'}])

    def test_first_run_without_existing_data_is_allowed(self, fetcher, tmp_path, monkeypatch):
        monkeypatch.delenv('ALLOW_DATA_SHRINK', raising=False)
        fetcher.output_file = str(tmp_path / 'missing.json')

        fetcher.check_result_size([{'name': 'only-one'}])


class TestEnhancement:
    def test_quality_score_stays_within_bounds(self, fetcher):
        empty = fetcher.calculate_quality_score({})
        rich = fetcher.calculate_quality_score({
            'stargazers_count': 500,
            'pushed_at': '2026-11-01T00:00:00Z',
            'has_readme': True,
            'description': 'x' * 200,
            'language': 'Python',
            'topics': ['nhs'],
            'size': 50000,
            'license': {'key': 'mit'},
        })

        assert empty >= 30
        assert rich <= 100

    def test_enhancement_adds_expected_fields(self, fetcher, sample_repo):
        enhanced = fetcher.enhance_repository_data(dict(sample_repo))

        assert enhanced['visibility'] == 'Public'
        assert isinstance(enhanced['quality_score'], int)
        assert 'nhs-wales' in enhanced['generated_tags']
        assert set(enhanced['topics']).issubset(set(enhanced['all_tags']))

    def test_private_repository_marked_internal(self, fetcher, sample_repo):
        sample_repo['private'] = True

        assert fetcher.enhance_repository_data(sample_repo)['visibility'] == 'Internal'
