# Manual de Despliegue y Uso - MarcaTracker

## Descripción General

MarcaTracker es una aplicación web desarrollada para el seguimiento de marcas registradas en Colombia. Permite a los usuarios monitorear sus marcas, recibir alertas sobre posibles conflictos, gestionar suscripciones y comparar marcas con registros de la Superintendencia de Industria y Comercio (SIC).

## Estructura del Proyecto

```
marca_tracker_app/
├── venv/                      # Entorno virtual de Python
├── src/                       # Código fuente de la aplicación
│   ├── models/                # Modelos de datos
│   │   ├── __init__.py        # Inicialización de modelos
│   │   ├── user.py            # Modelo de usuarios
│   │   ├── subscription.py    # Modelo de suscripciones
│   │   ├── trademark.py       # Modelo de marcas
│   │   └── alert.py           # Modelo de alertas
│   ├── routes/                # Rutas de la API
│   │   ├── auth.py            # Rutas de autenticación
│   │   ├── trademark.py       # Rutas de gestión de marcas
│   │   ├── subscription.py    # Rutas de suscripciones
│   │   ├── alert.py           # Rutas de alertas
│   │   └── integration.py     # Rutas de integración con SIC
│   ├── static/                # Archivos estáticos
│   │   ├── img/               # Imágenes
│   │   └── index.html         # Página principal
│   └── main.py                # Punto de entrada de la aplicación
├── integracion_sic.md         # Documentación de integración con SIC
└── requirements.txt           # Dependencias del proyecto
```

## Requisitos Previos

- Python 3.8 o superior
- MySQL 5.7 o superior
- Pip (gestor de paquetes de Python)
- Entorno virtual de Python (opcional pero recomendado)

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <url_del_repositorio>
cd marca_tracker_app
```

### 2. Configurar el Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la Base de Datos

Asegúrese de tener MySQL instalado y en ejecución. Luego, cree una base de datos para la aplicación:

```sql
CREATE DATABASE marca_tracker;
```

Configure las variables de entorno para la conexión a la base de datos:

```bash
export DB_USERNAME=root
export DB_PASSWORD=password
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=marca_tracker
```

En Windows, use `set` en lugar de `export`.

### 5. Inicializar la Base de Datos

La aplicación creará automáticamente las tablas necesarias al iniciar por primera vez.

## Ejecución de la Aplicación

### Desarrollo Local

```bash
cd marca_tracker_app
source venv/bin/activate  # En Windows: venv\Scripts\activate
python src/main.py
```

La aplicación estará disponible en `http://localhost:5000`.

### Producción

Para entornos de producción, se recomienda utilizar Gunicorn como servidor WSGI:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

## Configuración de Integración con la SIC

La aplicación está diseñada para integrarse con la Superintendencia de Industria y Comercio (SIC) a través de diferentes métodos:

1. **Gaceta de Propiedad Industrial**: Descarga y procesamiento automático de la publicación oficial.
2. **Scraping del Portal Web**: Extracción de datos del sitio web de la SIC.
3. **Portal de Datos Abiertos**: Consumo de datos desde el portal de datos abiertos de Colombia.
4. **Servicios Web**: Integración con APIs oficiales (si están disponibles).

Para configurar estas integraciones, acceda al panel de administración y configure las fuentes de datos en la sección correspondiente.

## Gestión de Usuarios y Suscripciones

### Creación de Planes de Suscripción

Para crear planes de suscripción, debe acceder con una cuenta de administrador y utilizar la API de administración:

```
POST /api/subscriptions/admin/plans
```

Con el siguiente formato de datos:

```json
{
  "name": "Plan Básico",
  "description": "Plan básico para seguimiento de marcas",
  "price": 49900,
  "duration_months": 1,
  "max_trademarks": 3,
  "features": "Alertas básicas, Comparación por nombre",
  "is_premium": false
}
```

### Registro de Usuarios

Los usuarios pueden registrarse a través de la interfaz web o mediante la API:

```
POST /api/auth/register
```

Con el siguiente formato de datos:

```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña_segura",
  "first_name": "Nombre",
  "last_name": "Apellido",
  "company_name": "Empresa S.A."
}
```

## Monitoreo y Mantenimiento

### Logs del Sistema

La aplicación genera logs que pueden ser útiles para el diagnóstico de problemas:

- Logs de la aplicación Flask
- Logs de sincronización con fuentes de datos
- Logs de errores y excepciones

### Respaldos de Base de Datos

Se recomienda configurar respaldos periódicos de la base de datos para evitar pérdida de información:

```bash
mysqldump -u [usuario] -p [base_de_datos] > backup_$(date +%Y%m%d).sql
```

## Solución de Problemas Comunes

### Error de Conexión a la Base de Datos

Verifique:
- Que el servidor MySQL esté en ejecución
- Que las credenciales sean correctas
- Que la base de datos exista

### Problemas con la Integración SIC

Si la sincronización con la SIC falla:
- Verifique la conectividad a Internet
- Confirme que las URLs de las fuentes sean correctas
- Revise los logs de sincronización para identificar errores específicos

## Contacto y Soporte

Para soporte técnico o consultas sobre la aplicación, contacte a:

- Email: soporte@marcatracker.co
- Teléfono: +57 601 123 4567

---

© 2025 MarcaTracker. Todos los derechos reservados.
