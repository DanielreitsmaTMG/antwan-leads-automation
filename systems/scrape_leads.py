"""
Scrapes business leads near Rhoon via Apify's Google Maps Scraper, filters out
companies already in the database, and inserts up to N new leads into Neon.

Usage: python systems/scrape_leads.py [--limit 10]
"""
import argparse
import os
import sys

from apify_client import ApifyClient

sys.path.insert(0, os.path.dirname(__file__))
from db import insert_leads, init_schema, save_email_message, save_score  # noqa: E402
from ai_personalize import generate_message  # noqa: E402
from ai_score import score_lead  # noqa: E402

APIFY_ACTOR_ID = "compass/crawler-google-places"

SEARCH_TERMS = [
    "hotel",
    "vakantiepark",
    "bungalowpark",
    "camping",
    "recreatiecentrum",
    "pretpark",
    "ziekenhuis",
    "verpleeghuis",
    "verzorgingshuis",
    "woonzorgcentrum",
    "zwembad",
    "sportpark",
    "sportcomplex",
    "golfbaan",
    "conferentiecentrum",
    "congrescentrum",
    "bedrijventerrein",
    "kantorenpark",
    "landgoed",
    "begraafplaats",
    "middelbare school",
    "hogeschool",
    "universiteit",
    "VVE vastgoedbeheer",
]

# Rotterdam als centrum dekt automatisch een straal van ~40km rond Rhoon
# (Rhoon ligt 5km van Rotterdam; Rotterdam-gebied beslaat een groot gebied)
SEARCH_LOCATION = "Rotterdam, Netherlands"
SEARCH_RADIUS_KM = 40


def run_actor(client: ApifyClient, max_results: int) -> list[dict]:
    run_input = {
        "searchStringsArray": SEARCH_TERMS,
        "locationQuery": SEARCH_LOCATION,
        "maxCrawledPlacesPerSearch": max_results * 2,
        "maxImages": 0,
        "language": "nl",
        "skipClosedPlaces": True,
        "scrapeContacts": True,  # actor visits website to extract emails and contact names
    }
    run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def to_lead_row(item: dict) -> dict:
    return {
        "company_name": item.get("title"),
        "category": item.get("categoryName"),
        "address": item.get("address"),
        "city": item.get("city"),
        "phone": item.get("phone") or item.get("phoneUnformatted"),
        "website": item.get("website"),
        "email": (item.get("emails") or [None])[0],
        "contact_name": item.get("ownerName") or item.get("placeOwnerName"),
        "contact_role": "Eigenaar/Manager" if (item.get("ownerName") or item.get("placeOwnerName")) else None,
        "source": "apify_google_maps",
        "place_id": item.get("placeId") or item.get("fid"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="Max new leads to insert")
    args = parser.parse_args()

    init_schema()

    client = ApifyClient(os.environ["APIFY_API_TOKEN"])
    items = run_actor(client, args.limit)

    rows = [to_lead_row(item) for item in items if item.get("placeId") or item.get("fid")]
    rows = [r for r in rows if r["company_name"]][: args.limit]

    new_leads = insert_leads(rows)

    for lead in new_leads:
        msg = generate_message(lead)
        save_email_message(lead["id"], msg["subject"], msg["body"])
        score, _ = score_lead(lead)
        save_score(lead["id"], score)
        print(f"  ✓ {lead['company_name']} (score: {score}/5)")

    print(f"\nGescraped: {len(items)} plekken | Nieuw ingevoegd: {len(new_leads)} leads | Doel: {args.limit}")


if __name__ == "__main__":
    main()
