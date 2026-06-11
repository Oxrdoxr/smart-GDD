"""
app/ui.py — All Streamlit UI components
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import json
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='font-size:0.85rem;'>🗺️ AGENT MAP</h2>", unsafe_allow_html=True)
        st.markdown("---")

        agents = [
            ("📋", "PLANNER",    "planner_output",    "Gemini Flash",  "Idea → Pillars"),
            ("🔍", "RESEARCHER", "researcher_output", "Gemini Flash",  "Market Analysis"),
            ("✍️", "WRITER",     "writer_output",     "Claude Sonnet", "Full GDD"),
            ("🔎", "REVIEWER",   "reviewer_output",   "Claude Haiku",  "QA Score"),
        ]

        for icon, name, key, model, desc in agents:
            done = st.session_state.get(key) is not None
            badge_cls = "done" if done else "wait"
            badge_txt = "✓ DONE" if done else "WAIT"
            st.markdown(
                f"<div style='margin-bottom:14px'>"
                f"{icon} <b style='font-family:\"Press Start 2P\",monospace;font-size:0.62rem'>{name}</b>"
                f"<span class='checkpoint {badge_cls}'>{badge_txt}</span><br>"
                f"<span style='font-size:0.72rem;color:#2e7d32;margin-left:22px'>{model}</span><br>"
                f"<span style='font-size:0.72rem;color:#4a7c59;margin-left:22px'>{desc}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            "<div style='font-family:\"Press Start 2P\",monospace;font-size:0.52rem;color:#2e7d32;line-height:2;'>"
            "🆓 FREE ASSETS<br><br>"
            "• OpenGameArt.org<br>"
            "• itch.io/game-assets<br>"
            "• Kenney.nl<br>"
            "• CraftPix.net<br>"
            "• Freesound.org"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.session_state.get("pipeline_run"):
            if st.button("🔄 NEW GAME"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


def render_input(run_pipeline_fn):
    st.markdown("### 💡 YOUR GAME IDEA")
    idea = st.text_area(
        label="idea",
        placeholder='e.g. "A horror game where your flashlight battery IS your health bar"',
        height=90,
        key="idea_field",
        label_visibility="collapsed",
    )
    col1, _ = st.columns([2, 5])
    with col1:
        go = st.button("▶ START", use_container_width=True)

    if go:
        if not idea.strip():
            st.warning("Enter a game idea first!")
        else:
            st.session_state.game_idea = idea.strip()
            st.session_state.revision_count = 0
            run_pipeline_fn(st.session_state.game_idea)
            st.rerun()


def render_results():
    idea       = st.session_state.game_idea
    planner    = st.session_state.planner_output    or {}
    researcher = st.session_state.researcher_output or {}
    writer     = st.session_state.writer_output     or {}
    reviewer   = st.session_state.reviewer_output   or {}

    score  = reviewer.get("score", "?")
    passed = st.session_state.review_passed
    cls    = "pass" if passed else "warn"
    icon   = "🏆 REVIEW PASSED" if passed else "⚠ NEEDS WORK"

    st.markdown(
        f"<div class='score-banner {cls}'>"
        f"<span>{icon}</span><span>SCORE: {score}/10</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**💡 Idea:** _{idea}_")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 PILLARS", "🔍 RESEARCH", "📄 GDD", "🎮 ASSETS", "🔎 REVIEW"
    ])

    with tab1:
        st.markdown("## Design Pillars")
        if planner:
            cols = st.columns(2)
            fields = [
                ("🎲 Genre", "genre"), ("🔁 Core Loop", "core_loop"),
                ("👥 Audience", "target_audience"), ("🖥️ Platform", "platform"),
                ("🎭 Tone", "tone"), ("✨ Unique Hook", "unique_hook"),
            ]
            for i, (label, key) in enumerate(fields):
                with cols[i % 2]:
                    st.markdown(
                        f"<div class='px-card done'><b>{label}</b><br>"
                        f"<span style='color:#2e7d32'>{planner.get(key,'—')}</span></div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("**🏛️ Design Pillars**")
            for p in planner.get("pillars", []):
                st.markdown(f"- {p}")

    with tab2:
        st.markdown("## Market Research")
        if researcher:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**🏆 Market Gap**\n\n{researcher.get('market_gap','—')}")
                st.markdown(f"**🎯 Opportunity**\n\n{researcher.get('main_opportunity','—')}")
            with c2:
                st.markdown(f"**⚠️ Risk**\n\n{researcher.get('main_risk','—')}")
                st.markdown(f"**👥 Audience**\n\n{researcher.get('audience_size','—')}")
            st.markdown("### Comparable Games")
            for game in researcher.get("comparable_games", []):
                st.markdown(
                    f"<div class='px-card done'><b>{game.get('title','')}</b> — "
                    f"{game.get('revenue','')}<br>"
                    f"<span style='color:#4a7c59'>{game.get('why_relevant','')}</span></div>",
                    unsafe_allow_html=True,
                )

    with tab3:
        st.markdown("## Game Design Document")
        st.caption("✍️ Written by Claude Sonnet")
        if writer:
            sections = [
                ("📖 Story", "story_summary"),
                ("🦸 Protagonist", "protagonist"),
                ("⚙️ Core Mechanic", "core_mechanic"),
                ("📈 Progression", "progression_system"),
                ("🗺️ Level Design", "level_design"),
                ("🖥️ UI / UX", "ui_ux_notes"),
                ("💰 Monetization", "monetization"),
                ("🎨 Art Direction", "art_direction"),
            ]
            for label, key in sections:
                with st.expander(label, expanded=False):
                    val = st.text_area(
                        "edit", value=writer.get(key, "—"),
                        key=f"edit_{key}", height=100,
                        label_visibility="collapsed",
                    )
                    st.session_state.writer_output[key] = val

        if st.button("💾 EXPORT JSON"):
            st.download_button(
                "⬇️ Download GDD",
                data=json.dumps({
                    "idea": idea, "pillars": planner,
                    "research": researcher,
                    "gdd": st.session_state.writer_output,
                    "review": reviewer,
                }, indent=2),
                file_name="game_design_document.json",
                mime="application/json",
            )

    with tab4:
        st.markdown("## 🎮 Free Asset Sources")
        ai_rec = writer.get("free_assets", "")
        if ai_rec:
            st.markdown(
                f"<div class='px-card done'><b>🤖 AI Recommendation</b><br><br>{ai_rec}</div>",
                unsafe_allow_html=True,
            )
        asset_sites = [
            ("🌟 OpenGameArt.org", "Free CC0/CC-BY sprites, music, sfx", "https://opengameart.org"),
            ("🎯 Kenney.nl", "1000+ free packs — pixel & vector", "https://kenney.nl/assets"),
            ("🏪 itch.io/game-assets", "Free & pay-what-you-want", "https://itch.io/game-assets/free"),
            ("🎨 CraftPix.net", "Free sprites and tilesets", "https://craftpix.net/freebies"),
            ("🎵 Freesound.org", "Free SFX and music loops", "https://freesound.org"),
            ("🖼️ GameDevMarket", "Free weekly asset drops", "https://gamedevmarket.net/category/free"),
        ]
        cols = st.columns(2)
        for i, (name, desc, url) in enumerate(asset_sites):
            with cols[i % 2]:
                st.markdown(
                    f"<div class='px-card'><b>{name}</b><br>"
                    f"<span style='font-size:0.85rem;color:#4a7c59'>{desc}</span><br>"
                    f"<a href='{url}' target='_blank' style='color:#388e3c;font-size:0.8rem'>→ {url.replace('https://','')}</a></div>",
                    unsafe_allow_html=True,
                )

    with tab5:
        st.markdown("## Reviewer Report")
        st.caption("🔎 Scored by Claude Haiku")
        if reviewer:
            color = "#1b5e20" if passed else "#e65100"
            st.markdown(
                f"<div style='font-family:\"Press Start 2P\",monospace;"
                f"font-size:2.5rem;color:{color};text-align:center;padding:1rem;'>"
                f"{score}/10</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**📝 Verdict:** {reviewer.get('recommendation','—')}")
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**✅ Strengths**")
                for s in reviewer.get("strengths", []):
                    st.markdown(f"- {s}")
            with c2:
                st.markdown("**⚠️ Issues**")
                for iss in reviewer.get("issues", []):
                    st.markdown(f"- {iss}")
            if reviewer.get("missing_sections"):
                st.warning("Missing: " + ", ".join(reviewer["missing_sections"]))
