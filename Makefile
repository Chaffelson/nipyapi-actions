# NiPyAPI Actions Makefile
# Commands for development, testing, and local act simulation

SHELL := /bin/bash

# Python interpreter - override with PYTHON=python3 if needed
PYTHON ?= python

# ============================================================================
# Infrastructure configuration
# ============================================================================

# Path to nipyapi repository (override if checked out elsewhere)
NIPYAPI_INFRA ?= ../nipyapi

# Derive env file path from infrastructure location
NIPYAPI_ENV_FILE := $(NIPYAPI_INFRA)/.env

# Load environment from nipyapi repo if available
# This provides GH_REGISTRY_TOKEN
ifneq (,$(wildcard $(NIPYAPI_ENV_FILE)))
    include $(NIPYAPI_ENV_FILE)
    export
endif

# NiFi endpoint for connectivity checks (read from compose.yml by scripts)
NIFI_API_ENDPOINT ?= https://localhost:9447/nifi-api

# ============================================================================
# Act settings (for local GitHub Actions simulation)
# ============================================================================

ACT_ARCH := linux/amd64
ACT_IMAGE ?= catthehacker/ubuntu:act-latest

# ============================================================================
# Targets
# ============================================================================

.PHONY: help test test-python test-act test-act-verbose test-single lint clean \
        infra-up infra-down infra-ready check-env check-act check-infra generate-secrets

help:
	@echo "NiPyAPI Actions Development Commands"
	@echo ""
	@echo "Testing (Python - direct):"
	@echo "  make test              - Run full workflow test (Python)"
	@echo "  make test-single CMD=X - Test single command"
	@echo ""
	@echo "Testing (act - GitHub Actions simulation):"
	@echo "  make test-act          - Run CI workflow with act"
	@echo "  make test-act-verbose  - Run with debug output"
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
	@echo "  PYTHON                 - Python interpreter (default: python)"
	@echo "  GH_REGISTRY_TOKEN      - Required (set in env or nipyapi/.env)"
	@echo ""

# ============================================================================
# Python-based testing (direct execution)
# ============================================================================

test: check-env check-infra
	@echo "Running full workflow test..."
	PYTHONPATH=$(CURDIR):$(CURDIR)/src:$$PYTHONPATH $(PYTHON) tests/local.py full-workflow

test-python: test

test-single: check-env check-infra
ifndef CMD
	@echo "ERROR: CMD is required. Example: make test-single CMD=ensure-registry"
	@echo "Available: ensure-registry, deploy-flow, start-flow, stop-flow, cleanup, configure-params, get-status"
	@exit 1
endif
	@echo "Testing command: $(CMD)"
	PYTHONPATH=$(CURDIR):$(CURDIR)/src:$$PYTHONPATH $(PYTHON) tests/local.py $(CMD)

# ============================================================================
# Act-based testing (GitHub Actions simulation)
# ============================================================================

# Generate .secrets file by reading config from nipyapi repo
generate-secrets: check-env
	@NIPYAPI_INFRA=$(NIPYAPI_INFRA) $(PYTHON) scripts/generate_secrets.py

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
	@echo "Set in environment or in $(NIPYAPI_ENV_FILE)"
	@exit 1
endif
	@echo "Environment OK"

check-act:
	@which act > /dev/null || (echo "ERROR: act not installed. Run: brew install act" && exit 1)
	@docker info > /dev/null 2>&1 || (echo "ERROR: Docker not running" && exit 1)
	@echo "act and Docker OK"

check-infra:
	@curl -sk $(NIFI_API_ENDPOINT)/access/config > /dev/null 2>&1 || \
		(echo "ERROR: NiFi not responding at $(NIFI_API_ENDPOINT)"; \
		 echo "Start it: make infra-up"; \
		 exit 1)
	@echo "NiFi OK"

lint:
	@echo "Checking Python code style..."
	@$(PYTHON) -m py_compile src/*.py tests/local.py scripts/*.py
	@echo "Syntax OK"

clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .act-* 2>/dev/null || true
	@rm -f .secrets 2>/dev/null || true
	@echo "Done"
