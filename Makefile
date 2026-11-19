.DEFAULT_GOAL := help

CLAUDE ?= claude

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

.PHONY: install-hooks
install-hooks: ## Install the git hooks from hooks/
	ln -sf ../../hooks/pre-commit .git/hooks/pre-commit

.PHONY: bootstrap
bootstrap: install-hooks ## Install the checks' dependencies, in a virtualenv
	pip install --upgrade pip setuptools
	pip install -r requirements.txt

.PHONY: test
test: ## Run the checks: manifests, frontmatter, links and content
	pytest

.PHONY: lint
lint: ## Check the Python's formatting and lint it
	black --check .
	pylint tests

.PHONY: format
format: ## Format the Python
	black .

.PHONY: validate
validate: ## Run Claude Code's validator on the marketplace and the plugin (CLAUDE= names the binary)
	$(CLAUDE) plugin validate .
	$(CLAUDE) plugin validate ./plugins/loopproof

.PHONY: clean
clean: ## Remove caches and the CI validator's node_modules
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache ci/node_modules
