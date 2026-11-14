"""Shared pytest fixtures for the Solutions Exchange data pipeline tests."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'scripts'))


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code=200, json_data=None, headers=None, text=''):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else []
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._json_data


@pytest.fixture
def fetcher(monkeypatch):
    """A fetcher with a dummy token and sleeping disabled."""
    from update_repositories import NHSWalesRepositoryFetcher

    instance = NHSWalesRepositoryFetcher(github_token='test-token')
    monkeypatch.setattr(instance, '_sleep', lambda seconds: None)
    return instance


@pytest.fixture
def sample_repo():
    """A representative enhanced repository record."""
    return {
        'id': 1,
        'name': 'patient-flow-dashboard',
        'full_name': 'GIGCymru/patient-flow-dashboard',
        'html_url': 'https://github.com/GIGCymru/patient-flow-dashboard',
        'owner': {'login': 'GIGCymru'},
        'description': 'A clinical dashboard for monitoring patient flow across sites.',
        'language': 'Python',
        'topics': ['nhs'],
        'visibility': 'public',
        'private': False,
        'stargazers_count': 2,
        'size': 1500,
        'pushed_at': '2026-11-01T00:00:00Z',
        'updated_at': '2026-11-01T00:00:00Z',
        'license': {'key': 'mit'},
        'generated_tags': ['nhs-wales'],
        'all_tags': ['nhs', 'nhs-wales'],
        'quality_score': 85,
        'featured': True,
    }
