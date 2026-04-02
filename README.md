# ledeclicmental — Instagram Automation Bot

Automatisation complète du compte Instagram [@ledeclicmental](https://instagram.com/ledeclicmental) — compte de motivation bilingue FR/EN.

## Fonctionnement

Le bot publie **3 posts par jour** aux horaires optimaux pour l'audience francophone :

| Slot | Heure (Paris) | Thème |
|------|--------------|-------|
| Matin | 07h00 | Énergie, ambition du réveil |
| Midi | 12h30 | Focus, relance de l'élan |
| Soir | 19h00 | Réflexion, recharge |

### Pipeline pour chaque post

```
Google Trends (thème du jour)
  → Claude API (citation + légende bilingue FR/EN)
  → PIL/Pillow (image 1080×1080 avec logo)
  → instagrapi (publication Instagram)
  → Historique local (déduplication)
```

---

## Installation

### 1. Prérequis

- Python 3.10+
- Un compte Instagram actif (@ledeclicmental)
- Une clé API Anthropic

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Éditer .env avec vos identifiants
nano .env
```

Variables obligatoires dans `.env` :
```
INSTAGRAM_USERNAME=ledeclicmental
INSTAGRAM_PASSWORD=votre_mot_de_passe
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Ajouter votre logo

Déposez votre logo dans `assets/logo/ledeclicmental_logo.png`
- Format : PNG avec transparence (RGBA)
- Taille recommandée : 300×300 px minimum

### 5. Générer les templates de fond

```bash
python scripts/build_templates.py
```

---

## Utilisation

### Démarrer le bot (mode production)

```bash
python scripts/run.py
```

Le bot tourne en continu et publie aux heures configurées.

### Tester sans publier sur Instagram

```bash
# Test de rendu d'image (aucun appel API)
python scripts/test_image.py --slot morning

# Test de génération de contenu (appel Claude API, pas de publication)
python scripts/test_content.py --slot evening

# Mode dry-run complet (pipeline entier, sans publication)
DRY_RUN=true python scripts/run.py --now morning
```

### Publier un post immédiatement

```bash
python scripts/run.py --now morning    # ou midday, evening
```

---

## Structure du projet

```
ledeclicmental/
├── assets/
│   ├── fonts/          # Polices (Montserrat-Bold.ttf, etc.)
│   ├── logo/           # ledeclicmental_logo.png  ← déposer ici
│   └── templates/      # Fonds générés par build_templates.py
│
├── data/
│   ├── generated/      # Images temporaires (auto-nettoyage 7j)
│   ├── logs/           # app.log, error.log
│   ├── session/        # Session Instagram (ne pas commiter)
│   └── post_history.json
│
├── ledeclicmental/
│   ├── config.py           # Configuration centralisée
│   ├── scheduler.py        # Orchestrateur APScheduler
│   ├── topics/trending.py  # Google Trends + fallback
│   ├── content/
│   │   ├── generator.py    # Claude API → contenu bilingue
│   │   ├── hashtags.py     # 30 hashtags FR+EN par post
│   │   └── audio.py        # Recommandations musicales
│   ├── image/renderer.py   # Rendu PIL 1080×1080
│   └── instagram/poster.py # Publication via instagrapi
│
├── scripts/
│   ├── run.py              # Point d'entrée principal
│   ├── test_image.py       # Test visuel du rendu
│   ├── test_content.py     # Test génération Claude
│   └── build_templates.py  # Génère les fonds
│
└── tests/                  # Tests unitaires
```

---

## Personnalisation

### Horaires de publication

Dans `.env` :
```
POST_TIMES=07:00,12:30,19:00
TIMEZONE=Europe/Paris
```

### Thèmes / topics

Le fichier `ledeclicmental/topics/trending.py` contient une liste de 40 thèmes evergreen en `_CURATED`. Vous pouvez en ajouter/modifier.

### Hashtags

Le fichier `ledeclicmental/content/hashtags.py` contient :
- `_BRAND_TAGS` : vos hashtags de marque (toujours inclus)
- `_TOPIC_TAGS` : hashtags spécifiques par thème
- `_POOL` : pool de 200+ hashtags rotatifs bilingues

### Audio / musique

Le fichier `ledeclicmental/content/audio.py` contient `_LIBRARY` — la liste des morceaux recommandés. Ajoutez vos favoris en suivant le format `AudioTrack`.

---

## Sécurité

- La session Instagram est sauvegardée dans `data/session/` (gitignore)
- Le fichier `.env` n'est jamais commité
- Le bot publie max 3 fois/jour (bien en-dessous des limites Instagram)
- Délai aléatoire 30–90s avant chaque publication (comportement humain)
- Mode `DRY_RUN=true` pour tester sans risque

---

## Polices recommandées (optionnel)

Pour un meilleur rendu visuel, téléchargez et placez dans `assets/fonts/` :
- `Montserrat-Bold.ttf` — [Google Fonts](https://fonts.google.com/specimen/Montserrat)
- `Raleway-Italic.ttf` — [Google Fonts](https://fonts.google.com/specimen/Raleway)

Sans ces polices, le bot utilise les polices système disponibles.
