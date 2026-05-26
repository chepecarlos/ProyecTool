.DEFAULT_GOAL := help

# ─── Variables ────────────────────────────────────────────────────────────────
UV      := uv
PACKAGE := proyectool

# ─── Ayuda ────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  proyectool — comandos disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ─── Instalación ──────────────────────────────────────────────────────────────
.PHONY: install
install: ## Instala el paquete y sus dependencias
	$(UV) sync

.PHONY: install-dev
install-dev: ## Instala incluyendo dependencias de desarrollo
	$(UV) sync --all-extras

.PHONY: dev
dev: ## Instala en modo editable (desarrollo activo)
	$(UV) pip install -e .

.PHONY: global
global: ## Instala proyectool globalmente (disponible en todo el sistema)
	$(UV) tool install . --reinstall

.PHONY: dev-global
dev-global: ## Instala globalmente en modo editable (cambios se reflejan al instante)
	$(UV) tool install . --reinstall --editable

# ─── Ejecución ────────────────────────────────────────────────────────────────
.PHONY: run
run: ## Ejecuta proyectool (uso: make run ARGS="--help")
	$(UV) run $(PACKAGE) $(ARGS)

# ─── Calidad de código ────────────────────────────────────────────────────────
.PHONY: lint
lint: ## Revisa el código con ruff
	$(UV) run ruff check src/

.PHONY: format
format: ## Formatea el código con ruff
	$(UV) run ruff format src/

.PHONY: check
check: lint ## Alias de lint

# ─── Limpieza ─────────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Elimina archivos temporales y caché
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .ruff_cache dist build

.PHONY: clean-all
clean-all: clean ## Elimina también el entorno virtual
	rm -rf .venv
