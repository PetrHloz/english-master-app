import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="English Master", layout="wide", page_icon="📝")

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ API key missing in Streamlit Secrets!")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .english-box, .dialect-box { 
        background-color: #ffffff; color: #1a202c !important; 
        padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px;
    }
    .phonetic-display { 
        background-color: #f1f5f9; color: #1e293b; 
        padding: 12px; border-radius: 8px; border-left: 5px solid #3b82f6;
        font-family: 'Courier New', monospace; font-size: 1.3rem; margin-bottom: 15px;
    }
    .english-box * { color: #1a202c !important; }
    h3 { color: #1e3a8a !important; margin-top: 20px; }
    /* Styl pro tlačítko, aby bylo na mobilu výrazné */
    .stButton>button {
        width: 100%;
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKCE PRO ANALÝZU ---
def analyze_text(text):
    system_instruction = """You are a professional English teacher. 
    Analyze the text and return a JSON object.
    1. 'translation' must be ONLY in Czech.
    2. 'grammar' section MUST include: Grammar notes, Synonyms, Idioms, and Alternative expressions.
    Use Markdown inside JSON strings."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- HLAVNÍ UI ---
st.title("Professional English Master")

user_input = st.text_area("Zadejte text k analýze:", placeholder="Type here...", height=150)

# PŘIDÁNÍ TLAČÍTKA PRO MOBILNÍ ZAŘÍZENÍ
submit_button = st.button("🚀 Analyzovat text")

# Analýza se spustí, pokud je stisknuto tlačítko NEBO pokud uživatel použije Ctrl+Enter (Streamlit default)
if submit_button and user_input:
    with st.spinner('Učitel připravuje rozbor...'):
        try:
            res = analyze_text(user_input)
            
            def g(key, default="N/A"):
                val = res.get(key, default)
                return val if val else default

            # --- VÝSLOVNOST ---
            st.subheader("Pronunciation")
            st.markdown(f"<div class='phonetic-display'>IPA: /{g('phonetic')}/</div>", unsafe_allow_html=True)
            
            try:
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            except:
                st.warning("Audio unavailable.")

            st.divider()

            # --- OPRAVA A PŘEKLAD ---
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Correction")
                st.success(g('correction'))
            with col2:
                st.subheader("🇨🇿 Překlad")
                st.info(g('translation'))

            # --- ROZŠÍŘENÁ GRAMATIKA ---
            st.subheader("Grammar, Synonyms & Idioms")
            st.markdown(f"""
                <div class='english-box'>
                    <b>Meaning:</b><br>{g('meaning')}<br><br>
                    <b>Details & Variations:</b><br>{g('grammar')}
                </div>
            """, unsafe_allow_html=True)

            # --- DIALEKTY ---
            st.subheader("Stylistic & Dialect Corner")
            st.markdown(f"<div class='dialect-box'>{g('stylistic')}</div>", unsafe_allow_html=True)

            # --- ANKI EXPORT ---
            st.divider()
            csv_row = [g('original', user_input), g('phonetic'), "", g('meaning'), g('translation'), g('example'), "NEW"]
            df = pd.DataFrame([csv_row])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba: {e}")
elif submit_button and not user_input:
    st.warning("Nejdříve prosím zadejte nějaký text.")
