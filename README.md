# Descargar materiales de UJAP (script)

Este repositorio contiene el script `download_ujap_materials.py` que automatiza la descarga de recursos desde el aula virtual de la Universidad (Moodle) usando Playwright + requests.

**Qué hace**

- Automatiza el inicio de sesión en `https://aulavirtual.ujap.edu.ve`.
- Navega a la lista de cursos del usuario y detecta recursos (archivos, enlaces, carpetas).
- Para recursos tipo `mod/resource` resuelve la URL final (buscando enlaces `pluginfile.php` o redirecciones intermedias) y descarga el archivo usando `requests` con las cookies del navegador Playwright.
- Guarda enlaces externos en un archivo de texto por curso y guarda referencias manuales cuando no se detecta un `pluginfile.php`.

**Requisitos**

- Windows 10/11 (las instrucciones de activación del virtualenv están para PowerShell).
- Python 3.8+ (recomendado 3.10/3.11).
- Conexión a Internet.

Dependencias Python (instalar en el virtualenv):

```powershell
python -m pip install --upgrade pip
pip install playwright requests
python -m playwright install
```

Notas:
- `python -m playwright install` descargará los navegadores necesarios para Playwright.
- Si vas a usar `venv`, crea y activa el entorno antes de instalar:

```powershell
python -m venv venv
# Permitir ejecución de scripts para el usuario (si PowerShell lo bloquea)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Activar el virtualenv
. .\venv\Scripts\Activate.ps1
```

**Configuración**

- Abre `download_ujap_materials.py` y revisa/ajusta las siguientes variables al inicio del archivo:
  - `USERNAME` y `PASSWORD` (no subas este archivo a repositorios públicos con las credenciales embebidas).
  - `DEST_ROOT` (ruta donde se guardarán las carpetas por curso).

Sugerencia de seguridad: en lugar de dejar las credenciales en el script, exporta variables de entorno y modifica el script para leer `os.environ.get("UJAP_USER")` y `os.environ.get("UJAP_PASS")`.

**Cómo ejecutar**

1. Abre PowerShell y ubícate en la carpeta del proyecto:

```powershell
cd "C:\Users\slgab\OneDrive\Desktop\Proyectos python\Scraping de Acropolis"
```

2. (Opcional) Crear y activar un `venv`:

```powershell
python -m venv venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
. .\venv\Scripts\Activate.ps1
```

3. Instalar dependencias (si aún no lo hiciste):

```powershell
pip install --upgrade pip
pip install playwright requests
python -m playwright install
```

4. Ejecutar el script:

```powershell
python download_ujap_materials.py
```

- El navegador Chromium se abrirá (el script usa Playwright en modo no headless por defecto para permitir ver lo que ocurre).
- El script intentará hacer login automáticamente (si los selectores coinciden). Si no, te dará tiempo para iniciar sesión manualmente.

**Salida**

- Por cada curso se crea una carpeta dentro de `DEST_ROOT` (por defecto `C:\Users\...\Universidad\9vo Semestre`).
- Archivos descargados se guardan en la carpeta del curso.
- Enlaces externos se guardan en `enlaces_y_videos.txt` dentro de la carpeta del curso.
- Referencias manuales (cuando no se detecta `pluginfile.php`) se guardan en `referencias_manuales.txt`.

**Posibles problemas y soluciones**

- PowerShell bloquea la activación del entorno o la ejecución de scripts: usa `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- Playwright no tiene navegadores instalados: ejecuta `python -m playwright install`.
- Selectores del sitio cambian (Moodle personalizado): revisa y ajusta los selectores en `download_ujap_materials.py` (inputs de login, enlaces de cursos, selectores de recursos).
- Problemas con cookies / autenticación: el script copia las cookies del contexto Playwright a una sesión `requests` para descargar archivos; si el servidor aplica protecciones adicionales puede ser necesario descargar vía Playwright (abrir el recurso y guardar la respuesta de la descarga) o añadir cabeceras adicionales.

**Mejoras recomendadas**

- Mover credenciales a variables de entorno o archivo `.env`.
- Añadir manejo de reintentos y logs detallados.
- Añadir opción `--headless` o argumento para ejecutar sin mostrar el navegador.
- Controlar mejor los tiempos de espera y excepciones específicas de Playwright.

**Licencia y uso**

- Este script es para uso personal y educativo. Respeta las políticas de uso del sitio y los derechos de autor de los materiales descargados.

Si quieres, puedo:
- Añadir la lectura de credenciales desde variables de entorno.
- Añadir un `requirements.txt` o `pyproject.toml`.
- Añadir un flag `--headless` y argumentos CLI.

---
Archivo principal: `download_ujap_materials.py`
