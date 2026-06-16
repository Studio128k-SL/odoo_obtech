# Odoo OBTech con Docker

Repositorio para levantar un entorno de Odoo con PostgreSQL y PgAdmin usando Docker Compose.

## Variables de entorno Producción
- ODOO_MASTER_PASSWORD: y9qj-2qms-vdng
- ODOO_USER: info@studio128k.com
- ODOO_DATABASE_NAME: odoo
- ODOO_USER_PASSWORD: odoo

## Requisitos

- Docker Engine (o Docker Desktop) instalado y en ejecución.
- Docker Compose disponible (`docker compose` o `docker-compose`).
- `make` instalado (recomendado para usar el `Makefile`).
- Puertos libres:
  - Local/base: `80`, `8072`, `8080`.
  - Producción (`docker-compose.prod.yml`): `80`, `81`, `443`, `8080`.

## Estructura principal

- `docker-compose.dev.yml`: entorno local/desarrollo (Odoo + DB + PgAdmin).
- `docker-compose.prod.yml`: entorno de producción (incluye Nginx Proxy Manager).
- `docker-compose.mac.yml`: variante para Mac.
- `Makefile`: comandos de operación diaria.
- `data/odoo/config/odoo.conf`: configuración Odoo local/base.
- `data/odoo/config-prod/odoo.conf`: configuración Odoo producción.
- `data/odoo/addons`: addons extra montados en el contenedor.
- `data/odoo/custom_addons`: addons personalizados montados en el contenedor.

## Configuración inicial

1. Crear archivo de entorno:

```bash
cp .env.example .env
```

2. Revisar y ajustar variables sensibles en `.env` (DB, PgAdmin, correo, etc.).
3. Revisar `odoo.conf` según entorno:
   - Local/base: `data/odoo/config/odoo.conf`
   - Producción: `data/odoo/config-prod/odoo.conf`

## Cómo levantar el proyecto

    make env=dev up

## Copiar base de datos
Para restaurar la base de datos debemos realizar las siguientes tareas

1. Borrar la base de datos `odoo` desde el gestor de Odoo. `http://localhos/web/database/manager`. Para eliminarla necesitaremos la `ODOO_MASTER_PASSWORD` ubicada en este documento. Al terminar de borrarla nos dará error 500.

2. Paramos el servidor con `make env=dev down`.

3. Comentar el config en el docker compose que se esté usando en ese momento. En este caso 

```yaml
    # docker-compose.dev.yml
    odoo:
        build:
        context: ./infrastructure/odoo
        dockerfile: Dockerfile
        container_name: obtech_odoo
        command: --dev all --log-level debug
        depends_on:
        - db
        volumes:
        - obtech-odoo-data:/var/lib/odoo
        #- ./data/odoo/config:/etc/odoo   // Comentar esta línea
        - ./data/odoo/addons:/mnt/extra-addons
        - ./data/odoo/custom_addons:/mnt/custom-addons
```

4. Levantar el servidor y acceder de nuevo a `http://localhost/web/database/manager`, y pulsar en restore database.

5. Introducimos de nuevo la master password, subimos el zip y ponemos el mismo nombre de la base de datos que está configurado en `./data/odoo/config` en caso de entorno de desarrollo y `./data/odoo/config_prod` en caso de producción.

6. Ahora endremos que descomentar el archvo `docker-compose.dev.yml` para que se vuelva a establecer la configuración del archivo.

```yaml
    # docker-compose.dev.yml
    odoo:
        build:
        context: ./infrastructure/odoo
        dockerfile: Dockerfile
        container_name: obtech_odoo
        command: --dev all --log-level debug
        depends_on:
        - db
        volumes:
        - obtech-odoo-data:/var/lib/odoo
        - ./data/odoo/config:/etc/odoo   # Descomentar esta línea
        - ./data/odoo/addons:/mnt/extra-addons
        - ./data/odoo/custom_addons:/mnt/custom-addons
```

7. Apagamos y encendemos de nuevo el servidor para que se apliquen los cambios `make env=dev down` y `make env=dev up`

Listo. Con esto tendremos restaurada una copia de seguridad hecha desde el administrador de bases de datos de Odoo.


## Instalar plugins personalizados

Los plugins personalizados se cargan desde el volumen `./data/odoo/custom_addons` (mapeado dentro del contenedor como `/mnt/custom-addons`).

### 1) Copiar el módulo al directorio correcto

- Coloca cada plugin en una carpeta propia dentro de:
  - `data/odoo/custom_addons` (dev/prod)
- Verifica que el módulo tenga `__manifest__.py`.

Ejemplo:

```bash
data/odoo/custom_addons/mi_modulo/__manifest__.py
```

### 2) Levantar/reiniciar el entorno

```bash
make env=dev up
make env=dev restart c=odoo
```

### 3) Instalar el plugin en Odoo

Instala el módulo por nombre técnico:

```bash
make env=dev install_modules modules=mi_modulo
```

Si el módulo ya estaba instalado y solo hiciste cambios:

```bash
make env=dev update_modules modules=mi_modulo
```

### 4) Verificar instalación

- Entra a Odoo: [http://localhost](http://localhost)
- Activa modo desarrollador.
- Ve a **Apps** y actualiza la lista de aplicaciones.
- Busca el módulo por nombre técnico o funcional y confirma que esté instalado.

### Comandos útiles para depuración

```bash
make env=dev logs_odoo
make env=dev connect_odoo
```

Documentación de despliegu