#!/usr/bin/env python
"""
ensure-registry command handler

Creates or updates a GitHub Flow Registry Client in NiFi.
Uses nipyapi's built-in utilities and versioning functions.
"""

import nipyapi
from nipyapi.utils import getenv


def run_ensure_registry(set_output):
    """
    Ensure a GitHub Flow Registry Client exists with the desired configuration.

    Args:
        set_output: Function to set output values
    """
    # Get inputs using nipyapi's getenv
    client_name = getenv('NIFI_REGISTRY_CLIENT_NAME') or 'GitHub-FlowRegistry'
    github_token = getenv('GH_REGISTRY_TOKEN')
    github_api_url = getenv('NIFI_REGISTRY_API_URL') or 'https://api.github.com/'
    default_branch = getenv('NIFI_REGISTRY_BRANCH') or 'main'
    repository_path = getenv('NIFI_REPOSITORY_PATH') or ''

    if not github_token:
        raise ValueError("github-registry-token is required for ensure-registry command")

    # Get repository (action.yml provides default from github.repository context)
    github_repo = getenv('NIFI_REGISTRY_REPO') or ''

    if not github_repo or '/' not in github_repo:
        raise ValueError(
            "Could not determine repository. "
            "Please provide github-registry-repo in owner/repo format, "
            "or ensure GITHUB_REPOSITORY context is available."
        )

    # Split into owner and name for the registry client properties
    repo_owner, repo_name = github_repo.split('/', 1)

    print(f"Ensuring registry client '{client_name}' for {repo_owner}/{repo_name}")

    # Build properties
    # IGNORE_CHANGES: imports new parameter defaults but ignores changed values
    # This is safer for CI/CD as it won't overwrite environment-specific values
    properties = {
        'GitHub API URL': github_api_url,
        'Repository Owner': repo_owner,
        'Repository Name': repo_name,
        'Authentication Type': 'PERSONAL_ACCESS_TOKEN',
        'Personal Access Token': github_token,
        'Default Branch': default_branch,
        'Parameter Context Values': 'IGNORE_CHANGES',
    }

    # Add Repository Path if specified (empty string means repo root)
    if repository_path:
        properties['Repository Path'] = repository_path

    # Use nipyapi's ensure_registry_client function
    client = nipyapi.versioning.ensure_registry_client(
        name=client_name,
        reg_type='org.apache.nifi.github.GitHubFlowRegistryClient',
        description=f'GitHub Registry Client for {repo_owner}/{repo_name}',
        properties=properties
    )

    print(f"Registry client ready: {client.component.name} (ID: {client.id})")

    # Set outputs
    set_output('registry_client_id', client.id)
    set_output('registry_client_name', client.component.name)
