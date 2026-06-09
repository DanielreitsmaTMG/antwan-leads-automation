"""
Beoordeelt de relevantie van een lead voor Antwan Tuinprojecten via Claude Haiku.
Geeft een score van 1 t/m 5 terug:
  5 = perfecte match (hotel, vakantiepark, ziekenhuis met grote buitenruimte)
  4 = goede match (conferentiecentrum, sportpark, woonzorgcentrum)
  3 = redelijke match (middelbare school, begraafplaats)
  2 = twijfelachtig (klein bedrijf, onbekende categorie)
  1 = niet relevant (apotheek, reisbureau, woonwinkel etc.)
"""
import json
import os
import sys

import anthropic

sys.path.insert(0, os.path.dirname(__file__))

MODEL = "claude-haiku-4-5-20251001"

SYSTEEM_PROMPT = """Je beoordeelt leads voor Antwan Tuinprojecten, een bedrijf dat zakelijk \
groenonderhoud verzorgt van bedrijfstuinen en openbare ruimtes (hotels, vakantieparken, \
campings, ziekenhuizen, verpleeghuizen, sportparken, conferentiecentra, golfbanen, \
bedrijventerreinen, hogescholen, landgoederen, zwembaden, VVE's).

Geef een score van 1-5 op basis van hoe relevant deze lead is als potentiële klant:
5 = perfecte match: grote buitenruimte, professioneel beheer nodig (hotel, ziekenhuis, vakantiepark, golfbaan, landgoed)
4 = goede match: relevante organisatie met waarschijnlijk groen (sportpark, conferentiecentrum, woonzorgcentrum, camping)
3 = redelijke match: mogelijk relevant, kleinere schaal (school, begraafplaats, recreatiecentrum)
2 = twijfelachtig: onduidelijke relevantie of kleine locatie
1 = niet relevant: geen buitenruimte te verwachten (apotheek, reisbureau, woonwinkel, zorgpraktijk)

Antwoord ALLEEN met een JSON-object: {"score": <1-5>, "reden": "<één zin waarom>"}"""


def score_lead(lead: dict) -> tuple:
    """Geeft (score: int, reden: str) terug. Valt bij fout terug op score 3."""
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        prompt = (
            f"Bedrijfsnaam: {lead.get('company_name')}\n"
            f"Categorie: {lead.get('category') or 'onbekend'}\n"
            f"Adres: {lead.get('address') or 'onbekend'}\n"
            f"Website: {lead.get('website') or 'onbekend'}"
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            system=SYSTEEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        data = json.loads(text)
        score = max(1, min(5, int(data["score"])))
        reden = data.get("reden", "")
        return score, reden
    except Exception as exc:
        print(f"Score-berekening mislukt voor '{lead.get('company_name')}': {exc}")
        return 3, "Automatische score niet beschikbaar"


def sterren(score: int) -> str:
    return "⭐" * score + "☆" * (5 - score)
