"""
Génère une lettre de motivation personnalisée avec Claude API.
"""
import anthropic

SYSTEM_PROMPT = """Tu es un expert en rédaction de lettres de motivation pour des ingénieurs en microélectronique et IA embarquée.
Tu rédiges des lettres percutantes, sincères et adaptées à chaque offre.

Règles :
- Longueur : 3 à 4 paragraphes, une page maximum.
- Ton : professionnel mais dynamique, pas pompeux.
- Personnalisation forte : mentionner explicitement l'entreprise et le poste.
- Mettre en valeur les projets et compétences du candidat EN LIEN avec l'offre.
- Pas de formules creuses ("je suis très motivé par...") sans justification concrète.
- Terminer par une formule de politesse professionnelle standard.
- Rédiger en français."""


def generate_cover_letter(
    cv_data: dict,
    optimized_cv: dict,
    job: dict,
    client: anthropic.Anthropic,
) -> str:
    """
    Génère une lettre de motivation pour une offre donnée.

    Args:
        cv_data: Données brutes du CV
        optimized_cv: CV optimisé (sortie de optimize_cv)
        job: Offre de stage
        client: Client Anthropic

    Returns:
        Texte de la lettre de motivation
    """
    full_name = optimized_cv.get("full_name", "Prénom NOM")
    email = optimized_cv.get("personal_info", {}).get("email", "")
    phone = optimized_cv.get("personal_info", {}).get("phone", "")
    location = optimized_cv.get("personal_info", {}).get("location", "France")

    priority_skills = optimized_cv.get("skills", {}).get("priority_skills", [])
    projects = optimized_cv.get("projects", [])

    projects_summary = "\n".join(
        f"- {p['title']} : {p['description']}" for p in projects[:3]
    )
    skills_summary = ", ".join(priority_skills[:8])

    prompt = f"""Candidat : {full_name}
Localisation : {location}
Email : {email} | Tél : {phone}

Formation : Cycle ingénieur Microélectronique – Polytech Marseille (5ème année)
           Prépa CPGE PT – Lille

Compétences prioritaires pour ce poste : {skills_summary}

Projets marquants :
{projects_summary}

Offre visée :
- Titre : {job['title']}
- Entreprise : {job['company']}
- Lieu : {job['location']}
- Description :
{job['description']}

Rédige une lettre de motivation complète et percutante pour ce stage.
Commence directement par la date et le lieu (utilise {location}), puis la lettre.
Inclus les coordonnées du candidat en haut à gauche et les coordonnées de l'entreprise en haut à droite.
Ne dépasse pas une page (environ 350 mots)."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
    )

    return response.content[0].text.strip()
