"""Output formatters for cluster version information."""

import datetime
import json
from dataclasses import asdict
from typing import Dict, Optional

from .models import ClusterInfo, group_nodes


def generate_markdown(versions: Dict[str, ClusterInfo], output_file: Optional[str] = None) -> str:
    """Generate a Markdown report of cluster versions."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_content = f"# Kubernetes Cluster Versions Report\n\n"
    md_content += f"*Generated on: {now}*\n\n"

    if not versions:
        md_content += "**No cluster information available.**\n"
        if output_file:
            with open(output_file, 'w') as f:
                f.write(md_content)
        return md_content

    for cluster_info in versions.values():
        md_content += f"## Context: {cluster_info.context_name}\n\n"
        md_content += f"**Kubernetes Version:** {cluster_info.git_version} (Major: {cluster_info.major}, Minor: {cluster_info.minor})\n\n"

        if not cluster_info.nodes:
            md_content += "No node information available.\n\n"
            continue

        node_groups = group_nodes(cluster_info.nodes)

        md_content += f"### Node Information ({cluster_info.node_count} nodes)\n\n"
        md_content += "| Kubelet Version | Node Count | OS | Container Runtime |\n"
        md_content += "|----------------|------------|----|-----------------|\n"

        for group in node_groups:
            md_content += f"| {group.kubelet_version} | {group.count} | {group.os_image} | {group.container_runtime} |\n"

        md_content += "\n"

    if output_file:
        with open(output_file, 'w') as f:
            f.write(md_content)

    return md_content


def generate_html(versions: Dict[str, ClusterInfo], output_file: Optional[str] = None) -> str:
    """Generate an HTML report of cluster versions."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes Cluster Versions Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #0066cc;
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #333;
            margin-top: 20px;
        }}
        .timestamp {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .cluster-info {{
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .version-info {{
            font-weight: bold;
            color: #0066cc;
        }}
    </style>
</head>
<body>
    <h1>Kubernetes Cluster Versions Report</h1>
    <div class="timestamp">Generated on: {now}</div>
"""

    if not versions:
        html_content += "<p><strong>No cluster information available.</strong></p>"
        html_content += "</body></html>"
        if output_file:
            with open(output_file, 'w') as f:
                f.write(html_content)
        return html_content

    for cluster_info in versions.values():
        html_content += f'<div class="cluster-info">'
        html_content += f'<h2>Context: {cluster_info.context_name}</h2>'
        html_content += f'<p class="version-info">Kubernetes Version: {cluster_info.git_version} (Major: {cluster_info.major}, Minor: {cluster_info.minor})</p>'

        if not cluster_info.nodes:
            html_content += "<p>No node information available.</p>"
            html_content += "</div>"
            continue

        node_groups = group_nodes(cluster_info.nodes)

        html_content += f'<h3>Node Information ({cluster_info.node_count} nodes)</h3>'
        html_content += """
        <table>
            <tr>
                <th>Kubelet Version</th>
                <th>Node Count</th>
                <th>OS</th>
                <th>Container Runtime</th>
            </tr>
        """

        for group in node_groups:
            html_content += f"""
            <tr>
                <td>{group.kubelet_version}</td>
                <td>{group.count}</td>
                <td>{group.os_image}</td>
                <td>{group.container_runtime}</td>
            </tr>
            """

        html_content += "</table></div>"

    html_content += "</body></html>"

    if output_file:
        with open(output_file, 'w') as f:
            f.write(html_content)

    return html_content


def generate_json(versions: Dict[str, ClusterInfo], output_file: Optional[str] = None) -> str:
    """Generate a JSON report of cluster versions."""
    # Convert dataclasses to dictionaries
    clusters_dict = {
        context_name: asdict(cluster_info)
        for context_name, cluster_info in versions.items()
    }

    # Add timestamp to the output
    output = {
        "generated_at": datetime.datetime.now().isoformat(),
        "clusters": clusters_dict
    }

    json_content = json.dumps(output, indent=2)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(json_content)

    return json_content


def display_text(versions: Dict[str, ClusterInfo]) -> None:
    """Display cluster versions in text format to console."""
    if not versions:
        print("No cluster information available.")
        return

    for cluster_info in versions.values():
        print(f"\n{'=' * 50}")
        print(f"Context: {cluster_info.context_name}")
        print(f"Kubernetes Version: {cluster_info.git_version} (Major: {cluster_info.major}, Minor: {cluster_info.minor})")

        if not cluster_info.nodes:
            print("No node information available.")
            continue

        node_groups = group_nodes(cluster_info.nodes)

        print(f"\nNode Information ({cluster_info.node_count} nodes):")
        for group in node_groups:
            print(f"  - Kubelet Version: {group.kubelet_version}")
            print(f"    Node Count: {group.count}")
            print(f"    OS: {group.os_image}")
            print(f"    Container Runtime: {group.container_runtime}")
