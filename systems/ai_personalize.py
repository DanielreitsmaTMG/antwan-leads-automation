"""
Generates a personalized sales outreach message per lead using Claude Haiku.
Falls back to the static template (generate_email.build_message) if the API
call fails for any reason — a lead must always end up with a usable message.
"""
import os
import sys

import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from generate_email import build_message as build_template_message  # noqa: E402

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """Je schrijft korte, persoonlijke Nederlandse sales-outreach e-mails namens \
Antwan Tuinprojecten (info@antwan.nl, 010-5011150, Nijverheidsweg 29, Rhoon). \
Antwan verzorgt tuin- en groenonderhoud van bedrijfstuinen en openbare ruimtes \
(hotels, VVE's, campings, bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden). \
Tone-of-voice: warm, professioneel, behulpzaam — "ontzorgen met behoud van inspraak", \
nooit opdringerig of overdreven salesy.

Schrijf een kort bericht (max. ~120 woorden) dat:
- de lead persoonlijk aanspreekt (naam indien gegeven, anders neutraal "Beste")
- kort en concreet verwijst naar het type bedrijf/locatie (categorie/naam) zodat het niet generiek aanvoelt
- een vrijblijvend voorstel doet voor groenonderhoud van hun bedrijfsterrein/openbare ruimte
- afsluit met een uitnodiging voor een kort kennismakingsgesprek
- ondertekend wordt met "Antwan Tuinprojecten" + telefoon + e-mail

Antwoord ALLEEN met een JSON-object met de keys "subject" en "body" (de body inclusief \
aanhef en ondertekening, met newlines als \\n). Geen uitleg, geen markdown, alleen JSON."""


def generate_message(lead: dict) -> dict:
    """Returns {subject, body}. Uses Claude Haiku; falls back to template on any failure."""
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        user_prompt = (
            f"Bedrijfsnaam: {lead.get('company_name')}\n"
            f"Categorie: {lead.get('category') or 'onbekend'}\n"
            f"Plaats/adres: {lead.get('address') or lead.get('city') or 'onbekend'}\n"
            f"Contactpersoon: {lead.get('contact_name') or 'onbekend'}\n"
            f"Website: {lead.get('website') or 'onbekend'}"
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()

        import json
        # Strip potential markdown code fences before parsing.
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        data = json.loads(text)
        if data.get("subject") and data.get("body"):
            return {"subject": data["subject"], "body": data["body"]}
    except Exception as exc:
        print(f"AI personalization failed for '{lead.get('company_name')}', using template fallback: {exc}")

    fallback = build_template_message(lead)
    return {"subject": fallback["subject"], "body": fallback["body"]}
