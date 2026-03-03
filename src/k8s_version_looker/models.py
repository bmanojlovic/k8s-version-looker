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


def group_nodes(nodes: List[NodeInfo], detailed: bool = True) -> List[NodeGroup]:
    """Group nodes by kubelet version, OS, and container runtime.
    
    Args:
        nodes: List of node information
        detailed: If False, group by minor version only (e.g., v1.28.1 -> v1.28)
                  and strip OS version numbers (e.g., Bottlerocket 1.51 -> Bottlerocket)
    """
    groups: Dict[tuple, List[str]] = {}

    for node in nodes:
        version = node.kubelet_version
        os_image = node.os_image
        container_runtime = node.container_runtime
        
        if not detailed:
            # Strip patch version: v1.28.5 -> v1.28
            parts = version.split('.')
            if len(parts) >= 2:
                version = f"{parts[0]}.{parts[1]}"
            
            # Strip OS version numbers and details, but preserve Windows year versions
            # "Bottlerocket OS 1.20.4 (aws-k8s-1.29)" -> "Bottlerocket OS"
            # "Ubuntu 22.04.3 LTS" -> "Ubuntu"
            # "Windows Server 2022" -> "Windows Server 2022" (preserve year)
            import re
            if "Windows" in os_image:
                # For Windows, keep the year version (e.g., 2019, 2022)
                # Strip only build numbers: "Windows Server 2022 Datacenter 10.0.20348" -> "Windows Server 2022 Datacenter"
                os_image = re.sub(r'\s+\d+\.\d+\.\d+.*$', '', os_image).strip()
            else:
                # For other OS, strip everything from first version number
                os_image = re.split(r'\s+\d+', os_image)[0].strip()
            
            # Strip container runtime patch version: containerd://1.7.5 -> containerd://1.7
            if '://' in container_runtime:
                runtime_parts = container_runtime.split('://')
                if len(runtime_parts) == 2:
                    runtime_name, runtime_version = runtime_parts
                    version_parts = runtime_version.split('.')
                    if len(version_parts) >= 2:
                        container_runtime = f"{runtime_name}://{version_parts[0]}.{version_parts[1]}"
        
        key = (version, os_image, container_runtime)
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
