import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS

# --- KONFIGURACE ---
st.set_page_config(page_title="Professional English Master", layout="wide", page_icon="📝")

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ API key missing in Secrets!")

# --- GRAFIKA ---
st.markdown("""
    <style>
    .english-box, .dialect-box { 
        background-color: #ffffff; color: #1a202c !important; 
        padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px;
    }
    .phonetic-display { 
        background-color: #f8fafc; color: #1e293b; 
        padding: 10px; border-radius: 5px; border-left: 5px solid #3b82f6;
        font-family: monospace; font-size: 1.3rem; margin-bottom: 15px;
    }
    .english-box *, .dialect-box * { color: #1a202c !important; }
    h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# --- MOZEK AI ---
def analyze_text(text):
    system_instruction = """You are a professional English teacher specializing in active spoken English and Scottish dialects. 
    Return ONLY a JSON object with these keys: 
    original, correction, meaning (en), grammar (en), stylistic (en/scot), translation (cz), phonetic (IPA), example (en)."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- ROZHRANÍ ---
st.title("Professional English Master")

user_input = st.text_area("Zadejte text k analýze:", placeholder="Type here...", height=100)

if user_input:
    with st.spinner('Analyzing...'):
        try:
            res = analyze_text(user_input)
            
            # --- VÝSLOVNOST A FONETIKA ---
            st.subheader("Pronunciation")
            st.markdown(f"<div class='phonetic-display'>IPA: /{res['phonetic']}/</div>", unsafe_allow_html=True)
            
            # Audio (Britská angličtina)
            tts = gTTS(text=user_input, lang='en', tld='co.uk')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')
            
            st.divider()

            # --- ANALÝZA (Oprava a Překlad) ---
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Correction")
                st.success(res['correction'])
            with col2:
                st.subheader("Překlad")
                st.info(res['translation'])

            # --- GRAMATIKA A VÝZNAM ---
            st.subheader("Grammar & Meaning")
            st.markdown(f"<div class='english-box'><b>Meaning:</b> {res['meaning']}<br><br><b>Grammar:</b> {res['grammar']}</div>", unsafe_allow_html=True)

            # --- SKOTSKÝ / STYLISTICKÝ KOUTEK (Vráceno zpět) ---
            st.subheader("Stylistic & Dialect Corner")
            st.markdown(f"<div class='dialect-box'>{res['stylistic']}</div>", unsafe_allow_html=True)

            # --- ANKI EXPORT ---
            st.divider()
            csv_data = [[res['original'], res['phonetic'], "", res['meaning'], res['translation'], res['example'], "NEW"]]
            df = pd.DataFrame(csv_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Error: {e}")
