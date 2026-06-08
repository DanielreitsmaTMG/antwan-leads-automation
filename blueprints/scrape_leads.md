# Blueprint: Dagelijks leads scrapen

## Doel
Elke dag automatisch ~10 nieuwe zakelijke leads verzamelen rond Rhoon (±25km) voor
Antwan Tuinprojecten: hotels, VVE's, campings, bedrijventerreinen, ziekenhuizen,
vakantieparken, zwembaden — inclusief contactpersoon en zo compleet mogelijke
contactgegevens (e-mail, telefoon, website).

## Benodigde input
- `APIFY_API_TOKEN` (env var / GitHub secret)
- `NEON_CONNECTION_STRING` (env var / GitHub secret)

## System
`systems/scrape_leads.py --limit 10`

Gebruikt de Apify-actor `compass/crawler-google-places` (Google Maps Scraper) met:
- Zoektermen: hotel, vakantiepark, camping, bedrijventerrein, ziekenhuis, zwembad,
  VVE vastgoedbeheer, kantorenpark
- Locatie: "Rhoon, Netherlands", straal 25km
- `scrapeContacts: true` zodat de actor de website van elk bedrijf bezoekt om
  e-mailadressen en (waar mogelijk) eigenaar/manager-namen op te halen

Resultaten worden gededupliceerd op `place_id` en weggeschreven naar de Neon-tabel
`leads` (zie `systems/schema.sql`). Alleen écht nieuwe bedrijven worden ingevoegd
(`ON CONFLICT (place_id) DO NOTHING`), dus na verloop van tijd kan het zijn dat een
run minder dan 10 nieuwe leads oplevert simpelweg omdat de regio "opraakt" — dat is
verwacht gedrag, geen bug.

## Verwachte output
Tot 10 nieuwe rijen in de `leads` tabel met status `new`.

## Scheduling
GitHub Actions cron-job: `.github/workflows/daily_scrape.yml`, draait dagelijks om
06:00 UTC (≈ 08:00 NL-tijd, let op zomer-/wintertijd-verschuiving).
Secrets `APIFY_API_TOKEN` en `NEON_CONNECTION_STRING` moeten in de GitHub repo
settings (Settings → Secrets and variables → Actions) worden gezet.

## Edge cases & geleerde lessen
- *(nog leeg — vul aan zodra de eerste runs gedraaid zijn: rate limits, actor-
  kosten per run, kwaliteit van e-mail/contactpersoon-data, eventuele behoefte om
  over te stappen op een combinatie van actors voor betere contactdekking)*

## Toekomstige verbetering (indien nodig)
Als de alles-in-1 actor te weinig e-mailadressen/contactpersonen oplevert: overstappen
op een combinatie van (1) Google Maps Scraper voor basisdata + (2) een dedicated
website/contact-scraper actor (bv. "Contact Info Scraper") die specifiek e-mails en
namen van verantwoordelijken van de bedrijfswebsite haalt.
