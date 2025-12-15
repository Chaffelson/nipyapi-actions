# NiPyAPI Actions Makefile
# Commands for development, testing, and local act/gitlab-ci-local simulation

SHELL := /bin/bash

# ============================================================================
# UV Configuration
# ============================================================================
# All Python commands use `uv run` which:
# - Automatically creates/uses .venv
# - Ensures dependencies are installed
# - Works without manual venv activation
#
# Convention for AI agents and scripts:
#   Use `uv run python ...` instead of `python ...`
#   Use `uv run pytest ...` instead of `pytest ...`
# ============================================================================

UV := uv
UV_RUN := $(UV) run

# ============================================================================
# Environment configuration
# ============================================================================

# Load local .env if it exists (for GH_REGISTRY_TOKEN, NIFI credentials, etc.)
# Create .env from .env.example for local development
ifneq (,$(wildcard .env))
    include .env
    export
endif

# NiFi endpoint for connectivity checks
NIFI_API_ENDPOINT ?= https://localhost:9447/nifi-api

# ============================================================================
# Infrastructure configuration
# ============================================================================

# Path to nipyapi repository (only needed for running NiFi infrastructure locally)
# Most users will have NiFi running elsewhere and won't need this
NIPYAPI_INFRA ?= ../nipyapi

# ============================================================================
# Act settings (for local GitHub Actions simulation)
# ============================================================================

ACT_ARCH := linux/amd64
ACT_IMAGE ?= catthehacker/ubuntu:act-latest

# ============================================================================
# Targets
# ============================================================================

.PHONY: help sync test test-single lint clean \
        infra-up infra-down infra-ready check-env check-act check-infra generate-secrets \
        test-act test-act-verbose gitlab-test

help:
	@echo "NiPyAPI Actions Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make sync              - Install dependencies (uv sync)"
	@echo ""
	@echo "Testing (Python - direct):"
	@echo "  make test              - Run full workflow test"
	@echo "  make test-single CMD=X - Test single command"
	@echo ""
	@echo "Testing (CI simulation):"
	@echo "  make test-act          - Run GitHub Actions with act"
	@echo "  make test-act-verbose  - Run with debug output"
	@echo "  make gitlab-test       - Run GitLab CI setup test (no NiFi needed)"
	@echo "  make gitlab-test-all   - Run full GitLab CI pipeline (NiFi required)"
	@echo "  make gitlab-test-gl    - Run with GitLab registry (nipyapi/nipyapi-actions)"
	@echo ""
	@echo "Infrastructure (uses nipyapi repo):"
	@echo "  make infra-up          - Start NiFi (github-cicd profile)"
	@echo "  make infra-down        - Stop NiFi"
	@echo "  make infra-ready       - Wait for NiFi to be ready"
	@echo ""
	@echo "Utilities:"
	@echo "  make generate-secrets  - Generate .secrets from nipyapi config"
	@echo "  make lint              - Check Python code style"
	@echo "  make clean             - Remove cache and temp files"
	@echo ""
	@echo "Configuration:"
	@echo "  NIPYAPI_INFRA          - Path to nipyapi repo (default: ../nipyapi)"
	@echo "  GH_REGISTRY_TOKEN      - GitHub token (set in .env)"
	@echo "  GL_REGISTRY_TOKEN      - GitLab token (set in .env)"
	@echo "  NIFI_REGISTRY_PROVIDER - 'github' or 'gitlab' (auto-detected from tokens)"
	@echo ""
	@echo "Note: All Python commands use 'uv run' - no venv activation needed."
	@echo ""

# ============================================================================
# Setup
# ============================================================================

sync:
	@echo "Installing dependencies with UV..."
	@$(UV) sync
	@echo "Dependencies installed"

# ============================================================================
# Python-based testing (direct execution via UV)
# ============================================================================

test: check-env check-infra
	@echo "Running full workflow test..."
	PYTHONPATH=$(CURDIR):$(CURDIR)/src:$$PYTHONPATH $(UV_RUN) python tests/local.py full-workflow

test-single: check-env check-infra
ifndef CMD
	@echo "ERROR: CMD is required. Example: make test-single CMD=ensure-registry"
	@echo "Available: ensure-registry, deploy-flow, start-flow, stop-flow, cleanup, configure-params, get-status"
	@exit 1
endif
	@echo "Testing command: $(CMD)"
	PYTHONPATH=$(CURDIR):$(CURDIR)/src:$$PYTHONPATH $(UV_RUN) python tests/local.py $(CMD)

# ============================================================================
# Act-based testing (GitHub Actions simulation)
# ============================================================================

# Generate .secrets file by reading config from nipyapi repo
generate-secrets: check-env
	@NIPYAPI_INFRA=$(NIPYAPI_INFRA) $(UV_RUN) python scripts/generate_secrets.py

test-act: check-env check-act check-infra generate-secrets
	@echo "Running CI workflow with act..."
	@act push \
		--container-architecture $(ACT_ARCH) \
		--network host \
		--secret-file .secrets \
		--env GITHUB_REPOSITORY=Chaffelson/nipyapi-actions \
		--env GITHUB_REF=refs/heads/main

test-act-verbose: check-env check-act check-infra generate-secrets
	@echo "Running CI workflow with act (verbose)..."
	@act push \
		--container-architecture $(ACT_ARCH) \
		--network host \
		--secret-file .secrets \
		--env GITHUB_REPOSITORY=Chaffelson/nipyapi-actions \
		--env GITHUB_REF=refs/heads/main \
		--verbose

# ============================================================================
# GitLab CI local testing
# ============================================================================

