from playwright.sync_api import sync_playwright
import requests
from pathlib import Path
import re
import time
import urllib.parse

# ----------------- CONFIG -----------------
BASE_URL = "https://aulavirtual.ujap.edu.ve"
LOGIN_URL = f"{BASE_URL}/login/index.php"
MY_COURSES = f"{BASE_URL}/my/courses.php"
# Ruta de tu carpeta
DEST_ROOT = Path(r"C:\Users\slgab\OneDrive\Desktop\Universidad\9vo Semestre")
DEST_ROOT.mkdir(parents=True, exist_ok=True)

# CREDENCIALES
USERNAME = "gsandoval21"
PASSWORD = "Gs20mh21."
# ------------------------------------------

def clean_name(name: str) -> str:
    # Limpia caracteres inválidos para Windows
    invalid = r'<>:"/\|?*'
    for ch in invalid:
        name = name.replace(ch, "")
    return name.strip()[:120]

def requests_with_playwright_cookies(session: requests.Session, context_cookies):
    for c in context_cookies:
        cookie = {
            "domain": c.get("domain"),
            "name": c.get("name"),
            "value": c.get("value"),
            "path": c.get("path", "/")
        }
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])

def download_file(session: requests.Session, url: str, dest_path: Path):
    try:
        # Iniciamos la petición solo para ver las cabeceras (stream=True)
        resp = session.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        
        # Intentamos obtener el nombre real del archivo desde el servidor
        filename = None
        cd = resp.headers.get("content-disposition")
        if cd:
            m = re.search(r'filename\*?=([^;]+)', cd)
            if m:
                filename = m.group(1).strip().strip('"').strip("UTF-8''")
        
        if not filename:
            # Si no hay nombre en cabeceras, lo sacamos de la URL
            path = urllib.parse.urlsplit(url).path
            filename = Path(path).name
            if not filename or "." not in filename:
                filename = "documento_descargado.pdf"

        filename = clean_name(filename)
        target = dest_path / filename

        # Logica para no duplicar descargas
        if target.exists():
            # Comprobamos si el tamaño es mayor a 0 para asegurar que no sea un archivo corrupto
            if target.stat().st_size > 0:
                print(f"    El archivo ya existe: {target.name} (Saltando descarga)")
                resp.close() # Cerramos la conexión sin descargar el cuerpo
                return True
        
        # Si no existe, procedemos a descargar el contenido
        print(f"    Descargando: {filename}...")
        with open(target, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"    GUARDADO: {target.name}")
        return True

    except Exception as e:
        print(f"    Error descargando {url}: {e}")
        return False

