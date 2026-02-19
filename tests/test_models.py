"""Tests for data models."""

import unittest
from src.k8s_version_looker.models import NodeInfo, ClusterInfo, NodeGroup, group_nodes


class TestNodeInfo(unittest.TestCase):
    """Test NodeInfo dataclass."""

    def test_create_node_info(self):
        """Test creating a NodeInfo instance."""
        node = NodeInfo(
            name="node-1",
            kubelet_version="v1.28.0",
            os_image="Ubuntu 22.04",
            container_runtime="containerd://1.7.0"
        )
        self.assertEqual(node.name, "node-1")
        self.assertEqual(node.kubelet_version, "v1.28.0")


class TestClusterInfo(unittest.TestCase):
    """Test ClusterInfo dataclass."""

    def test_create_cluster_info(self):
        """Test creating a ClusterInfo instance."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        cluster = ClusterInfo(
            context_name="test-cluster",
            major="1",
            minor="28",
            git_version="v1.28.0",
            nodes=nodes
        )
        self.assertEqual(cluster.context_name, "test-cluster")
        self.assertEqual(cluster.node_count, 2)

    def test_empty_cluster(self):
        """Test cluster with no nodes."""
        cluster = ClusterInfo(
            context_name="empty-cluster",
            major="1",
            minor="28",
            git_version="v1.28.0",
            nodes=[]
        )
        self.assertEqual(cluster.node_count, 0)


class TestNodeGroup(unittest.TestCase):
    """Test NodeGroup dataclass."""

    def test_node_group_count(self):
        """Test NodeGroup count property."""
        group = NodeGroup(
            kubelet_version="v1.28.0",
            os_image="Ubuntu 22.04",
            container_runtime="containerd://1.7.0",
            node_names=["node-1", "node-2", "node-3"]
        )
        self.assertEqual(group.count, 3)


class TestGroupNodes(unittest.TestCase):
    """Test group_nodes function."""

    def test_group_identical_nodes(self):
        """Test grouping identical nodes."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].count, 3)

    def test_group_different_versions(self):
        """Test grouping nodes with different versions."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.1", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes)
        self.assertEqual(len(groups), 2)

    def test_group_different_os(self):
        """Test grouping nodes with different OS."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Debian 11", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes)
        self.assertEqual(len(groups), 2)

    def test_empty_nodes(self):
        """Test grouping empty node list."""
        groups = group_nodes([])
        self.assertEqual(len(groups), 0)


if __name__ == "__main__":
    unittest.main()