# Run just the setup test (no NiFi required)
gitlab-test: check-env
	@echo "Running GitLab CI setup test..."
	@echo "Ensuring nipyapi CLI is available..."
	@$(UV_RUN) python -c "import nipyapi.ci; print('nipyapi.ci available')" || \
		(echo "ERROR: nipyapi.ci not available. Run 'uv sync' first"; exit 1)
	@PATH="$(CURDIR)/.venv/bin:$$PATH" gitlab-ci-local \
		--force-shell-executor \
		--job test-setup \
		--variable LOCAL_TEST="true"

# Run full pipeline (requires NiFi running)
# Note: Uses LOCAL_TEST=true to skip DinD and use host NiFi
# Uses --force-shell-executor to bypass DinD service startup in gitlab-ci-local
# Supports both GH_REGISTRY_TOKEN and GL_REGISTRY_TOKEN
# Note: Requires nipyapi CLI to be installed - run 'uv sync' first
gitlab-test-all: check-env check-infra
	@echo "Running full GitLab CI pipeline (local mode)..."
	@echo "Ensuring nipyapi CLI is available..."
	@$(UV_RUN) python -c "import nipyapi.ci; print('nipyapi.ci available')" || \
		(echo "ERROR: nipyapi.ci not available. Run 'uv sync' first"; exit 1)
	@PATH="$(CURDIR)/.venv/bin:$$PATH" gitlab-ci-local \
		--force-shell-executor \
		--variable LOCAL_TEST="true" \
		--variable NIFI_API_ENDPOINT="https://localhost:9447/nifi-api" \
		--variable NIFI_FLOW_HOST="localhost" \
		--variable NIFI_USERNAME="einstein" \
		--variable NIFI_PASSWORD="password1234" \
		--variable NIFI_VERIFY_SSL="false" \
		--variable GH_REGISTRY_TOKEN="$(GH_REGISTRY_TOKEN)" \
		--variable GL_REGISTRY_TOKEN="$(GL_REGISTRY_TOKEN)" \
		--variable NIFI_REGISTRY_PROVIDER="$(NIFI_REGISTRY_PROVIDER)" \
		--variable NIFI_REGISTRY_REPO="$(or $(NIFI_REGISTRY_REPO),Chaffelson/nipyapi-actions)" \
		--variable NIFI_REGISTRY_CLIENT_NAME="gitlab-test-registry" \
		--variable NIFI_REPOSITORY_PATH="tests" \
		--variable NIFI_BUCKET="flows" \
		--variable NIFI_FLOW="cicd-demo-flow"

# Run full pipeline with GitLab registry (convenience target)
gitlab-test-gl: check-env check-infra
	@echo "Running GitLab CI with GitLab registry..."
	@$(MAKE) gitlab-test-all NIFI_REGISTRY_PROVIDER=gitlab NIFI_REGISTRY_REPO=nipyapi/nipyapi-actions

# Run a specific GitLab CI job
gitlab-test-job:
ifndef JOB
	@echo "ERROR: JOB is required. Example: make gitlab-test-job JOB=test-setup"
	@exit 1
endif
	@echo "Running GitLab CI job: $(JOB)"
	@gitlab-ci-local --job $(JOB)

# ============================================================================
# Infrastructure management (delegates to nipyapi repo)
# ============================================================================

infra-up:
	@if [ ! -d "$(NIPYAPI_INFRA)" ]; then \
		echo "ERROR: nipyapi repo not found at $(NIPYAPI_INFRA)"; \
		echo "Override: NIPYAPI_INFRA=/path/to/nipyapi make infra-up"; \
		exit 1; \
	fi
	@echo "Starting NiFi infrastructure..."
	@cd $(NIPYAPI_INFRA) && make certs && make up NIPYAPI_PROFILE=github-cicd

infra-down:
	@if [ -d "$(NIPYAPI_INFRA)" ]; then \
		cd $(NIPYAPI_INFRA) && make down; \
	fi

infra-ready:
	@if [ ! -d "$(NIPYAPI_INFRA)" ]; then \
		echo "ERROR: nipyapi repo not found at $(NIPYAPI_INFRA)"; \
		exit 1; \
	fi
	@cd $(NIPYAPI_INFRA) && make wait-ready NIPYAPI_PROFILE=github-cicd

# ============================================================================
# Checks and utilities
# ============================================================================

check-env:
ifndef GH_REGISTRY_TOKEN
	@echo "ERROR: GH_REGISTRY_TOKEN is not set"
	@echo "Set in environment or create .env from .env.example"
	@exit 1
endif
	@echo "Environment OK"

check-act:
	@which act > /dev/null || (echo "ERROR: act not installed. Run: brew install act" && exit 1)
	@docker info > /dev/null 2>&1 || (echo "ERROR: Docker not running" && exit 1)
	@echo "act and Docker OK"

check-infra:
	@echo "Checking NiFi at: $(NIFI_API_ENDPOINT)"
	@curl -sk $(NIFI_API_ENDPOINT)/access/config > /dev/null 2>&1 || \
		(echo "ERROR: NiFi not responding"; \
		 echo "Start it: make infra-up"; \
		 exit 1)
	@echo "NiFi OK"

lint:
	@echo "Checking Python code style..."
	@$(UV_RUN) python -m py_compile core/*.py adapters/*/*.py tests/local.py scripts/*.py
	@echo "Syntax OK"

clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .act-* 2>/dev/null || true
	@rm -f .secrets 2>/dev/null || true
	@rm -rf .venv 2>/dev/null || true
	@rm -f uv.lock 2>/dev/null || true
	@echo "Done"
