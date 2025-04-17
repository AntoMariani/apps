from pathlib import Path

# Ruta base de tu proyecto
ROOT = Path("C:/Users/antom/Documentos/Repositorios/apps/")

def insertar_gitkeep_en_todas():
    for carpeta in ROOT.rglob("*"):
        if carpeta.is_dir():
            gitkeep = carpeta / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                print(f"📝 .gitkeep creado en: {carpeta}")

if __name__ == "__main__":
    insertar_gitkeep_en_todas()
