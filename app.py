import streamlit as st
import time
import json
import os
from dotenv import load_dotenv
from agent import TravelAgent
from utils import format_itinerary, init_session_state
from metrics import TravelEvaluator, EvaluationReport

# ── Load API keys from .env ───────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voyager AI · Travel Concierge",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f1923 0%, #1a2a3a 50%, #0d1f2d 100%);
    color: #e8dcc8;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Hero header */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 3.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #c9a96e, #f0d5a0, #c9a96e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
    letter-spacing: -1px;
}
.hero-header p {
    color: #8fa8bc;
    font-size: 1.05rem;
    font-weight: 300;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Chat bubbles */
.chat-bubble-user {
    background: linear-gradient(135deg, #1e3a5f, #1a3050);
    border: 1px solid #2e5080;
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0 0.6rem 4rem;
    color: #dce8f5;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.chat-bubble-agent {
    background: linear-gradient(135deg, #1a2a1e, #152418);
    border: 1px solid #2a4a30;
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 4rem 0.6rem 0;
    color: #d4e8d0;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.bubble-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    opacity: 0.6;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1a26 0%, #111f2e 100%);
    border-right: 1px solid #1e3045;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #c9a96e;
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #c9a96e, #b8924d);
    color: #0f1923;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    letter-spacing: 0.04em;
    padding: 0.55rem 1.5rem;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(201,169,110,0.25);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(201,169,110,0.4);
}

/* Input */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0d1a26;
    border: 1px solid #2e4a65;
    color: #e8dcc8;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
}

/* Metrics */
.stMetric {
    background: rgba(255,255,255,0.03);
    border: 1px solid #1e3045;
    border-radius: 10px;
    padding: 0.8rem;
}

/* Status badge */
.status-badge {
    display: inline-block;
    background: rgba(50,200,100,0.15);
    border: 1px solid rgba(50,200,100,0.4);
    color: #50c864;
    border-radius: 20px;
    padding: 0.2rem 0.9rem;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* Divider */
.gold-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #c9a96e55, transparent);
    margin: 1.5rem 0;
}

/* Tool call indicator */
.tool-call {
    background: rgba(201,169,110,0.08);
    border-left: 3px solid #c9a96e;
    border-radius: 0 8px 8px 0;
    padding: 0.5rem 0.8rem;
    margin: 0.4rem 0;
    font-size: 0.82rem;
    color: #c9a96e;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
init_session_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✈️ Voyager AI")
    st.markdown('<div class="status-badge">● Agent Online</div>', unsafe_allow_html=True)
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    st.markdown("### 🗺️ Trip Preferences")
    budget = st.selectbox("Budget Range", ["Economy ($500–$1,500)", "Mid-range ($1,500–$4,000)", "Luxury ($4,000+)", "Ultra-luxury ($10,000+)"])
    travel_style = st.multiselect("Travel Style", ["Adventure", "Culture & History", "Beach & Relaxation", "Gastronomy", "Nature & Wildlife", "City Explorer", "Wellness & Spa"], default=["Culture & History"])
    group_type = st.selectbox("Travelling As", ["Solo", "Couple", "Family with kids", "Group of friends", "Business"])
    duration = st.slider("Trip Duration (days)", 3, 30, 7)

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.agent = None
            st.session_state.evaluator = None
            st.rerun()
    with col2:
        if st.button("📋 Export"):
            if st.session_state.messages:
                export_text = format_itinerary(st.session_state.messages)
                st.download_button("⬇️ Download", export_text, "itinerary.md", "text/markdown")

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    st.markdown("**Quick Starts:**")
    quick_prompts = [
        "🗼 Plan a week in Paris",
        "🏝️ Bali honeymoon, 10 days",
        "🗽 NYC family trip, 5 days",
        "🏔️ Swiss Alps adventure",
    ]
    for qp in quick_prompts:
        if st.button(qp, key=qp):
            st.session_state.quick_prompt = qp[2:].strip()
            st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>Voyager AI</h1>
    <p>Your personal luxury travel concierge · Powered by LangChain</p>
</div>
""", unsafe_allow_html=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌍 Destinations", "195+")
with col2:
    st.metric("🏨 Hotels", "50,000+")
with col3:
    st.metric("✈️ Airlines", "500+")
with col4:
    st.metric("🎭 Activities", "1M+")

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ── Initialize agent ──────────────────────────────────────────────────────────
context = {
    "budget": budget,
    "travel_style": travel_style,
    "group_type": group_type,
    "duration": duration,
}

if OPENAI_API_KEY and st.session_state.agent is None:
    with st.spinner("Initialising your AI concierge..."):
        try:
            st.session_state.agent = TravelAgent(
                openai_api_key=OPENAI_API_KEY,
                serpapi_key=SERPAPI_API_KEY or None,
                context=context,
            )
            st.session_state.evaluator = TravelEvaluator(
                openai_api_key=OPENAI_API_KEY,
                enable_llm_judge=True,
            )
        except Exception as e:
            st.error(f"Agent init error: {e}")

elif not OPENAI_API_KEY:
    st.error("⚠️ OPENAI_API_KEY not found. Please add it to your .env file and restart the app.")

# ── Render chat history ───────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-bubble-user">
                <div class="bubble-label">You</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-bubble-agent">
                <div class="bubble-label">✈️ Voyager AI</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
            if msg.get("tools_used"):
                for tool in msg["tools_used"]:
                    st.markdown(f'<div class="tool-call">🔧 Used: {tool}</div>', unsafe_allow_html=True)

# ── Handle quick prompt ───────────────────────────────────────────────────────
if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
    prompt = st.session_state.quick_prompt
    st.session_state.quick_prompt = None
    st.session_state.messages.append({"role": "user", "content": prompt})
    if st.session_state.agent:
        with st.spinner("🌍 Researching your perfect trip..."):
            result = st.session_state.agent.run(prompt, context)
        evaluator = st.session_state.get("evaluator")
        report = None
        if evaluator:
            report = evaluator.evaluate(
                question=prompt,
                answer=result["output"],
                tools_used=result.get("tools_used_full", result.get("tools_used", [])),
                tool_results=result.get("tool_results", []),
                latency_ms=result.get("latency_ms", 0),
            )
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["output"],
            "tools_used": result.get("tools_used", []),
            "eval_report": report.summary() if report else None,
        })
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_area(
            "Message your concierge…",
            placeholder="e.g. I want to spend 10 days in Japan in March, budget around $3,000. I love food and temples.",
            height=80,
            key="user_input",
            label_visibility="collapsed",
        )
    with col_send:
        st.markdown("<br>", unsafe_allow_html=True)
        send = st.button("Send ✈️", use_container_width=True)

if send and user_input.strip():
    if not st.session_state.agent:
        st.warning("Agent not initialised. Check your .env file and restart the app.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("🌍 Crafting your personalised itinerary…"):
            try:
                result = st.session_state.agent.run(user_input.strip(), context)
                evaluator = st.session_state.get("evaluator")
                report = None
                if evaluator:
                    report = evaluator.evaluate(
                        question=user_input.strip(),
                        answer=result["output"],
                        tools_used=result.get("tools_used_full", result.get("tools_used", [])),
                        tool_results=result.get("tool_results", []),
                        latency_ms=result.get("latency_ms", 0),
                    )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["output"],
                    "tools_used": result.get("tools_used", []),
                    "eval_report": report.summary() if report else None,
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Sorry, I encountered an error: {str(e)}. Please check your API key and try again.",
                    "tools_used": [],
                    "eval_report": None,
                })
        st.rerun()

# ── Metrics Dashboard ─────────────────────────────────────────────────────────
evaluator = st.session_state.get("evaluator")
eval_reports = evaluator.history if evaluator else []

if eval_reports:
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    with st.expander("📊 Tableau de bord d'évaluation", expanded=False):

        # ── Session KPIs ──
        agg = evaluator.get_aggregated_stats()
        st.markdown("#### 📈 Métriques de session")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Tours évalués", agg.get("total_turns", 0))
        k2.metric("Taux grounding", f"{agg.get('grounded_rate', 0)}%")
        k3.metric("Pipeline complet", f"{agg.get('pipeline_complete_rate', 0)}%")
        k4.metric("Risque hallucination", f"{agg.get('hallucination_risk_rate', 0)}%")
        judge_avg = agg.get("avg_judge_score")
        k5.metric("Score LLM Juge", f"{judge_avg:.2f}/5" if judge_avg else "N/A")

        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

        # ── Last turn detail ──
        last = eval_reports[-1]
        st.markdown(f"#### 🔍 Dernier tour · `{last.turn_id}`")

        tab1, tab2, tab3, tab4 = st.tabs([
            "🔎 Retrieval", "✍️ Génération", "🤖 Pipeline Agentique", "⚖️ LLM Juge"
        ])

        with tab1:
            r = last.retrieval
            if r:
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Docs récupérés", r.raw_count)
                c2.metric("Docs retenus", r.selected_count)
                c3.metric("Score max", r.top_1_raw_score)
                c4.metric("Score moyen", r.avg_raw_score)
                c5.metric("Compression ratio", r.compression_ratio)
                if r.empty_retrieval:
                    st.warning("⚠️ Retrieval vide – aucun document retourné")
                if r.over_retrieval:
                    st.warning("⚠️ Sur-retrieval détecté – filtrage insuffisant")
                if r.under_retrieval:
                    st.warning("⚠️ Sous-retrieval détecté – corpus ou requête trop restrictifs")

        with tab2:
            g = last.generation
            if g:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Réponse présente", "✅" if g.has_answer else "❌")
                c2.metric("Grounded", "✅" if g.grounded else "❌")
                c3.metric("Taille réponse", f"{g.answer_length} chars")
                c4.metric("Compression", g.compression_ratio)
                if g.potential_hallucination:
                    st.error("🚨 Hallucination potentielle – réponse non grounded sur des sources")
                if g.answer_too_short:
                    st.warning("⚠️ Réponse trop courte")
                if g.answer_too_long:
                    st.warning("⚠️ Réponse très longue – risque d'invention")

        with tab3:
            a = last.agentic
            if a:
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Étapes totales", a.execution_steps)
                c2.metric("Agents utilisés", a.agents_used)
                c3.metric("Étapes/agent", a.steps_per_agent)
                c4.metric("Pipeline complet", "✅" if a.pipeline_complete else "❌")
                c5.metric("Latence", f"{a.latency_ms:.0f} ms")

                st.markdown("**Séquence d'exécution :**")
                if a.tools_sequence:
                    st.code(" → ".join(a.tools_sequence))
                else:
                    st.info("Aucun outil appelé")

                cols = st.columns(4)
                cols[0].metric("Synthèse", "✅" if a.has_summary else "❌")
                cols[1].metric("Analyse", "✅" if a.has_analysis else "❌")
                cols[2].metric("Réponse", "✅" if a.has_answer else "❌")
                cols[3].metric("Supervision", "✅" if a.has_supervision else "❌")

                if not a.pipeline_complete:
                    st.warning("⚠️ Pipeline incomplet – certaines étapes essentielles manquantes")
                if not a.has_supervision:
                    st.info("ℹ️ Pas de supervision active sur ce tour")

        with tab4:
            j = last.judge
            if j:
                verdict_color = {"EXCELLENT": "🟢", "BON": "🔵", "ACCEPTABLE": "🟡", "INSUFFISANT": "🔴"}.get(j.verdict, "⚪")
                st.markdown(f"**Verdict : {verdict_color} {j.verdict}** · Score global : **{j.score_global}/5**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Pertinence", f"{j.pertinence}/5")
                c2.metric("Fidélité", f"{j.fidelite}/5")
                c3.metric("Complétude", f"{j.completude}/5")
                c4.metric("Clarté", f"{j.clarte}/5")
                if j.justification:
                    st.markdown(f"**Justification :** {j.justification}")
                if j.recommandations:
                    st.markdown("**Recommandations :**")
                    for rec in j.recommandations:
                        st.markdown(f"- {rec}")
            else:
                st.info("LLM Juge non activé ou non disponible pour ce tour.")

        # ── Export JSON ──
        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
        all_reports = [r.to_dict() for r in eval_reports]
        st.download_button(
            "⬇️ Exporter tous les rapports (JSON)",
            data=json.dumps(all_reports, ensure_ascii=False, indent=2),
            file_name="evaluation_reports.json",
            mime="application/json",
        )