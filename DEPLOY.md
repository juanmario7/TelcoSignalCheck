# Documento de Requisitos para Despliegue en AWS
**Proyecto:** VMContigo — Encuesta de Cobertura Virgin Mobile
**Repositorio:** https://github.com/juanmario7/TelcoSignalCheck
**Dominio:** vmcontigo.co
**Fecha:** Marzo 2026

---

## 1. Descripción del Proyecto

Aplicación web que permite recopilar reportes de calidad de señal de usuarios de Virgin Mobile Colombia. Consta de:

- **Formulario móvil** (`/form?phone=NUMERO`): encuesta multi-paso para usuarios finales
- **Dashboard** (`/dashboard`): panel de análisis con mapas y gráficas para el equipo interno

---

## 2. Stack Tecnológico

| Componente | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.11 |
| Framework | FastAPI | 0.115.0 |
| Servidor | Uvicorn | 0.30.6 |
| Base de datos | PostgreSQL | 14+ |
| Frontend | HTML + JavaScript (sin frameworks) | — |

---

## 3. Infraestructura Requerida

### 3.1 Servidor de Aplicación
- **Tipo sugerido:** EC2 `t3.small` o Lightsail equivalente
- **SO:** Ubuntu 22.04 LTS
- **RAM mínima:** 512 MB
- **Región recomendada:** `sa-east-1` (São Paulo) por proximidad a Colombia
- **Puerto expuesto:** 8080 (HTTP interno), 443 (HTTPS público)

### 3.2 Base de Datos
- **Motor:** PostgreSQL 14 o superior
- **Tipo sugerido:** RDS `db.t3.micro` o Lightsail Managed Database
- **Almacenamiento:** 5 GB inicial (suficiente para cientos de miles de registros)
- **La aplicación crea la tabla automáticamente** al arrancar (no requiere scripts de migración manuales)

---

## 4. Variables de Entorno

La aplicación requiere las siguientes variables de entorno configuradas en el servidor:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@host:5432/dbname` |
| `GOOGLE_MAPS_API_KEY` | API Key de Google Maps (Geocoding + Places) | `AIzaSy...` |

> ⚠️ Estas variables **no deben** estar en el código fuente ni en el repositorio.

---

## 5. Comando de Arranque

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

O usando el `Procfile` incluido en el repositorio:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 6. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

Dependencias principales:
- `fastapi`
- `uvicorn`
- `psycopg2-binary`
- `requests`
- `python-dotenv`

---

## 7. Configuración de Red y Seguridad

- **HTTPS obligatorio** — el formulario usa geolocalización del navegador, la cual requiere HTTPS
- **Certificado SSL:** se puede usar AWS Certificate Manager (ACM) con un Application Load Balancer, o Let's Encrypt directamente en el servidor
- **Firewall:** solo exponer puertos 80 y 443 públicamente; el puerto de PostgreSQL debe ser privado (no accesible desde internet)

---

## 8. Dominio

El dominio `vmcontigo.co` está registrado en Namecheap. Una vez desplegada la aplicación, se necesita:

1. La **IP pública** o el **CNAME** del servidor/load balancer en AWS
2. El equipo solicitante actualizará el DNS en Namecheap para apuntar al nuevo servidor

---

## 9. APIs Externas

| API | Proveedor | Uso |
|---|---|---|
| Maps JavaScript API | Google Cloud | Autocomplete de direcciones en el formulario |
| Places API | Google Cloud | Sugerencias de direcciones |
| Geocoding API | Google Cloud | Conversión de dirección a coordenadas |

> La API Key de Google Maps debe tener como **sitio web autorizado**: `https://vmcontigo.co/*`

---

## 10. Consideraciones de Privacidad

- La aplicación recopila datos personales de usuarios (teléfono, ubicación)
- Se recomienda desplegar en la región **`sa-east-1` (São Paulo)** como la más cercana a Colombia disponible en AWS
- El tratamiento de datos se rige bajo la **Ley 1581 de 2012** de Colombia
- Se recomienda revisar con el equipo legal/compliance de Virgin Mobile antes del despliegue en producción con datos reales

---

## 11. Contacto del Proyecto

Para dudas técnicas sobre el código o arquitectura, contactar al responsable del proyecto interno de Virgin Mobile.
