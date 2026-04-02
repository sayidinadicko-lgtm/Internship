# CV Optimizer – Stages Microélectronique / IA Embarquée

Automatise la recherche d'offres de stage et l'optimisation du CV + lettre de motivation pour chaque offre.

## Fonctionnement

1. **Scraping** : récupère les offres de stage sur Indeed France et HelloWork
2. **Optimisation CV** : adapte le CV aux mots-clés de chaque offre (ATS-friendly) via Claude API
3. **Lettre de motivation** : génère une lettre personnalisée pour chaque offre
4. **Export** : génère un `.docx` pour le CV et un `.docx` pour la lettre de motivation

### Structure du CV généré

```
[TITRE DU POSTE] ← en gros, centré, gras (ATS)
─────────────────────────────────────────────
Informations personnelles (email, téléphone, localisation, LinkedIn, GitHub)
Compétences (priorité aux compétences de l'offre)
Formation (Bac → CPGE PT → Polytech Marseille)
Projets
Expériences professionnelles
Langues
Centres d'intérêt
                                    Prénom NOM ← tout en bas
```

> **Note :** Pas de photo, pas de nationalité dans le CV généré.

## Installation

```bash
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine :
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Configuration du CV

Remplir `cv_data.json` avec tes informations personnelles, compétences, projets, formation, etc.

## Utilisation

```bash
# Toutes les sources (Indeed + HelloWork), 10 offres max par source
python main.py

# Seulement Indeed, 5 offres
python main.py --source indeed --max 5

# Seulement HelloWork, requête personnalisée
python main.py --source hellowork --query "stage FPGA intelligence artificielle embarquée" --max 8

# Dossier de sortie personnalisé
python main.py --output mes_candidatures/
```

### Arguments disponibles

| Argument | Défaut | Description |
|---|---|---|
| `--source` | `all` | Source : `indeed`, `hellowork`, ou `all` |
| `--max` | `10` | Nombre max d'offres par source |
| `--query` | `"stage microelectronique IA embarquée..."` | Requête de recherche |
| `--location` | `France` | Localisation pour la recherche |
| `--cv` | `cv_data.json` | Chemin vers les données du CV |
| `--output` | `output/` | Dossier de sortie |

## Structure du projet

```
Internship/
├── main.py                  # Point d'entrée
├── cv_data.json             # Données personnelles du CV (à remplir)
├── requirements.txt
├── .env                     # Clé API (non commitée)
├── scrapers/
│   ├── indeed.py            # Scraper Indeed France
│   └── hellowork.py         # Scraper HelloWork
├── cv_optimizer/
│   ├── optimizer.py         # Optimisation CV via Claude
│   ├── cover_letter.py      # Génération lettre de motivation
│   └── docx_builder.py      # Export Word (.docx)
└── output/                  # CVs et LMs générés (non commités)
```
