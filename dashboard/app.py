"""Streamlit dashboard voor Antwan Tuinprojecten lead automation."""
import os
import sys

import streamlit as st

# Streamlit Cloud injecteert secrets in st.secrets, niet in os.environ.
# systems/ leest altijd via os.environ zodat het overal hetzelfde werkt
# (lokaal, GitHub Actions, Streamlit Cloud).
for _key in ("APIFY_API_TOKEN", "NEON_CONNECTION_STRING", "ANTHROPIC_API_KEY"):
    if _key in st.secrets and _key not in os.environ:
        os.environ[_key] = st.secrets[_key]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems"))
from db import fetch_leads, update_lead_status, save_email_message  # noqa: E402
from generate_email import build_message, build_mailto  # noqa: E402
from ai_personalize import generate_message  # noqa: E402

PRIMARY = "#305544"   # Antwan donkergroen
ACCENT  = "#E28759"   # Antwan terracotta

STATUS_OPTIES = ["nieuw", "benaderd", "gereageerd", "niet_interessant", "gewonnen"]
STATUS_VERTALING = {
    "new":             "nieuw",
    "contacted":       "benaderd",
    "replied":         "gereageerd",
    "not_interested":  "niet_interessant",
    "won":             "gewonnen",
}
STATUS_TERUGVERTALING = {v: k for k, v in STATUS_VERTALING.items()}

st.set_page_config(page_title="Antwan Tuinprojecten — Leads", page_icon="🌿", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #FAFAF8; }}
    h1, h2, h3 {{ color: {PRIMARY}; font-family: 'Georgia', serif; }}
    div.stButton > button {{
        background-color: {ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
    }}
    div.stButton > button:hover {{
        background-color: {PRIMARY};
        color: white;
    }}
    span[data-baseweb="tag"] {{ background-color: {PRIMARY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌿 Antwan Tuinprojecten — Leads")
st.caption("Dagelijks verse leads voor zakelijk groenonderhoud — hotels, VVE's, campings, bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden.")

status_filter_nl = st.selectbox(
    "Filter op status",
    ["nieuw", "benaderd", "gereageerd", "niet_interessant", "gewonnen", "alle"],
    index=0,
)

status_filter_en = None if status_filter_nl == "alle" else STATUS_TERUGVERTALING.get(status_filter_nl, status_filter_nl)
leads = fetch_leads(status=status_filter_en)

st.write(f"**{len(leads)}** leads gevonden.")

for lead in leads:
    status_nl = STATUS_VERTALING.get(lead["status"], lead["status"])

    with st.container(border=True):
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader(lead["company_name"])
            st.write(f"**Categorie:** {lead.get('category') or '—'}")
            st.write(f"**Adres:** {lead.get('address') or '—'}")
            st.write(f"**Telefoon:** {lead.get('phone') or '—'}")
            st.write(f"**Website:** {lead.get('website') or '—'}")
            st.write(f"**Contactpersoon:** {lead.get('contact_name') or '—'} ({lead.get('contact_role') or 'onbekend'})")
            st.write(f"**E-mail:** {lead.get('email') or '⚠️ niet gevonden'}")
            st.caption(f"Status: `{status_nl}` · gescraped op {lead['scraped_at']}")

        with col2:
            # AI-bericht gegenereerd tijdens de scrape en opgeslagen in de database.
            # Oudere leads zonder opgeslagen bericht krijgen de statische template als fallback.
            subject = lead.get("email_subject")
            body    = lead.get("email_body")
            if not body:
                fallback = build_message(lead)
                subject, body = fallback["subject"], fallback["body"]

            st.markdown("**Voorgesteld bericht (AI-gepersonaliseerd):**")
            bewerkt_bericht = st.text_area(
                "Bericht",
                value=body,
                height=220,
                key=f"bericht_{lead['id']}",
                label_visibility="collapsed",
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Nieuw bericht genereren", key=f"genereer_{lead['id']}", use_container_width=True):
                    with st.spinner("Bericht wordt gegenereerd..."):
                        nieuw_bericht = generate_message(lead)
                        save_email_message(lead["id"], nieuw_bericht["subject"], nieuw_bericht["body"])
                    st.rerun()
            with col_b:
                mailto_url = build_mailto(lead.get("email"), subject, bewerkt_bericht)
                if lead.get("email"):
                    st.link_button("✉️ Openen in mail-app", mailto_url, use_container_width=True)
                else:
                    st.button("✉️ Geen e-mailadres bekend", disabled=True, use_container_width=True, key=f"geenmailadres_{lead['id']}")

            nieuwe_status_nl = st.selectbox(
                "Status bijwerken",
                STATUS_OPTIES,
                index=STATUS_OPTIES.index(status_nl) if status_nl in STATUS_OPTIES else 0,
                key=f"status_{lead['id']}",
            )
            if nieuwe_status_nl != status_nl:
                if st.button("Opslaan", key=f"opslaan_{lead['id']}"):
                    update_lead_status(lead["id"], STATUS_TERUGVERTALING[nieuwe_status_nl])
                    st.rerun()
