import streamlit as st
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai import init
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/service-account.json"  # Points to uploaded JSON

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
            init(project="my-project-ai-idea", location="us-central1") 

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
                    max_output_tokens=8192  # Higher for full 3 detailed ideas + SWOT
                )
            )

            ideas_md = response.text
            st.session_state.ideas = ideas_md 

            st.success("Ideas generated! 🚀")


        except Exception as e:
            st.error(f"Vertex AI error: {str(e)}")
            st.info("Fixes: Check project ID, enable Vertex AI API, or quota in console.cloud.google.com/vertex-ai")

# === PERSIST IDEAS AND SHOW RATING (outside button) ===
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

    # === LOG RATING TO GOOGLE SHEET ===
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("/secrets/service-account.json", scope)
        gc = gspread.authorize(creds)
        sheet = gc.open("Idea Generator Ratings").sheet1  

        # Log on every new rating 
        if "last_rating" not in st.session_state or st.session_state.last_rating != rating:
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                rating,
                field,
                num_ideas,
                st.session_state.ideas[:100] + "..." 
            ])
            st.session_state.last_rating = rating
            st.success(f"Rating {rating}/5 logged! ⭐")

        # Show live average from session (Sheet has full data)
        if "ratings" not in st.session_state:
            st.session_state.ratings = []
        if st.session_state.last_rating:
            st.session_state.ratings.append(rating)  # Local avg for immediate feedback

        if st.session_state.ratings:
            avg = sum(st.session_state.ratings) / len(st.session_state.ratings)
            st.info(f"Local average: {avg:.2f}/5")

    except Exception as log_e:
        st.warning(f"Logging skipped (check Sheet sharing): {str(log_e)}")

    if st.button("Clear Ideas & Ratings"):
        st.session_state.clear()
        st.rerun()

    st.caption("High quality startup ideas based on practicality and real world use")

else:
    st.info("👆 Generate ideas above to see and rate them!")
