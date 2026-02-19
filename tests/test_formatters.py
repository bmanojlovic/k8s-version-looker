"""Tests for output formatters."""

import unittest
import json
from src.k8s_version_looker.models import NodeInfo, ClusterInfo
from src.k8s_version_looker.formatters import generate_markdown, generate_html, generate_json


class TestFormatters(unittest.TestCase):
    """Test output formatter functions."""

    def setUp(self):
        """Set up test data."""
        self.nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        self.cluster = ClusterInfo(
            context_name="test-cluster",
            major="1",
            minor="28",
            git_version="v1.28.0",
            nodes=self.nodes
        )
        self.versions = {"test-cluster": self.cluster}

    def test_generate_markdown(self):
        """Test Markdown generation."""
        md_output = generate_markdown(self.versions)
        self.assertIn("# Kubernetes Cluster Versions Report", md_output)
        self.assertIn("## Context: test-cluster", md_output)
        self.assertIn("v1.28.0", md_output)
        self.assertIn("Ubuntu 22.04", md_output)
        self.assertIn("2 nodes", md_output)

    def test_generate_markdown_empty(self):
        """Test Markdown generation with no clusters."""
        md_output = generate_markdown({})
        self.assertIn("No cluster information available", md_output)

    def test_generate_html(self):
        """Test HTML generation."""
        html_output = generate_html(self.versions)
        self.assertIn("<!DOCTYPE html>", html_output)
        self.assertIn("<h2>Context: test-cluster</h2>", html_output)
        self.assertIn("v1.28.0", html_output)
        self.assertIn("Ubuntu 22.04", html_output)

    def test_generate_html_empty(self):
        """Test HTML generation with no clusters."""
        html_output = generate_html({})
        self.assertIn("No cluster information available", html_output)
        self.assertIn("</html>", html_output)

    def test_generate_json(self):
        """Test JSON generation."""
        json_output = generate_json(self.versions)
        data = json.loads(json_output)

        self.assertIn("generated_at", data)
        self.assertIn("clusters", data)
        self.assertIn("test-cluster", data["clusters"])

        cluster_data = data["clusters"]["test-cluster"]
        self.assertEqual(cluster_data["context_name"], "test-cluster")
        self.assertEqual(cluster_data["git_version"], "v1.28.0")
        self.assertEqual(len(cluster_data["nodes"]), 2)

    def test_generate_json_empty(self):
        """Test JSON generation with no clusters."""
        json_output = generate_json({})
        data = json.loads(json_output)

        self.assertIn("generated_at", data)
        self.assertEqual(data["clusters"], {})

    def test_multiple_clusters(self):
        """Test formatters with multiple clusters."""
        cluster2 = ClusterInfo(
            context_name="prod-cluster",
            major="1",
            minor="29",
            git_version="v1.29.0",
            nodes=[]
        )
        versions = {
            "test-cluster": self.cluster,
            "prod-cluster": cluster2
        }

        md_output = generate_markdown(versions)
        self.assertIn("test-cluster", md_output)
        self.assertIn("prod-cluster", md_output)

        html_output = generate_html(versions)
        self.assertIn("test-cluster", html_output)
        self.assertIn("prod-cluster", html_output)

        json_output = generate_json(versions)
        data = json.loads(json_output)
        self.assertEqual(len(data["clusters"]), 2)


if __name__ == "__main__":
    unittest.main()
