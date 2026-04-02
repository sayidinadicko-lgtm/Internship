"""
Convertit un fichier .docx en .pdf via LibreOffice headless.
"""
import subprocess
import shutil
import os
from pathlib import Path


def docx_to_pdf(docx_path: str, output_dir: str = None) -> str:
    """
    Convertit un .docx en .pdf avec LibreOffice headless.

    Args:
        docx_path: Chemin vers le fichier .docx source
        output_dir: Dossier de destination (par défaut : même dossier que le .docx)

    Returns:
        Chemin du fichier .pdf généré

    Raises:
        FileNotFoundError: si LibreOffice n'est pas installé
        RuntimeError: si la conversion échoue
    """
    lo_bin = shutil.which("libreoffice") or shutil.which("soffice")
    if not lo_bin:
        raise FileNotFoundError(
            "LibreOffice introuvable. Installer avec : sudo apt install libreoffice"
        )

    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {docx_path}")

    out_dir = Path(output_dir).resolve() if output_dir else docx_path.parent

    result = subprocess.run(
        [
            lo_bin,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Échec de la conversion LibreOffice :\n{result.stderr}"
        )

    pdf_path = out_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF attendu mais introuvable : {pdf_path}")

    return str(pdf_path)
