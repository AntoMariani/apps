import os
import subprocess
from markdown2 import markdown
from weasyprint import HTML
from bs4 import BeautifulSoup

def reemplazar_titulos_con_estilos_inline(html):
    soup = BeautifulSoup(html, 'html.parser')

    estilos_inline = {
        "h1": "color:#1e1e1e;font-size:24px;border-bottom:2px solid #ccc;padding-bottom:0.2em;margin-top:1.5em;margin-bottom:0.5em;font-weight:bold;",
        "h2": "color:#1e1e1e;font-size:20px;border-bottom:1px solid #ccc;padding-bottom:0.2em;margin-top:1.2em;margin-bottom:0.5em;font-weight:bold;",
        "h3": "color:#1e1e1e;font-size:17px;margin-top:1em;margin-bottom:0.3em;font-weight:bold;"
    }

    for tag_name, estilo in estilos_inline.items():
        for tag in soup.find_all(tag_name):
            tag['style'] = estilo

    return str(soup)

def convertir_html_a_docx(path_html, path_salida_docx):
    try:
        subprocess.run(["pandoc", path_html, "-o", path_salida_docx], check=True)
        print(f"✅ DOCX generado desde HTML: {path_salida_docx}")
    except subprocess.CalledProcessError:
        print("❌ Error al ejecutar Pandoc desde HTML.")

def convertir_markdown(path_md, salida="html"):
    if not os.path.isfile(path_md):
        print(f"❌ El archivo no existe: {path_md}")
        return

    with open(path_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    html = markdown(md_text, extras=["tables", "fenced-code-blocks", "strike", "task_list"])
    html = reemplazar_titulos_con_estilos_inline(html)

    html_full = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
    @page {{
        margin: 1cm;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        font-size: 14px;
        line-height: 1.6;
        color: #1e1e1e;
        margin: 1cm;
    }}
    p {{ margin-bottom: 1em; }}
    ul, ol {{ margin: 1em 0 1em 2em; }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 1.2em 0;
    }}
    th, td {{
        border: 1px solid #ccc;
        padding: 6px 12px;
        text-align: left;
    }}
    blockquote {{
        border-left: 4px solid #ccc;
        margin: 1em 0;
        padding-left: 1em;
        color: #555;
        font-style: italic;
    }}
    hr {{
        border: none;
        border-top: 1px solid #ccc;
        margin: 2em 0;
    }}
    code, pre {{
        font-family: Consolas, 'Courier New', monospace;
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 4px;
    }}
    pre code {{
        display: block;
        padding: 12px;
        overflow-x: auto;
    }}
</style>
</head>
<body>
{html}
</body>
</html>
"""

    nombre_base = os.path.splitext(path_md)[0]
    path_html = f"{nombre_base}_vscode.html"

    if salida in ["html", "todas", "docx"]:
        with open(path_html, "w", encoding="utf-8") as f:
            f.write(html_full)
        print(f"✅ HTML generado en: {path_html}")

    if salida in ["pdf", "todas"]:
        path_pdf = f"{nombre_base}_vscode.pdf"
        HTML(string=html_full).write_pdf(path_pdf)
        print(f"✅ PDF generado en: {path_pdf}")

    if salida in ["docx", "todas"]:
        path_docx = f"{nombre_base}.docx"
        convertir_html_a_docx(path_html, path_docx)

# --- INTERFAZ ---

print("📄 Conversor de Markdown al estilo VSCode")
ruta = input("📅 Ingresá la ruta del archivo .md: ").strip()

print("\n¿Qué formato querés generar?")
print("1. HTML")
print("2. PDF")
print("3. DOCX (sin títulos azules 😎)")
print("4. Todas (HTML + PDF + DOCX)")
opcion = input("Elegí una opción (1/2/3/4): ").strip()

formato = {
    "1": "html",
    "2": "pdf",
    "3": "docx",
    "4": "todas"
}.get(opcion, None)

if formato:
    convertir_markdown(ruta, formato)
else:
    print("❌ Opción no válida.")
