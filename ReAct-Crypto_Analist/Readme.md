 # Proyecto de Prueba Python

Este proyecto es una prueba que utiliza Python y la API de Groq.

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Configuración del Entorno

### 1. Crear un Entorno Virtual

Primero, necesitas crear un entorno virtual para aislar las dependencias del proyecto. Abre una terminal y ejecuta:

```bash
# En Windows
python -m venv venv

# En macOS/Linux
python3 -m venv venv
```

### 2. Activar el Entorno Virtual

```bash
# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar Dependencias

Una vez activado el entorno virtual, instala las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

### 4. Configurar Variable de Entorno de Groq

1. Crea un archivo `.env` en la raíz del proyecto
2. Añade tu clave API de Groq en el archivo:

```env
GROQ_API_KEY=tu_clave_api_aquí
```


## Notas Importantes

- No olvides añadir `.env` a tu archivo `.gitignore` para evitar compartir tus claves API
- Mantén el entorno virtual activado mientras trabajas en el proyecto
- Para desactivar el entorno virtual, simplemente ejecuta `deactivate` en la terminal

## Solución de Problemas

Si encuentras algún problema durante la instalación o configuración:

1. Asegúrate de que el entorno virtual está activado (deberías ver `(venv)` en tu terminal)
2. Verifica que todas las dependencias están instaladas correctamente con `pip list`
3. Comprueba que el archivo `.env` está en la ubicación correcta y contiene la variable de entorno necesaria