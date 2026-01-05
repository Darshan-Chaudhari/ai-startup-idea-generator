import streamlit as st
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai import init
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as VertexCredentials
from google.oauth2.service_account import Credentials as GspreadCredentials  # same class, different alias
from datetime import datetime
import gspread

import json
from google.oauth2.service_account import Credentials as VertexCredentials

# Load from string secret (for deployment)
vertex_credentials = None
if "SERVICE_ACCOUNT_JSON" in st.secrets:
    json_dict = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
    vertex_credentials = VertexCredentials.from_service_account_info(
        json_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

st.set_page_config(page_title="AI Startup Idea Generator", page_icon="🚀")
st.title("🚀 AI Startup Idea Generator")
st.markdown("Realistic Bay Area startup ideas with Gemini on Google Cloud")

field = st.text_input("Industry/field", value="")
num_ideas = st.slider("Number of ideas", 1, 3, 2)
temperature = st.slider("Creativity (Higher values mean higher creativity!)", 0.5, 1.2, 0.8, 0.1)

if st.button("Generate Ideas"):
    if not field.strip():
        st.warning("Enter a field!")
        st.stop()

    with st.spinner("Brainstorming 2026 winners... 🤔"):
        try:
            init(
                project="my-project-ai-idea",  # <-- replace if your project ID is different
                location="us-central1",
                credentials=vertex_credentials
            )

            model = GenerativeModel("gemini-2.5-pro")

            prompt = f"""You are my entrepreneurship advisor with expert business knowledge and creative yet realistic mindset. Generate EXACTLY {num_ideas} complete startup ideas in {field}.

STRICTLY use this exact markdown structure for EVERY idea—do not combine sections or use paragraphs:

# Idea {{1-{num_ideas}}}: {{Name}}

**One-sentence pitch:** {{Pitch}}

**One-sentence description:** {{Description}}

**Target market:** {{Detailed description}}

**Revenue model:** {{e.g., subscription, freemium}}

**Key competitors:** {{2-3 listed}}

**SWOT Analysis:**
- **Strengths:** {{3-5 bullets}}
- **Weaknesses:** {{3-5 bullets}}
- **Opportunities:** {{3-5 bullets}}
- **Threats:** {{3-5 bullets}}

**Practicality for 2026:** {{One separate sentence: Is this worth pursuing? Why/why not, based on trends/AI leverage?}}

Complete EVERY idea and section FULLY with the required bullets—no truncation, no early stop. Output ONLY in markdown."""

            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=8192
                )
            )

            ideas_md = response.text
            st.session_state.ideas = ideas_md 
            st.success("Ideas generated! 🚀")

        except Exception as e:
            st.error(f"Vertex AI error: {str(e)}")
            st.info("Fixes: Check project ID, enable Vertex AI API, or quota in console.cloud.google.com/vertex-ai")

if "ideas" in st.session_state:
    st.markdown("### Your Latest Startup Ideas")
    st.markdown(st.session_state.ideas)

    st.caption("How useful were these ideas?")

    rating = st.slider(
        "Rate 1–5 stars",
        min_value=1,
        max_value=5,
        value=3,
        key="idea_rating"
    )

    # ---------- LOG RATING TO GOOGLE SHEET ----------
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        gspread_creds = GspreadCredentials.from_service_account_info(
    json.loads(st.secrets["SERVICE_ACCOUNT_JSON"]),
    scopes=scope)
        gc = gspread.authorize(gspread_creds)
        sheet = gc.open("Idea Generator Ratings").sheet1  

        if "last_rating" not in st.session_state or st.session_state.last_rating != rating:
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                rating,
                field,
                num_ideas,
                st.session_state.ideas[:200] + "..."  
            ])
            st.session_state.last_rating = rating
            st.success(f"Rating {rating}/5 logged to Sheet! ⭐")

    except Exception as log_e:
        st.warning(f"Sheet logging failed: {str(log_e)}")

    if "ratings" not in st.session_state:
        st.session_state.ratings = []
    if rating not in st.session_state.ratings:  # avoid duplicates on rerun
        st.session_state.ratings.append(rating)

    if st.session_state.ratings:
        avg = sum(st.session_state.ratings) / len(st.session_state.ratings)
        st.info(f"Local average: {avg:.2f}/5 across {len(st.session_state.ratings)} rating(s)")

    if st.button("Clear Ideas & Ratings"):
        st.session_state.clear()
        st.rerun()

    st.caption("High quality startup ideas based on practicality and real world use")

else:
    st.info("👆 Generate ideas above to see and rate them!")
