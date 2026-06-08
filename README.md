# Sales-automation — Antwan Tuinprojecten

Dagelijks automatisch zakelijke leads scrapen (hotels, VVE's, campings,
bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden binnen ±25km van Rhoon),
opslaan in Neon Postgres en beheren via een Streamlit-dashboard in Antwan's huisstijl
— inclusief één-klik mailto-link met een voorgesteld sales-bericht per lead.

## Stack
- **Scraping:** Apify (`compass/crawler-google-places` — Google Maps Scraper)
- **Database:** Neon (serverless Postgres)
- **Scheduling:** GitHub Actions (dagelijkse cron)
- **Dashboard:** Streamlit

## Setup

### 1. Database
Maak een Neon-project aan op [neon.tech](https://neon.tech) en kopieer de
connection string. Het schema (`systems/schema.sql`) wordt automatisch aangemaakt
bij de eerste run van de scraper.

### 2. Apify
Maak een account aan op [apify.com](https://apify.com), kopieer je API-token uit
**Settings → Integrations**.

### 3. Lokaal draaien
```bash
cp .env.example .env   # vul APIFY_API_TOKEN en NEON_CONNECTION_STRING in
pip install -r requirements.txt

# eenmalig/test: scrape 10 leads
python systems/scrape_leads.py --limit 10

# dashboard starten
streamlit run dashboard/app.py
```

Voor het dashboard kun je de credentials ook in `.streamlit/secrets.toml` zetten
(zie Streamlit-documentatie) i.p.v. `.env`.

### 4. Dagelijkse automatisering (GitHub Actions)
1. Push deze repo naar GitHub.
2. Ga naar **Settings → Secrets and variables → Actions** en voeg toe:
   - `APIFY_API_TOKEN`
   - `NEON_CONNECTION_STRING`
3. De workflow `.github/workflows/daily_scrape.yml` draait dagelijks om 06:00 UTC
   en kan ook handmatig gestart worden via de "Run workflow" knop (Actions-tab).

### 5. Dashboard hosten
Het eenvoudigst via [Streamlit Community Cloud](https://streamlit.io/cloud):
koppel de GitHub-repo, wijs `dashboard/app.py` aan als entrypoint, en zet de
credentials in de app-secrets (TOML-formaat, zelfde keys als hierboven).

## Structuur
```
blueprints/   # SOP's: wat er moet gebeuren en hoe
systems/      # Python: scraping, database, e-mailtekst-generatie
dashboard/    # Streamlit-app in Antwan-huisstijl (#305544 / #E28759)
.github/      # Dagelijkse cron-workflow
```

## Huisstijl Antwan Tuinprojecten
- Donkergroen: `#305544`
- Terracotta-accent: `#E28759`
- Tone-of-voice: warm, professioneel, "ontzorgen met behoud van inspraak"
- Contact: info@antwan.nl · 010-5011150 · Nijverheidsweg 29, 3161 GJ Rhoon
