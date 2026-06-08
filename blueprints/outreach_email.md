# Blueprint: Sales-outreach e-mail genereren

## Doel
Voor elke lead automatisch een persoonlijk, AI-gegenereerd sales-bericht opstellen
gericht op onderhoud van de bedrijfstuin/openbare ruimte, opslaan in de database,
en de gebruiker met één klik naar zijn eigen mailclient sturen (`mailto:`) om te
versturen — geen automatische verzending, de mens blijft in de lead.

## Benodigde input
- Een lead-record (dict) met minimaal: `company_name`, optioneel `category`,
  `address`/`city`, `contact_name`, `website`, `email`.
- `ANTHROPIC_API_KEY` (env var / GitHub secret / Streamlit secret)

## Systems

### 1. `systems/ai_personalize.py` → `generate_message(lead)`
Genereert per lead een uniek bericht met **Claude Haiku 4.5**, op basis van
bedrijfsnaam, categorie, locatie, contactpersoon en website — zodat het bericht
niet generiek aanvoelt maar aansluit op het type organisatie. Geeft `{subject, body}`
terug. **Bij elke fout (API down, parse-fout, ontbrekende key) valt het systeem
automatisch terug op de statische template** (`generate_email.build_message`),
zodat een lead nooit zonder bruikbaar bericht komt te zitten.

### 2. `systems/generate_email.py`
- `build_message(lead)`: statische Nederlandstalige template (fallback) met
  Antwan's tone-of-voice ("ontzorgen met behoud van inspraak")
- `build_mailto(to_addr, subject, body)`: bouwt een kant-en-klare `mailto:` link
  met gecodeerde subject/body uit een (AI- of template-)bericht

## Wanneer wordt het bericht gegenereerd?
**Tijdens de dagelijkse scrape** (`systems/scrape_leads.py`): direct na het
invoegen van een nieuwe lead wordt `generate_message()` aangeroepen en het
resultaat opgeslagen in `leads.email_subject` / `leads.email_body`. Dit zorgt
voor een snel ladend dashboard (geen AI-call per paginaweergave) en voorkomt
herhaalde kosten. In het dashboard kan de gebruiker per lead alsnog op
"🔄 Nieuw AI-bericht genereren" klikken om een nieuwe versie te laten maken.

## Verwachte output
Het dashboard toont het opgeslagen AI-bericht in een bewerkbaar tekstveld en een
knop "✉️ Open in mail-app" die de mailto-link opent in de standaard mailclient van
de gebruiker, met afzendergegevens van Antwan Tuinprojecten (info@antwan.nl,
010-5011150) al ingevuld in de ondertekening.

## Edge cases
- Geen e-mailadres bekend → knop is uitgeschakeld en toont een waarschuwing; de
  gebruiker kan dan handmatig bellen via het getoonde telefoonnummer.
- Geen contactpersoon bekend → aanhef valt automatisch terug op "Beste," zonder naam.
- AI-call faalt → automatische fallback naar de statische template (zie boven);
  wordt gelogd in de scrape-output zodat het zichtbaar is in de GitHub Actions-run.
- Oudere leads zonder opgeslagen bericht (vóór deze functionaliteit bestond) →
  dashboard genereert dan live een template-bericht als fallback.

## Geleerde lessen
*(nog leeg — vul aan met feedback over welke bewoordingen het beste converteren,
en eventuele kwaliteitsverschillen tussen Haiku en Sonnet als je ooit wilt switchen)*
