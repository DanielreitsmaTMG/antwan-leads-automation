"""Streamlit dashboard voor Antwan Tuinprojecten lead automation."""
import io
import os
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit Cloud: secrets naar os.environ spiegelen zodat systems/ altijd via os.environ leest.
for _key in ("APIFY_API_TOKEN", "NEON_CONNECTION_STRING", "ANTHROPIC_API_KEY"):
    if _key in st.secrets and _key not in os.environ:
        os.environ[_key] = st.secrets[_key]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems"))
from db import fetch_leads, fetch_analytics, update_lead_status, save_email_message, save_score  # noqa: E402
from generate_email import build_message, build_mailto, build_whatsapp  # noqa: E402
from ai_personalize import generate_message  # noqa: E402
from ai_score import score_lead, sterren  # noqa: E402

# ── Huisstijl ──────────────────────────────────────────────────────────────
PRIMARY = "#305544"
ACCENT  = "#E28759"

STATUS_OPTIES   = ["nieuw", "benaderd", "gereageerd", "niet_interessant", "gewonnen"]
STATUS_NL_EN    = {"nieuw": "new", "benaderd": "contacted", "gereageerd": "replied",
                   "niet_interessant": "not_interested", "gewonnen": "won"}
STATUS_EN_NL    = {v: k for k, v in STATUS_NL_EN.items()}

st.set_page_config(page_title="Antwan Tuinprojecten — Leads", page_icon="🌿", layout="wide")

