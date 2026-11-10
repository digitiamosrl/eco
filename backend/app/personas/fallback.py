"""Biografia da template, usata quando il modello fallisce anche dopo il retry.

Usa solo gli attributi campionati: non inventa nulla e non salta la persona, così le quote tornano.
"""


def fallback_profile(
    role: str, sector: str, company_size: str, region: str, ai_attitude: str, linkedin_use: str
) -> str:
    return (
        f"{role}, nel settore {sector}, in una {company_size} in {region}. "
        f"Rapporto con l'intelligenza artificiale, {ai_attitude}. "
        f"Su LinkedIn, {linkedin_use}."
    )
