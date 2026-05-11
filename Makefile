# Makefile para proyecto Odoo OBTech

file_selected := -f docker-compose.$(env).yml
environment := $(env)
DOCKER_COMPOSE := $(shell docker-compose version >/dev/null 2>&1 && echo "docker-compose" || (docker compose version >/dev/null 2>&1 && echo "docker compose"))
DB_NAME := odoo

# Comandos básicos de Docker
up:
	@$(DOCKER_COMPOSE) $(file_selected) up -d

ps:
	@$(DOCKER_COMPOSE) $(file_selected) ps

down:
	@$(DOCKER_COMPOSE) $(file_selected) down

build:
	@$(DOCKER_COMPOSE) $(file_selected) build $(c)

build_no_cache:
	@$(DOCKER_COMPOSE) $(file_selected) build $(c) --no-cache

restart:
	@$(DOCKER_COMPOSE) $(file_selected) restart $(c)

logs:
	@$(DOCKER_COMPOSE) $(file_selected) logs -f $(c)

logs_odoo:
	@$(DOCKER_COMPOSE) $(file_selected) logs -f odoo

logs_db:
	@$(DOCKER_COMPOSE) $(file_selected) logs -f db

connect:
	@$(DOCKER_COMPOSE) $(file_selected) exec -it -u root $(c) bash

connect_odoo:
	@$(DOCKER_COMPOSE) $(file_selected) exec odoo bash

connect_db:
	@$(DOCKER_COMPOSE) $(file_selected) exec db bash

connect_root:
	@$(DOCKER_COMPOSE) $(file_selected) exec -u root $(c) bash

# Comandos específicos de Odoo
init_database:
	@$(DOCKER_COMPOSE) $(file_selected) run --rm odoo --dev all --log-level debug -i base -d $(DB_NAME) --stop-after-init

init_database_demo:
	@$(DOCKER_COMPOSE) $(file_selected) run --rm odoo --dev all --log-level debug -i base -d $(DB_NAME) --stop-after-init --load-language=es_ES

install_modules:
	@$(DOCKER_COMPOSE) $(file_selected) run --rm odoo -i $(modules) -d $(DB_NAME) --stop-after-init

update_modules:
	@$(DOCKER_COMPOSE) $(file_selected) run --rm odoo -u $(modules) -d $(DB_NAME) --stop-after-init

shell_odoo:
	@$(DOCKER_COMPOSE) $(file_selected) run --rm odoo shell -d $(DB_NAME)

# Comandos de base de datos
dump_database:
	@$(DOCKER_COMPOSE) $(file_selected) exec -T db pg_dump -U studio128k_odoo_user $(DB_NAME) > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore_database:
	@$(DOCKER_COMPOSE) $(file_selected) exec -T db psql -U studio128k_odoo_user -d $(DB_NAME) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@$(DOCKER_COMPOSE) $(file_selected) exec -T db psql -U studio128k_odoo_user -d $(DB_NAME) < $(file)

psql:
	@$(DOCKER_COMPOSE) $(file_selected) exec -T db psql -U odoo -d $(DB_NAME)

# Instalación y configuración
copy_env_vars:
	@if [ -f .env.example ]; then cp .env.example .env; fi

install: copy_env_vars up init_database

# Comandos de desarrollo
dev_up:
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d

dev_down:
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

dev_logs:
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

dev_build:
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml build $(c)

# Comandos de producción
prod_up:
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

prod_down:
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

prod_logs:
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f

prod_build:
	@$(DOCKER_COMPOSE) -f docker-compose.prod.yml build $(c)

# Comandos de Mac
mac_up:
	@$(DOCKER_COMPOSE) -f docker-compose.mac.yml up -d

mac_down:
	@$(DOCKER_COMPOSE) -f docker-compose.mac.yml down

mac_logs:
	@$(DOCKER_COMPOSE) -f docker-compose.mac.yml logs -f

mac_build:
	@$(DOCKER_COMPOSE) -f docker-compose.mac.yml build $(c)

# Comandos de limpieza
clean:
	@$(DOCKER_COMPOSE) $(file_selected) down -v --remove-orphans
	@docker system prune -f

clean_soft:
	@$(DOCKER_COMPOSE) $(file_selected) down --remove-orphans

install_addons:
	@echo "🚀 Instalando addons para entorno $(env)..."
	@$(DOCKER_COMPOSE) $(file_selected) exec -T -u root odoo bash -c "bash /mnt/scripts/install_addons.sh"
	@echo "✅ Addons instalados correctamente."

# Deploy y gestión de código
pull_code:
	git checkout main
	git pull

deploy: down pull_code up install

# Información del proyecto
info:
	@echo "Proyecto: Odoo OBTech"
	@echo "Base de datos: $(DB_NAME)"
	@echo "Entorno: $(environment)"
	@echo "URLs:"
	@echo "  - Odoo: http://localhost"
	@echo "  - PgAdmin: http://localhost:8080"
	@echo "  - Longpolling: http://localhost:8072"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make env=dev up          - Levantar entorno desarrollo"
	@echo "  make env=prod up         - Levantar entorno producción"
	@echo "  make env=mac up          - Levantar entorno Mac"
	@echo "  make env=dev install     - Instalación completa desarrollo"
	@echo "  make init_database       - Inicializar base de datos"
	@echo "  make logs_odoo           - Ver logs de Odoo"
	@echo "  make shell_odoo          - Acceder shell de Odoo"