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

    def test_group_by_minor_version(self):
        """Test grouping nodes by minor version (summary mode)."""
        nodes = [
            NodeInfo("node-1", "v1.28.1", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.5", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.27.3", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes, detailed=False)
        self.assertEqual(len(groups), 2)  # v1.28 and v1.27
        
        # Find the v1.28 group
        v128_group = next(g for g in groups if g.kubelet_version == "v1.28")
        self.assertEqual(v128_group.count, 2)  # node-1 and node-2

    def test_group_by_os_summary(self):
        """Test grouping OS versions together in summary mode."""
        nodes = [
            NodeInfo("node-1", "v1.29.0", "Bottlerocket OS 1.20.4 (aws-k8s-1.29)", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.30.0", "Bottlerocket OS 1.21.2 (aws-k8s-1.30)", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.31.0", "Bottlerocket OS 1.23.0 (aws-k8s-1.31)", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes, detailed=False)
        # All should group together: same OS (Bottlerocket OS), same k8s minor (different), same runtime
        # Actually they have different k8s versions so will be 3 groups
        # But all should have "Bottlerocket OS" as os_image
        for group in groups:
            if "Bottlerocket" in group.os_image:
                self.assertEqual(group.os_image, "Bottlerocket OS")

    def test_windows_year_preserved(self):
        """Test that Windows year versions are preserved in summary mode."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Windows Server 2019 Datacenter", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Windows Server 2022 Datacenter", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.28.0", "Windows Server 2022 Datacenter 10.0.20348", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes, detailed=False)
        # Should have 2 groups: 2019 and 2022 (node-2 and node-3 grouped)
        self.assertEqual(len(groups), 2)
        
        # Check that years are preserved
        os_images = {g.os_image for g in groups}
        self.assertIn("Windows Server 2019 Datacenter", os_images)
        self.assertIn("Windows Server 2022 Datacenter", os_images)

    def test_container_runtime_minor_grouping(self):
        """Test that container runtime versions group by major.minor in summary mode."""
        nodes = [
            NodeInfo("node-1", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.0", "Ubuntu 22.04", "containerd://1.7.5"),
            NodeInfo("node-3", "v1.28.0", "Ubuntu 22.04", "containerd://1.6.8"),
        ]
        groups = group_nodes(nodes, detailed=False)
        # Should have 2 groups: containerd 1.7 (node-1 and node-2) and 1.6 (node-3)
        self.assertEqual(len(groups), 2)
        
        # Check runtime versions
        runtimes = {g.container_runtime for g in groups}
        self.assertIn("containerd://1.7", runtimes)
        self.assertIn("containerd://1.6", runtimes)

    def test_group_by_patch_version(self):
        """Test grouping nodes by patch version (detailed mode)."""
        nodes = [
            NodeInfo("node-1", "v1.28.1", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-2", "v1.28.5", "Ubuntu 22.04", "containerd://1.7.0"),
            NodeInfo("node-3", "v1.28.1", "Ubuntu 22.04", "containerd://1.7.0"),
        ]
        groups = group_nodes(nodes, detailed=True)
        self.assertEqual(len(groups), 2)  # v1.28.1 and v1.28.5
        
        # Find the v1.28.1 group
        v1281_group = next(g for g in groups if g.kubelet_version == "v1.28.1")
        self.assertEqual(v1281_group.count, 2)  # node-1 and node-3


if __name__ == "__main__":
    unittest.main()
