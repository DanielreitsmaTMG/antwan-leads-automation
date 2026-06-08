"""Builds a personalized sales outreach message + mailto: link for a lead."""
import urllib.parse

SENDER_NAME = "Antwan Tuinprojecten"
SENDER_EMAIL = "info@antwan.nl"
SENDER_PHONE = "010-5011150"

SUBJECT_TEMPLATE = "Onderhoud van het groen bij {company_name} – vrijblijvend voorstel"

BODY_TEMPLATE = """Beste{contact_part},

Bij het bekijken van {company_name} viel ons op dat groen en buitenruimte bijdragen aan hoe bezoekers en gebruikers de locatie ervaren. Bij Antwan Tuinprojecten ontzorgen we organisaties zoals de uwe volledig op het gebied van tuin- en groenonderhoud van bedrijfsterreinen en openbare ruimtes – met behoud van inspraak over hoe het eruit komt te zien.

Graag denken we vrijblijvend met u mee over een onderhoudsplan dat past bij {company_name}: van regulier groenonderhoud tot seizoensgebonden aanpak en aanleg.

Heeft u interesse in een kort kennismakingsgesprek?

Met vriendelijke groet,
{sender_name}
{sender_phone} | {sender_email}
"""


def build_message(lead: dict) -> dict:
    """Returns dict with subject, body, and a ready-to-use mailto: URL for the lead."""
    contact_name = (lead.get("contact_name") or "").strip()
    contact_part = f" {contact_name}" if contact_name else ""

    subject = SUBJECT_TEMPLATE.format(company_name=lead["company_name"])
    body = BODY_TEMPLATE.format(
        contact_part=contact_part,
        company_name=lead["company_name"],
        sender_name=SENDER_NAME,
        sender_phone=SENDER_PHONE,
        sender_email=SENDER_EMAIL,
    )

    to_addr = lead.get("email") or ""
    query = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    mailto_url = f"mailto:{to_addr}?{query}"

    return {"subject": subject, "body": body, "mailto_url": mailto_url}
