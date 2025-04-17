import os
from markdown2 import markdown
from weasyprint import HTML

def convertir_markdown(path_md, salida="html"):
    if not os.path.isfile(path_md):
        print(f"❌ El archivo no existe: {path_md}")
        return

    with open(path_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    html = markdown(md_text, extras=["tables", "fenced-code-blocks", "strike", "task_list"])

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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe WPC', 'Segoe UI',
                         system-ui, 'Ubuntu', 'Droid Sans', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #1e1e1e;
            margin: 1cm;
        }}
        h1 {{ font-size: 1.8em; border-bottom: 2px solid #ddd; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #ddd; }}
        h3 {{ font-size: 1.2em; }}
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

    if salida in ["html", "ambas"]:
        path_html = f"{nombre_base}_vscode.html"
        with open(path_html, "w", encoding="utf-8") as f:
            f.write(html_full)
        print(f"✅ HTML generado en: {path_html}")

    if salida in ["pdf", "ambas"]:
        path_pdf = f"{nombre_base}_vscode.pdf"
        HTML(string=html_full).write_pdf(path_pdf)
        print(f"✅ PDF generado en: {path_pdf}")

# --- INTERFAZ INTERACTIVA ---

print("📄 Conversor de Markdown al estilo VSCode")
ruta = input("📥 Ingresá la ruta del archivo .md: ").strip()

print("\n¿Qué formato querés generar?")
print("1. HTML")
print("2. PDF")
print("3. Ambas")
opcion = input("Elegí una opción (1/2/3): ").strip()

formato = {
    "1": "html",
    "2": "pdf",
    "3": "ambas"
}.get(opcion, None)

if formato:
    convertir_markdown(ruta, formato)
else:
    print("❌ Opción no válida.")