st.markdown(f"""
<style>
.stApp {{ background-color: #FAFAF8; }}
h1, h2, h3 {{ color: {PRIMARY}; font-family: 'Georgia', serif; }}
div.stButton > button {{
    background-color: {ACCENT}; color: white; border: none; border-radius: 6px;
}}
div.stButton > button:hover {{ background-color: {PRIMARY}; color: white; }}
div[data-testid="stMetricValue"] {{ color: {PRIMARY}; font-size: 2rem; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)


# ── Login ──────────────────────────────────────────────────────────────────
def check_login() -> bool:
    if st.session_state.get("ingelogd"):
        return True

    st.markdown(f"<h1 style='text-align:center;color:{PRIMARY}'>🌿 Antwan Tuinprojecten</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888'>Lead management systeem</p>", unsafe_allow_html=True)
    st.markdown("---")

    col = st.columns([1, 1, 1])[1]
    with col:
        gebruikersnaam = st.text_input("E-mailadres", placeholder="info@antwan.nl", key="usr")
        wachtwoord     = st.text_input("Wachtwoord", type="password", key="pwd")
        if st.button("Inloggen", use_container_width=True):
            juist_gebruiker  = st.secrets.get("DASHBOARD_USERNAME", "info@antwan.nl")
            juist_wachtwoord = st.secrets.get("DASHBOARD_PASSWORD", "antwan2024")
            if gebruikersnaam == juist_gebruiker and wachtwoord == juist_wachtwoord:
                st.session_state.ingelogd = True
                st.rerun()
            else:
                st.error("Ongeldig e-mailadres of wachtwoord — probeer het opnieuw.")
    return False


if not check_login():
    st.stop()


# ── Header ─────────────────────────────────────────────────────────────────
col_logo, col_titel, col_uitlog = st.columns([1, 6, 1])
with col_titel:
    st.title("🌿 Antwan Tuinprojecten — Leads")
    st.caption("Dagelijks verse leads voor zakelijk groenonderhoud — hotels, VVE's, campings, bedrijventerreinen, ziekenhuizen, vakantieparken, zwembaden.")
with col_uitlog:
    st.write("")
    st.write("")
    if st.button("Uitloggen"):
        st.session_state.ingelogd = False
        st.rerun()


# ── Tabs ───────────────────────────────────────────────────────────────────
tab_leads, tab_analyse = st.tabs(["📋 Leads", "📊 Analyse"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LEADS
# ══════════════════════════════════════════════════════════════════════════════
with tab_leads:

    # Filters
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])
    with col_f1:
        status_filter_nl = st.selectbox("Status", ["alle"] + STATUS_OPTIES, index=0)
    with col_f2:
        min_score = st.selectbox("Minimale score", [1, 2, 3, 4, 5], index=0)
    with col_f3:
        zoekterm = st.text_input("Zoek op naam of categorie", placeholder="bijv. hotel")
    with col_f4:
        st.write("")
        st.write("")
        export_clicked = st.button("⬇️ Exporteren naar Excel", use_container_width=True)

    status_en = None if status_filter_nl == "alle" else STATUS_NL_EN.get(status_filter_nl)
    leads = fetch_leads(status=status_en)

    # Filteren op score en zoekterm
    if min_score > 1:
        leads = [l for l in leads if (l.get("score") or 0) >= min_score]
    if zoekterm:
        term = zoekterm.lower()
        leads = [l for l in leads if term in (l.get("company_name") or "").lower()
                 or term in (l.get("category") or "").lower()]

    st.write(f"**{len(leads)}** leads gevonden.")

    # Excel export
    if export_clicked:
        df = pd.DataFrame(leads)
        kolommen = ["company_name", "category", "address", "city", "phone",
                    "website", "email", "contact_name", "score", "status", "scraped_at"]
        df = df[[k for k in kolommen if k in df.columns]]
        df.columns = ["Bedrijfsnaam", "Categorie", "Adres", "Plaats", "Telefoon",
                      "Website", "E-mail", "Contactpersoon", "Score", "Status", "Gescraped op"][:len(df.columns)]
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Leads")
        st.download_button(
            label="📥 Download Excel-bestand",
            data=buffer.getvalue(),
            file_name=f"antwan_leads_{datetime.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # Lead-kaarten
    for lead in leads:
        status_nl   = STATUS_EN_NL.get(lead["status"], lead["status"])
        score_waarde = lead.get("score") or 0
        score_tekst  = sterren(score_waarde) if score_waarde else "☆☆☆☆☆ (nog niet beoordeeld)"

        with st.container(border=True):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.subheader(f"{lead['company_name']}  {score_tekst}")
                st.write(f"**Categorie:** {lead.get('category') or '—'}")
                st.write(f"**Adres:** {lead.get('address') or '—'}")
                st.write(f"**Telefoon:** {lead.get('phone') or '—'}")
                st.write(f"**Website:** {lead.get('website') or '—'}")
                st.write(f"**Contactpersoon:** {lead.get('contact_name') or '—'} "
                         f"({lead.get('contact_role') or 'onbekend'})")
                st.write(f"**E-mail:** {lead.get('email') or '⚠️ niet gevonden'}")
                st.caption(f"Status: `{status_nl}` · gescraped op {lead['scraped_at']}")

                # Score opnieuw laten berekenen
                if st.button("🔁 Score herberekenen", key=f"score_{lead['id']}", use_container_width=False):
                    with st.spinner("Score berekenen..."):
                        nieuwe_score, _ = score_lead(lead)
                        save_score(lead["id"], nieuwe_score)
                    st.rerun()

            with col2:
                subject = lead.get("email_subject")
                body    = lead.get("email_body")
                if not body:
                    fallback = build_message(lead)
                    subject, body = fallback["subject"], fallback["body"]

                st.markdown("**Voorgesteld bericht (AI-gepersonaliseerd):**")
                bewerkt_bericht = st.text_area(
                    "Bericht", value=body, height=200,
                    key=f"bericht_{lead['id']}", label_visibility="collapsed",
                )

                if st.button("🔄 Nieuw bericht genereren", key=f"genereer_{lead['id']}", use_container_width=True):
                    with st.spinner("Bericht wordt gegenereerd..."):
                        nieuw = generate_message(lead)
                        save_email_message(lead["id"], nieuw["subject"], nieuw["body"])
                    st.rerun()

                # Actieknoppen
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    mailto_url = build_mailto(lead.get("email"), subject, bewerkt_bericht)
                    if lead.get("email"):
                        st.link_button("✉️ E-mail", mailto_url, use_container_width=True)
                    else:
                        st.button("✉️ E-mail", disabled=True, use_container_width=True, key=f"email_{lead['id']}")
                with col_b:
                    wa_url = build_whatsapp(lead.get("phone"), bewerkt_bericht)
                    if wa_url:
                        st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
                    else:
                        st.button("💬 WhatsApp", disabled=True, use_container_width=True, key=f"wa_{lead['id']}")
                with col_c:
                    if lead.get("phone"):
                        st.link_button("📞 Bellen", f"tel:{lead['phone']}", use_container_width=True)
                    else:
                        st.button("📞 Bellen", disabled=True, use_container_width=True, key=f"tel_{lead['id']}")

                # Status bijwerken
                nieuwe_status_nl = st.selectbox(
                    "Status bijwerken",
                    STATUS_OPTIES,
                    index=STATUS_OPTIES.index(status_nl) if status_nl in STATUS_OPTIES else 0,
                    key=f"status_{lead['id']}",
                )
                if nieuwe_status_nl != status_nl:
                    if st.button("Opslaan", key=f"opslaan_{lead['id']}"):
                        update_lead_status(lead["id"], STATUS_NL_EN[nieuwe_status_nl])
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYSE
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyse:
    alle_leads = fetch_leads()
    data       = fetch_analytics()

    if not alle_leads:
        st.info("Nog geen leads in de database. Voer eerst een scrape uit.")
        st.stop()

    df_all = pd.DataFrame(alle_leads)
    df_all["status_nl"] = df_all["status"].map(STATUS_EN_NL)

    # ── KPI-metrics ────────────────────────────────────────────────────────
    totaal      = len(df_all)
    benaderd    = len(df_all[df_all["status"] == "contacted"])
    gewonnen    = len(df_all[df_all["status"] == "won"])
    conv_pct    = round(gewonnen / totaal * 100, 1) if totaal else 0
    gem_score   = round(df_all["score"].dropna().mean(), 1) if "score" in df_all else "—"

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Totaal leads",       totaal)
    k2.metric("Benaderd",           benaderd)
    k3.metric("Gewonnen",           gewonnen)
    k4.metric("Conversieratio",     f"{conv_pct}%")
    k5.metric("Gem. leadscore",     gem_score)

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)

    # Status verdeling
    with col_g1:
        status_counts = df_all["status_nl"].value_counts().reset_index()
        status_counts.columns = ["Status", "Aantal"]
        fig = px.pie(
            status_counts, names="Status", values="Aantal",
            title="Verdeling per status",
            color_discrete_sequence=[PRIMARY, ACCENT, "#7aab93", "#c4845a", "#4a8069"],
        )
        fig.update_layout(title_font_color=PRIMARY)
        st.plotly_chart(fig, use_container_width=True)

    # Categorie top 10
    with col_g2:
        cat_counts = df_all["category"].fillna("Onbekend").value_counts().head(10).reset_index()
        cat_counts.columns = ["Categorie", "Aantal"]
        fig2 = px.bar(
            cat_counts, x="Aantal", y="Categorie", orientation="h",
            title="Top 10 categorieën",
            color_discrete_sequence=[PRIMARY],
        )
        fig2.update_layout(title_font_color=PRIMARY, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    # Leads per week
    with col_g3:
        df_week = pd.DataFrame(data)
        if not df_week.empty and "week" in df_week.columns:
            df_week["week"] = pd.to_datetime(df_week["week"]).dt.strftime("%d %b")
            week_counts = df_week.groupby("week").size().reset_index(name="Nieuwe leads")
            fig3 = px.bar(
                week_counts, x="week", y="Nieuwe leads",
                title="Nieuwe leads per week",
                color_discrete_sequence=[ACCENT],
            )
            fig3.update_layout(title_font_color=PRIMARY, xaxis_title="Week")
            st.plotly_chart(fig3, use_container_width=True)

    # Score verdeling
    with col_g4:
        if "score" in df_all.columns:
            score_counts = df_all["score"].dropna().astype(int).value_counts().sort_index().reset_index()
            score_counts.columns = ["Score", "Aantal"]
            score_counts["Score"] = score_counts["Score"].apply(lambda s: f"{'⭐'*s} ({s}/5)")
            fig4 = px.bar(
                score_counts, x="Score", y="Aantal",
                title="Verdeling AI-leadscore",
                color_discrete_sequence=[PRIMARY],
            )
            fig4.update_layout(title_font_color=PRIMARY)
            st.plotly_chart(fig4, use_container_width=True)
