"""Shared pytest fixtures and configuration for Pipework tests.

This module provides fixtures that are available to all test modules
without needing to import them explicitly.
"""

import pytest

# Add any shared fixtures here that should be available to all tests
# For now, test-specific fixtures are in test_engine.py


def pytest_configure(config: pytest.Config) -> None:
	"""Configure pytest with custom markers and settings.

	Args:
		config: pytest configuration object
	"""
	config.addinivalue_line(
		"markers",
		"integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
	)
	config.addinivalue_line(
		"markers",
		"slow: marks tests as slow (deselect with '-m \"not slow\"')",
	)
