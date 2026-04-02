"""
Optimise le CV en fonction d'une offre de stage en utilisant Claude API.
"""
import json
import anthropic

SYSTEM_PROMPT = """Tu es un expert en recrutement spécialisé dans les profils ingénieurs en microélectronique et IA embarquée.
Tu aides à optimiser des CVs pour passer les filtres ATS (Applicant Tracking Systems) et séduire les recruteurs.

Règles absolues pour la génération du CV :
1. Le titre du poste de l'offre doit figurer en PREMIER, en gras, comme intitulé principal du CV.
2. Ne PAS inclure de photo, ni la nationalité du candidat.
3. Nom et prénom apparaissent EN BAS du CV, dans les informations personnelles.
4. Ordre des sections : TITRE DU POSTE → Informations personnelles → Compétences → Formation → Projets → Expériences → Langues → Centres d'intérêt → Nom/Prénom (tout en bas).
5. Pour la localisation dans les infos personnelles : utiliser le département/région le plus proche du lieu du poste (pas l'adresse exacte).
6. Compétences : mettre en AVANT les compétences mentionnées dans l'offre. Retirer les compétences non pertinentes.
7. Rester factuel : ne PAS inventer de compétences ou d'expériences que le candidat n'a pas.
8. Adapter le vocabulaire et les mots-clés à l'offre pour l'ATS.
9. Retourner un JSON structuré (voir format ci-dessous)."""


def optimize_cv(cv_data: dict, job: dict, client: anthropic.Anthropic) -> dict:
    """
    Utilise Claude pour adapter le CV à une offre de stage.

    Args:
        cv_data: Données brutes du CV (cv_data.json)
        job: Offre de stage (titre, entreprise, localisation, description)
        client: Client Anthropic

    Returns:
        dict avec les sections du CV optimisé
    """
    prompt = f"""Voici le CV brut du candidat :
{json.dumps(cv_data, ensure_ascii=False, indent=2)}

Voici l'offre de stage :
- Titre du poste : {job['title']}
- Entreprise : {job['company']}
- Lieu : {job['location']}
- Source : {job['source']}
- Description complète :
{job['description']}

Adapte le CV pour cette offre en respectant STRICTEMENT les règles données.

Retourne UNIQUEMENT un JSON valide avec cette structure exacte :
{{
  "job_title_header": "le titre exact du poste à mettre en gros en haut",
  "personal_info": {{
    "email": "...",
    "phone": "...",
    "location": "département/région proche du poste",
    "linkedin": "...",
    "github": "..."
  }},
  "skills": {{
    "priority_skills": ["compétences clés en lien direct avec l'offre"],
    "additional_skills": ["autres compétences pertinentes à garder"]
  }},
  "education": [
    {{
      "degree": "...",
      "school": "...",
      "year": "...",
      "mention": "..."
    }}
  ],
  "projects": [
    {{
      "title": "...",
      "description": "description adaptée aux mots-clés de l'offre",
      "technologies": ["..."],
      "year": "..."
    }}
  ],
  "experience": [
    {{
      "title": "...",
      "company": "...",
      "location": "...",
      "period": "...",
      "description": "..."
    }}
  ],
  "languages": [
    {{"language": "...", "level": "..."}}
  ],
  "interests": ["..."],
  "full_name": "Prénom NOM"
}}"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
    )

    raw = response.content[0].text.strip()

    # Extraire le JSON si entouré de balises markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)
