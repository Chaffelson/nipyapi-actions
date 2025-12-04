#!/usr/bin/env python
"""
Shared utilities for NiFi Flow CI/CD Action.

This module contains helper functions used across multiple command handlers.
"""

import os
import re

import requests
from nipyapi.utils import getenv


def set_output(name, value):
    """
    Set an output for GitHub Actions.

    In GitHub Actions, writes to GITHUB_OUTPUT file.
    For local testing, prints to stdout.

    Args:
        name: Output variable name
        value: Output value
    """
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"{name}={value}\n")
    else:
        # For local testing, just print
        print(f"OUTPUT: {name}={value}")


def resolve_version_ref(version, repo=None, token=None):
    """
    Resolve a version ref (tag/branch/SHA) to a commit SHA.

    If the version already looks like a SHA (7-40 hex characters), returns it as-is.
    Otherwise, calls the GitHub API to resolve the ref to a SHA.

    Args:
        version: Tag name, branch name, or commit SHA. If None or empty, returns None.
        repo: Repository in owner/repo format. Defaults to NIFI_REGISTRY_REPO env var.
        token: GitHub token for API access. Defaults to GH_REGISTRY_TOKEN env var.

    Returns:
        Resolved commit SHA, or None if version was empty.

    Raises:
        ValueError: If the ref cannot be resolved.
    """
    if not version:
        return None  # Caller wants latest version

    # Already a SHA (7-40 hex characters) - return as-is
    if re.match(r'^[0-9a-fA-F]{7,40}$', version):
        return version

    # Resolve via GitHub API
    repo = repo or getenv('NIFI_REGISTRY_REPO')
    token = token or getenv('GH_REGISTRY_TOKEN')

    if not repo:
        raise ValueError("Cannot resolve version ref: repository not specified")
    if not token:
        raise ValueError("Cannot resolve version ref: GitHub token not available")

    url = f'https://api.github.com/repos/{repo}/commits/{version}'
    headers = {'Authorization': f'Bearer {token}'}

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 404:
        raise ValueError(f"Could not resolve version ref '{version}' - not found in {repo}")
    resp.raise_for_status()

    sha = resp.json()['sha']
    print(f"Resolved version '{version}' to SHA: {sha[:12]}...")
    return sha


def modify_processor(process_group_id):
    """Rename first processor in a process group to trigger LOCALLY_MODIFIED state."""
    import nipyapi

    proc = nipyapi.canvas.list_all_processors(process_group_id)[0]
    new_name = proc.component.name + '_MODIFIED'

    update_body = nipyapi.nifi.ProcessorEntity(
        id=proc.id,
        revision=proc.revision,
        component=nipyapi.nifi.ProcessorDTO(id=proc.component.id, name=new_name)
    )
    # Note: API signature is update_processor(body, id) - body comes first!
    nipyapi.nifi.ProcessorsApi().update_processor(body=update_body, id=proc.id)
    print(f"Renamed processor to '{new_name}'")
