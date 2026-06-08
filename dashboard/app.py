"""Streamlit dashboard for Antwan Tuinprojecten lead automation."""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems"))
from db import fetch_leads, update_lead_status  # noqa: E402
from generate_email import build_message  # noqa: E402

PRIMARY = "#305544"   # Antwan donkergroen
ACCENT = "#E28759"    # Antwan terracotta

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

st.title("🌿 Antwan Tuinprojecten — Lead dashboard")
st.caption("Dagelijks verse leads voor zakelijk groenonderhoud — hotels, VVE's, campings, bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden.")

status_filter = st.selectbox("Status", ["new", "contacted", "replied", "not_interested", "won", "alle"], index=0)
leads = fetch_leads(status=None if status_filter == "alle" else status_filter)

st.write(f"**{len(leads)}** leads gevonden.")

for lead in leads:
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
            st.caption(f"Status: `{lead['status']}` · gescraped op {lead['scraped_at']}")

        with col2:
            msg = build_message(lead)
            st.markdown("**Voorgesteld bericht:**")
            st.text_area("Bericht", value=msg["body"], height=220, key=f"msg_{lead['id']}", label_visibility="collapsed")

            if lead.get("email"):
                st.link_button("✉️ Open in mail-app", msg["mailto_url"], use_container_width=True)
            else:
                st.button("✉️ Geen e-mailadres bekend", disabled=True, use_container_width=True, key=f"noemail_{lead['id']}")

            new_status = st.selectbox(
                "Status bijwerken",
                ["new", "contacted", "replied", "not_interested", "won"],
                index=["new", "contacted", "replied", "not_interested", "won"].index(lead["status"]),
                key=f"status_{lead['id']}",
            )
            if new_status != lead["status"]:
                if st.button("Opslaan", key=f"save_{lead['id']}"):
                    update_lead_status(lead["id"], new_status)
                    st.rerun()