def resolve_final_resource_url(page, url):
    try:
        try:
            # Intentamos ir a la URL. Si es descarga forzada, saltará excepción.
            page.goto(url, wait_until="domcontentloaded")
        except Exception as nav_err:
            if "Download is starting" in str(nav_err):
                print("   -> Detectada descarga directa (Force Download).")
                return url
            else:
                # Si es otro error, lo mostramos pero intentamos seguir
                print(f"   ! Nota de navegación: {nav_err}")
                return url

        time.sleep(1) 
        current_url = page.url

        # CASO 1: Redirección intermedia (urlworkaround)
        workaround_link = page.query_selector("div.urlworkaround a")
        if workaround_link:
            real_href = workaround_link.get_attribute("href")
            print(f"   -> Redirección detectada: {real_href}")
            return real_href

        # CASO 2: Enlaces automáticos a pluginfile
        if "pluginfile.php" in current_url:
            return current_url
            
        # CASO 3: Buscar enlace dentro del visualizador de recursos de Moodle
        if "mod/resource/view.php" in url:
            # A veces el enlace está en un div con clase resourcecontent
            resource_link = page.query_selector("div.resourcecontent a") 
            if resource_link:
                return resource_link.get_attribute("href")
            
            # O buscamos cualquier link a pluginfile
            all_links = page.query_selector_all("a")
            for l in all_links:
                href = l.get_attribute("href")
                if href and "pluginfile.php" in href:
                    return href

        return current_url

    except Exception as e:
        print(f"Error resolviendo URL: {e}")
        return url

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(" -> Abriendo página de login...")
        page.goto(LOGIN_URL)

        # Login
        try:
            page.fill("input[name='username']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            page.click("button[type='submit']")
        except:
            print(" ! Revisa los selectores de login o logueate manualmente.")
            time.sleep(15)

        page.wait_for_load_state("networkidle")
        
        print(" -> Navegando a Mis cursos...")
        page.goto(MY_COURSES)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Selector de cursos
        course_elements = page.query_selector_all("a[href*='/course/view.php?id=']")
        
        courses = []
        seen_ids = set()

        for a in course_elements:
            href = a.get_attribute("href")
            course_id_match = re.search(r'id=(\d+)', href)
            if not course_id_match: continue
            
            course_id = course_id_match.group(1)
            if course_id in seen_ids: continue
                
            raw_name = a.inner_text().strip()
            if not raw_name: continue

            course_name = raw_name
            if "-" in raw_name:
                parts = raw_name.split("-")
                if len(parts) > 1:
                    course_name = parts[-1].strip()
            
            course_name = clean_name(course_name)
            seen_ids.add(course_id)
            courses.append({"name": course_name, "url": href})

        print(f" -> Cursos detectados: {len(courses)}")

        session = requests.Session()
        requests_with_playwright_cookies(session, context.cookies())
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        for idx, course in enumerate(courses, start=1):
            course_name = course["name"]
            course_url = course["url"]
            course_folder = DEST_ROOT / course_name
            course_folder.mkdir(parents=True, exist_ok=True)

            print(f"\n{idx}. Curso: {course_name}")
            
            page.goto(course_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

            all_anchors = page.query_selector_all("a")
            
            downloadable = []
            external_links = []

            for a in all_anchors:
                href = a.get_attribute("href")
                if not href: continue

                full_url = urllib.parse.urljoin(page.url, href)
                text = (a.inner_text() or "").strip()
                if not text: continue

                if "/mod/resource/view.php" in full_url:
                    downloadable.append((text, full_url))
                elif "/mod/folder/view.php" in full_url:
                    external_links.append((f"[CARPETA] {text}", full_url))
                elif "/mod/url/view.php" in full_url:
                    external_links.append((text, full_url))

            downloadable = list(dict.fromkeys(downloadable))
            external_links = list(dict.fromkeys(external_links))

            print(f"   Recursos encontrados: {len(downloadable)} archivos, {len(external_links)} enlaces.")

            # 1. Enlaces (Guardamos solo si no existe la entrada en el txt para evitar spam, o sobrescribimos)
            if external_links:
                links_file = course_folder / "enlaces_y_videos.txt"
                # Leemos lo que ya existe para no repetir (opcional, básico)
                existing_content = ""
                if links_file.exists():
                    existing_content = links_file.read_text(encoding="utf-8")
                
                with open(links_file, "a", encoding="utf-8") as f:
                    # Escribimos cabecera solo si es nuevo día o archivo
                    if "Escaneo" not in existing_content:
                         f.write(f"--- Escaneo Inicial ---\n")

                    for title, url in external_links:
                        # Si el titulo ya está en el archivo, lo saltamos (básico)
                        if title in existing_content:
                            continue

                        real_url = url
                        if "/mod/url/view.php" in url:
                             real_url = resolve_final_resource_url(page, url)
                             page.goto(course_url) 
                             page.wait_for_load_state("domcontentloaded")
                        
                        f.write(f"{title} | {real_url}\n")
                        print(f"    Enlace nuevo guardado: {title}")

            # 2. Descargas
            for title, url in downloadable:
                print(f"   Procesando: {title}...")
                final_url = resolve_final_resource_url(page, url)
                
                if "pluginfile.php" in final_url:
                    download_file(session, final_url, course_folder)
                else:
                    # Referencias manuales
                    ref_file = course_folder / "referencias_manuales.txt"
                    if not ref_file.exists() or title not in ref_file.read_text(encoding="utf-8"):
                        print(f"    Referencia manual guardada.")
                        with open(ref_file, "a", encoding="utf-8") as f:
                            f.write(f"{title} | {final_url}\n")
                
                page.goto(course_url)
                page.wait_for_load_state("domcontentloaded")

        print("\n¡Proceso finalizado con éxito!")
        browser.close()

if __name__ == "__main__":
    run()