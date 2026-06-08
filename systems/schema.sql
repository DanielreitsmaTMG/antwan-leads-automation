-- Neon Postgres schema for Antwan Tuinprojecten lead automation
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    category TEXT,
    address TEXT,
    city TEXT,
    phone TEXT,
    website TEXT,
    email TEXT,
    contact_name TEXT,
    contact_role TEXT,
    source TEXT DEFAULT 'apify_google_maps',
    place_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'new',  -- new | contacted | replied | not_interested | won
    notes TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contacted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_scraped_at ON leads(scraped_at);
