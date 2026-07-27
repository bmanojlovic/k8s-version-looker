"""Kubernetes cluster client for querying version information."""

import fnmatch
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Callable

import urllib3
from kubernetes import client, config

from .models import ClusterInfo, NodeInfo

# Suppress noisy urllib3 connection pool logging (e.g. "remaining: 0")
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
urllib3.disable_warnings()

# Lock for kubeconfig loading (not thread-safe in the kubernetes client)
_config_lock = threading.Lock()


def should_include_context(context_name: str, include_patterns: Optional[List[str]] = None,
                           exclude_patterns: Optional[List[str]] = None) -> bool:
    """
    Check if a context should be included based on include/exclude patterns.

    Args:
        context_name: Name of the context to check
        include_patterns: List of glob patterns to include (if None, include all)
        exclude_patterns: List of glob patterns to exclude

    Returns:
        True if context should be included, False otherwise
    """
    # If include patterns specified, context must match at least one
    if include_patterns:
        if not any(fnmatch.fnmatch(context_name, pattern) for pattern in include_patterns):
            return False

    # If exclude patterns specified, context must not match any
    if exclude_patterns:
        if any(fnmatch.fnmatch(context_name, pattern) for pattern in exclude_patterns):
            return False

    return True


def _query_single_cluster(context_name: str, skip_tls_verify: bool, timeout: int = 5) -> Tuple[str, Optional[ClusterInfo], Optional[str]]:
    """
    Query a single cluster for version information.

    Args:
        context_name: Name of the context to query
        skip_tls_verify: If True, skip TLS certificate verification
        timeout: Connection and read timeout in seconds (default: 5)

    Returns:
        Tuple of (context_name, ClusterInfo or None if error, error message or None)
    """
    try:
        # Create a thread-safe client - lock during config parsing and pool setup
        with _config_lock:
            api_client = config.new_client_from_config(context=context_name)
            # Set pool-level timeout and limit retries (must be done before any requests)
            api_client.rest_client.pool_manager.connection_pool_kw['timeout'] = \
                urllib3.util.Timeout(connect=timeout, read=timeout)
            # total=1 allows SSL handshake, connect=0 prevents TCP connect retries on dead hosts
            api_client.rest_client.pool_manager.connection_pool_kw['retries'] = \
                urllib3.util.Retry(total=1, connect=0)

        # Configure TLS
        if skip_tls_verify:
            api_client.configuration.verify_ssl = False

        with api_client:
            version_api = client.VersionApi(api_client)
            core_api = client.CoreV1Api(api_client)

            # Get cluster version (with per-request timeout: connect, read)
            version_info = version_api.get_code(_request_timeout=(timeout, timeout))

            # Get node information
            nodes_list = core_api.list_node(_request_timeout=(timeout, timeout))
            node_infos = []

            for node in nodes_list.items:
                node_infos.append(NodeInfo(
                    name=node.metadata.name,
                    kubelet_version=node.status.node_info.kubelet_version,
                    os_image=node.status.node_info.os_image,
                    container_runtime=node.status.node_info.container_runtime_version
                ))

            cluster_info = ClusterInfo(
                context_name=context_name,
                major=version_info.major,
                minor=version_info.minor,
                git_version=version_info.git_version,
                nodes=node_infos
            )
            return (context_name, cluster_info, None)

    except Exception as e:
        # Extract a clean, short error message
        error_msg = str(e)
        if "Max retries exceeded" in error_msg:
            # Extract host:port and root cause type
            import re
            host_match = re.search(r"host='([^']+)'.*?port=(\d+)", error_msg)
            cause_match = re.search(r"Caused by (\w+)", error_msg)
            if host_match and cause_match:
                host, port = host_match.groups()
                cause = cause_match.group(1)
                error_msg = f"{host}:{port} - {cause}"
            elif host_match:
                host, port = host_match.groups()
                error_msg = f"{host}:{port} - connection failed"
            else:
                error_msg = "connection failed"
        else:
            # Generic: first line, trimmed
            error_msg = error_msg.split('\n')[0].strip()
            if len(error_msg) > 80:
                error_msg = error_msg[:77] + "..."
        return (context_name, None, error_msg)


def get_cluster_versions(specific_context: Optional[str] = None,
                        skip_tls_verify: bool = False,
                        include_patterns: Optional[List[str]] = None,
                        exclude_patterns: Optional[List[str]] = None,
                        max_workers: int = 10,
                        timeout: int = 5,
                        progress_callback: Optional[Callable[[int, int, str], None]] = None,
                        error_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, ClusterInfo]:
    """
    Query Kubernetes clusters for version information in parallel.

    Args:
        specific_context: If provided, only query this specific context
        skip_tls_verify: If True, skip TLS certificate verification
        include_patterns: List of glob patterns for contexts to include
        exclude_patterns: List of glob patterns for contexts to exclude
        max_workers: Maximum number of parallel queries (default: 5)
        timeout: Connection and read timeout in seconds (default: 5)
        progress_callback: Optional callback(completed, total, context_name) for progress updates
        error_callback: Optional callback(context_name, error_message) for error display

    Returns:
        Dictionary mapping context names to ClusterInfo objects
    """
    versions: Dict[str, ClusterInfo] = {}

    try:
        # Get all available contexts
        contexts, _ = config.list_kube_config_contexts()
    except Exception as e:
        print(f"Error getting contexts: {e}")
        return versions

    # If a specific context is provided, filter the contexts list
    if specific_context:
        context_names = [c["name"] for c in contexts]
        if specific_context not in context_names:
            print(f"Error: Context '{specific_context}' not found in kubeconfig")
            return versions
        contexts = [c for c in contexts if c["name"] == specific_context]
    else:
        # Apply include/exclude filtering
        contexts = [
            c for c in contexts
            if should_include_context(c["name"], include_patterns, exclude_patterns)
        ]

    total_contexts = len(contexts)

    # Query clusters in parallel
    executor = ThreadPoolExecutor(max_workers=max_workers)
    interrupted = False

    try:
        # Submit all queries
        future_to_context = {
            executor.submit(_query_single_cluster, c["name"], skip_tls_verify, timeout): c["name"]
            for c in contexts
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_context):
            context_name = future_to_context[future]
            try:
                _, cluster_info, error_msg = future.result()
                if cluster_info is not None:
                    versions[context_name] = cluster_info
                elif error_msg and error_callback:
                    error_callback(context_name, error_msg)
            except Exception:
                pass

            completed += 1
            if progress_callback:
                progress_callback(completed, total_contexts, context_name)

    except KeyboardInterrupt:
        interrupted = True

        # Cancel all pending futures
        for future in future_to_context:
            future.cancel()

        # Print newline for clean output
        sys.stderr.write("\n\n⚠️  Interrupted by user. Returning partial results...\n")
        sys.stderr.flush()

    except Exception as e:
        # Handle any other exceptions (like timeout from as_completed)
        interrupted = True
        for future in future_to_context:
            future.cancel()
        sys.stderr.write(f"\n\n⚠️  Error: {e}. Returning partial results...\n")
        sys.stderr.flush()

    finally:
        # Shutdown - don't wait if interrupted
        executor.shutdown(wait=not interrupted, cancel_futures=interrupted)

    return versions
