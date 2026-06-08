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
from db import insert_leads, init_schema  # noqa: E402

APIFY_ACTOR_ID = "compass/crawler-google-places"

SEARCH_TERMS = [
    "hotel",
    "vakantiepark",
    "camping",
    "bedrijventerrein",
    "ziekenhuis",
    "zwembad",
    "VVE vastgoedbeheer",
    "kantorenpark",
]

# Rhoon, NL — ~25km radius
SEARCH_LOCATION = "Rhoon, Netherlands"
SEARCH_RADIUS_M = 25_000


def run_actor(client: ApifyClient, max_results: int) -> list[dict]:
    run_input = {
        "searchStringsArray": SEARCH_TERMS,
        "locationQuery": SEARCH_LOCATION,
        "maxCrawledPlacesPerSearch": max_results * 3,  # overshoot, dedupe later
        "language": "nl",
        "skipClosedPlaces": True,
        "scrapeContacts": True,  # actor visits the website to pull emails when available
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

    inserted = insert_leads(rows)
    print(f"Scraped {len(items)} places, inserted {inserted} new leads (target {args.limit}).")


if __name__ == "__main__":
    main()
