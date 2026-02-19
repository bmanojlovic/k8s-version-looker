"""Tests for Kubernetes client functionality."""

import unittest
from src.k8s_version_looker.client import should_include_context


class TestContextFiltering(unittest.TestCase):
    """Test context filtering logic."""

    def test_no_patterns(self):
        """Test with no include/exclude patterns - should include everything."""
        self.assertTrue(should_include_context("prod-cluster"))
        self.assertTrue(should_include_context("dev-cluster"))
        self.assertTrue(should_include_context("test-cluster"))

    def test_include_pattern_match(self):
        """Test include pattern matching."""
        include_patterns = ["prod-*"]
        self.assertTrue(should_include_context("prod-us-east", include_patterns=include_patterns))
        self.assertTrue(should_include_context("prod-eu-west", include_patterns=include_patterns))
        self.assertFalse(should_include_context("dev-cluster", include_patterns=include_patterns))

    def test_include_multiple_patterns(self):
        """Test multiple include patterns."""
        include_patterns = ["prod-*", "staging-*"]
        self.assertTrue(should_include_context("prod-cluster", include_patterns=include_patterns))
        self.assertTrue(should_include_context("staging-cluster", include_patterns=include_patterns))
        self.assertFalse(should_include_context("dev-cluster", include_patterns=include_patterns))

    def test_exclude_pattern_match(self):
        """Test exclude pattern matching."""
        exclude_patterns = ["dev-*", "test-*"]
        self.assertTrue(should_include_context("prod-cluster", exclude_patterns=exclude_patterns))
        self.assertFalse(should_include_context("dev-cluster", exclude_patterns=exclude_patterns))
        self.assertFalse(should_include_context("test-cluster", exclude_patterns=exclude_patterns))

    def test_include_and_exclude(self):
        """Test combined include and exclude patterns."""
        include_patterns = ["prod-*"]
        exclude_patterns = ["*-backup"]
        self.assertTrue(should_include_context("prod-main", include_patterns, exclude_patterns))
        self.assertFalse(should_include_context("prod-backup", include_patterns, exclude_patterns))
        self.assertFalse(should_include_context("dev-main", include_patterns, exclude_patterns))

    def test_exact_match(self):
        """Test exact context name matching."""
        include_patterns = ["production"]
        self.assertTrue(should_include_context("production", include_patterns=include_patterns))
        self.assertFalse(should_include_context("production-new", include_patterns=include_patterns))

    def test_wildcard_patterns(self):
        """Test various wildcard patterns."""
        # Match anything starting with 'k8s'
        self.assertTrue(should_include_context("k8s-prod", include_patterns=["k8s-*"]))

        # Match anything ending with 'prod'
        self.assertTrue(should_include_context("cluster-prod", include_patterns=["*-prod"]))

        # Match anything containing 'staging'
        self.assertTrue(should_include_context("my-staging-cluster", include_patterns=["*staging*"]))


if __name__ == "__main__":
    unittest.main()
