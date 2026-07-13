# APsystems Alert Monitor

Sistema de monitoreo automatico de instalaciones solares APsystems con deteccion de alertas y notificaciones por email.

## Caracteristicas

- Soporte multi-cuenta (multiples App ID + App Secret)
- Deteccion de estado via campo `light` (verde/amarillo/rojo/gris)
- Alertas por email via SMTP Microsoft 365
- Reporte diario consolidado
- Contabilidad de llamadas API (limite 1000/mes por cuenta)
- PostgreSQL para historial y auditoria
- Docker para despliegue sencillo

## Requisitos

- Docker + Docker Compose
- Cuenta de APsystems OpenAPI (App ID, App Secret, System IDs)
- Servidor SMTP (Microsoft 365 o similar)

## Instalacion Rápida

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/apsystems-alert-monitor.git
cd apsystems-alert-monitor

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar
docker compose up -d

# 4. Ver logs
docker compose logs -f monitor
```

## Configuracion

### Cuentas API

```env
ACCOUNT1_NAME=Residencial
ACCOUNT1_APP_ID=tu_app_id_aqui
ACCOUNT1_APP_SECRET=tu_app_secret
ACCOUNT1_BASE_URL=https://api.apsystemsema.com:9282
ACCOUNT1_SYSTEMS=SID001,SID002,SID003
```

### SMTP Microsoft 365

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=alertas@tudominio.com
SMTP_PASSWORD=contrasena_de_aplicacion
SMTP_FROM=Monitor Solar <alertas@tudominio.com>
ALERT_TO=soporte@tudominio.com
```

### PostgreSQL

```env
DB_HOST=postgres
DB_PORT=5432
DB_USER=apsystems
DB_PASSWORD=contrasena_segura
DB_NAME=apsystems_monitor
```

## Tipos de Alerta

| Estado | light | Significado | Severidad |
|--------|-------|-------------|-----------|
| Verde | 1 | Sistema funcionando normal | info |
| Amarillo | 2 | Inversor con alarma | warning |
| Rojo | 3 | ECU sin conexion | critical |
| Gris | 4 | Sin datos subidos | critical |

## Uso de API

El monitor consume el endpoint batch de APsystems:

```
POST /patch/api/v2/systems (50 sistemas por pagina)
```

Con 10 sistemas: ~1-2 llamadas/dia = ~30-60/mes (de 1000 disponibles).

## Estructura del Proyecto

```
apsystems-alert-monitor/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── src/
│   ├── main.py              # Scheduler
│   ├── config.py            # Configuracion multi-cuenta
│   ├── api/
│   │   ├── client.py        # Cliente HMAC-SHA256
│   │   └── models.py        # Modelos de datos
│   ├── monitor/
│   │   ├── batch.py         # Consumo batch endpoint
│   │   ├── checker.py       # Logica de verificacion
│   │   └── rules.py         # Reglas de alerta
│   ├── notify/
│   │   ├── email_sender.py  # Envio SMTP
│   │   └── templates/       # Templates HTML
│   └── storage/
│       └── db.py            # PostgreSQL
├── migrations/
│   └── 001_initial.sql      # Esquema de base de datos
└── .github/workflows/
    └── deploy.yml           # CI/CD a DigitalOcean
```

## Despliegue en DigitalOcean

### Opcion A: Droplet + Docker Compose

```bash
# En el droplet (Ubuntu 22.04)
sudo apt update && sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
newgrp docker

git clone https://github.com/tu-usuario/apsystems-alert-monitor.git
cd apsystems-alert-monitor
cp .env.example .env
# Editar .env con credenciales reales
docker compose up -d
```

### Opcion B: GitHub Actions (Auto-deploy)

Configurar secrets en GitHub:
- `DO_HOST`: IP del droplet
- `DO_USER`: usuario SSH
- `DO_SSH_KEY`: clave SSH privada

Push a `main` activa el deploy automatico.

## Monitoreo

```bash
# Ver logs en tiempo real
docker compose logs -f monitor

# Ver estado de la base de datos
docker compose exec postgres psql -U apsystems -d apsystems_monitor -c "SELECT * FROM daily_summary ORDER BY date DESC LIMIT 5;"

# Contar llamadas API este mes
docker compose exec postgres psql -U apsystems -d apsystems_monitor -c "SELECT account_name, COUNT(*) as calls FROM api_calls WHERE created_at >= date_trunc('month', NOW()) GROUP BY account_name;"
```

## Licencia

MIT
