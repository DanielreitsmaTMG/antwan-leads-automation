# Blueprint: Leads scrapen

## Doel
Periodiek (2x per week) automatisch ~10 nieuwe zakelijke leads verzamelen binnen
~40km rond Rhoon voor Antwan Tuinprojecten: hotels, VVE's, campings,
bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden, etc. — inclusief
contactpersoon en zo compleet mogelijke contactgegevens (e-mail, telefoon, website).

## Benodigde input
- `APIFY_API_TOKEN` (env var / GitHub secret)
- `NEON_CONNECTION_STRING` (env var / GitHub secret)

## System
`systems/scrape_leads.py --limit 10`

Gebruikt de Apify-actor `compass/crawler-google-places` (Google Maps Scraper) met:
- Zoektermen (24 categorieën, totaal): hotel, vakantiepark, bungalowpark, camping,
  recreatiecentrum, pretpark, ziekenhuis, verpleeghuis, verzorgingshuis,
  woonzorgcentrum, zwembad, sportpark, sportcomplex, golfbaan, conferentiecentrum,
  congrescentrum, bedrijventerrein, kantorenpark, landgoed, begraafplaats,
  middelbare school, hogeschool, universiteit, VVE vastgoedbeheer
- Locatie: "Rotterdam, Netherlands" — dekt automatisch ~40km rond Rhoon
  (Rhoon ligt op 5km van Rotterdam; Rotterdam-regio beslaat het volledige doelgebied)
- `scrapeContacts: true` zodat de actor de website van elk bedrijf bezoekt om
  e-mailadressen en (waar mogelijk) eigenaar/manager-namen op te halen
- Eerdere fout opgelost: `SEARCH_RADIUS_M` werd niet meegegeven aan de actor waardoor
  alleen de gemeente Rhoon (~16 km²) werd gescand. Nu opgelost via grotere locationQuery.

## Kostenbeheersing (belangrijk!)
Apify rekent kosten af op basis van compute-units. `scrapeContacts: true` is de
grootste kostenpost, omdat de actor voor élke gevonden plek de website bezoekt.
Met 24 zoektermen in één run liep het Apify gratis tegoed ($5/maand) binnen één run
volledig leeg.

Daarom:
- **Roteren van zoektermen**: per run wordt maar 1 groep van `ZOEKTERMEN_PER_GROEP`
  (=6) zoektermen gebruikt, gekozen op basis van de datum (`date.today().toordinal()
  % aantal_groepen`). Over ~4 runs komen alle 24 categorieën aan bod.
- **`maxCrawledPlacesPerSearch` = `--limit`** (i.p.v. `limit * 2`) om het aantal
  websitebezoeken te beperken.
- **Frequentie verlaagd naar 2x per week** (dinsdag + vrijdag) i.p.v. dagelijks,
  zodat het gratis Apify-tegoed langer meegaat tijdens de testfase.

Zodra het systeem waarde aantoont (eerste deals), kan worden opgeschaald naar
dagelijks draaien — dit vraagt dan een betaald Apify-plan (Starter, ~$49/mnd, geschat
voldoende voor dagelijkse runs met de huidige kostenoptimalisatie).

Resultaten worden gededupliceerd op `place_id` en weggeschreven naar de Neon-tabel
`leads` (zie `systems/schema.sql`). Alleen écht nieuwe bedrijven worden ingevoegd
(`ON CONFLICT (place_id) DO NOTHING`), dus na verloop van tijd kan het zijn dat een
run minder dan 10 nieuwe leads oplevert simpelweg omdat de regio "opraakt" — dat is
verwacht gedrag, geen bug.

## Verwachte output
Tot 10 nieuwe rijen in de `leads` tabel met status `new`.

## Scheduling
GitHub Actions cron-job: `.github/workflows/daily_scrape.yml`, draait elke
dinsdag en vrijdag om 06:00 UTC (≈ 08:00 NL-tijd, let op zomer-/wintertijd-
verschuiving).
Secrets `APIFY_API_TOKEN`, `NEON_CONNECTION_STRING` en `ANTHROPIC_API_KEY` moeten
in de GitHub repo settings (Settings → Secrets and variables → Actions, tabblad
"Repository secrets") worden gezet — **niet** als "Environment secrets" of
"Variables", anders zijn ze leeg in de workflow.

## Edge cases & geleerde lessen
- **`apify-client` versie-verschil**: nieuwere versies van `apify-client` geven een
  object terug bij `actor().call()` i.p.v. een dict, waardoor `run["defaultDatasetId"]`
  faalt met `TypeError: 'Run' object is not subscriptable`. Opgelost met een
  `isinstance`-check die beide vormen ondersteunt.
- **Neon cold start**: bij inactiviteit gaat de Neon-compute "slapen", waardoor de
  eerste connectie soms een TCP-timeout geeft. `db.get_connection()` retried nu met
  oplopende wachttijd (0s, 3s, 6s, 10s) en `connect_timeout=15`.
- **GitHub secrets**: zorg dat secrets onder "Repository secrets" staan (niet
  "Environment secrets"); anders zijn ze leeg (`os.environ` geeft lege string,
  psycopg2 valt dan terug op een lokale socket-verbinding).
- **Apify-kosten**: zie sectie "Kostenbeheersing" hierboven.

## Toekomstige verbetering (indien nodig)
Als de alles-in-1 actor te weinig e-mailadressen/contactpersonen oplevert: overstappen
op een combinatie van (1) Google Maps Scraper voor basisdata + (2) een dedicated
website/contact-scraper actor (bv. "Contact Info Scraper") die specifiek e-mails en
namen van verantwoordelijken van de bedrijfswebsite haalt.
