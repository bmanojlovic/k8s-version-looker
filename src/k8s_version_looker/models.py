"""Data models for Kubernetes cluster information."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class NodeInfo:
    """Information about a single Kubernetes node."""
    name: str
    kubelet_version: str
    os_image: str
    container_runtime: str


@dataclass
class ClusterInfo:
    """Information about a Kubernetes cluster."""
    context_name: str
    major: str
    minor: str
    git_version: str
    nodes: List[NodeInfo]

    @property
    def node_count(self) -> int:
        """Total number of nodes in the cluster."""
        return len(self.nodes)


@dataclass
class NodeGroup:
    """Group of nodes with identical version and runtime characteristics."""
    kubelet_version: str
    os_image: str
    container_runtime: str
    node_names: List[str]

    @property
    def count(self) -> int:
        """Number of nodes in this group."""
        return len(self.node_names)


def group_nodes(nodes: List[NodeInfo]) -> List[NodeGroup]:
    """Group nodes by kubelet version, OS, and container runtime."""
    groups: Dict[tuple, List[str]] = {}

    for node in nodes:
        key = (node.kubelet_version, node.os_image, node.container_runtime)
        if key not in groups:
            groups[key] = []
        groups[key].append(node.name)

    return [
        NodeGroup(
            kubelet_version=kubelet_version,
            os_image=os_image,
            container_runtime=container_runtime,
            node_names=node_names
        )
        for (kubelet_version, os_image, container_runtime), node_names in groups.items()
    ]
