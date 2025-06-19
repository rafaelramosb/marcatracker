# Actualización del Almacenamiento y Comparación de Imágenes

Este documento describe las actualizaciones realizadas al sistema para mejorar el almacenamiento de archivos y la comparación de imágenes de logos.

## Cambios en el Almacenamiento de Archivos

### 1. Estructura de Directorios

Se ha implementado una estructura de directorios organizada para almacenar diferentes tipos de archivos:

```
marca_tracker_app/
├── storage/
│   ├── gacetas/      # Almacenamiento de PDFs de la Gaceta
│   │   ├── 2025/     # Organizado por año
│   │   │   ├── 01/   # Y por mes
│   │   │   ├── 02/
│   │   │   └── ...
│   ├── logos/        # Almacenamiento de imágenes de logos
│   │   ├── 2025/
│   │   │   ├── 01/
│   │   │   └── ...
│   └── json/         # Almacenamiento de datos JSON
```

### 2. Nuevos Modelos de Datos

Se han añadido dos nuevos modelos para gestionar las referencias a archivos:

- **GacetaDocument**: Almacena referencias a los PDFs de la Gaceta
- **LogoImage**: Almacena referencias a las imágenes de logos

Estos modelos permiten mantener en la base de datos solo las referencias a los archivos, mientras que los archivos binarios se almacenan en el sistema de archivos.

## Implementación de Comparación de Imágenes

### 1. Servicio de Comparación de Imágenes

Se ha implementado un nuevo servicio `ImageComparisonService` que proporciona:

- Comparación de logos mediante histogramas y características SIFT
- Descarga y almacenamiento eficiente de imágenes de logos
- Cálculo de puntuaciones de similitud visual

### 2. Algoritmos de Comparación Visual

La comparación de imágenes utiliza varios métodos:

- **Comparación de histogramas**: Para similitud general de color y tono
- **Detección de características SIFT**: Para identificar puntos clave y formas
- **Ratio test de Lowe**: Para filtrar coincidencias de alta calidad

### 3. Integración con el Flujo de Trabajo

El servicio de comparación de imágenes se integra con:

- El scraper web para procesar logos encontrados en la SIC
- El sistema de alertas para notificar similitudes visuales
- El sistema de gestión de marcas para almacenar y comparar logos de usuarios

## Mejoras en el Procesamiento de PDFs

### 1. Almacenamiento Eficiente

Los PDFs de la Gaceta ahora:

- Se almacenan en el sistema de archivos con estructura año/mes
- Se registran en la base de datos mediante el modelo GacetaDocument
- Se procesan y extraen a archivos JSON para análisis posterior

### 2. Procesamiento de Datos Extraídos

Los datos extraídos de los PDFs:

- Se almacenan en archivos JSON en la carpeta storage/json
- Mantienen referencias al documento original
- Son accesibles para análisis sin necesidad de reprocesar los PDFs

## Pruebas y Validación

Se han implementado pruebas unitarias para:

- Verificar el correcto funcionamiento del almacenamiento de archivos
- Validar los algoritmos de comparación de imágenes
- Comprobar la integración con el resto del sistema

## Consideraciones de Seguridad

- Los directorios de almacenamiento se crean con permisos adecuados
- Se validan los tipos de archivo antes de procesarlos
- Se implementan mecanismos para evitar desbordamientos de buffer en el procesamiento de imágenes
