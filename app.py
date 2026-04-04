import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS

# --- KONFIGURACE ---
st.set_page_config(page_title="English Master", layout="wide", page_icon="📝")

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ API key missing!")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .english-box, .dialect-box { 
        background-color: #ffffff; color: #1a202c !important; 
        padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px;
    }
    .correction-box {
        background-color: #f0fdf4; color: #166534 !important;
        padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0;
        min-height: 150px; font-size: 1.1rem; margin-bottom: 20px;
    }
    .phonetic-display { 
        background-color: #f1f5f9; color: #1e293b; 
        padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6;
        font-family: 'Courier New', monospace; 
        font-size: 1.1rem; margin-bottom: 15px;
    }
    .english-box * { color: #1a202c !important; }
    h3 { color: #1e3a8a !important; margin-top: 20px; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def analyze_text(text):
    system_instruction = """You are a top-tier English teacher and linguist.
    Analyze the text and return a JSON object with EXACTLY these keys:
    "original", "correction", "meaning", "details", "stylistic", "translation", "phonetic", "example".
    'translation' MUST be only in Czech."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- UI ---
st.title("Professional English Master")
user_input = st.text_area("Zadejte text k analýze:", placeholder="Type here...", height=150)
submit_button = st.button("🚀 Analyzovat text")

if submit_button and user_input:
    with st.spinner('Analyzuji...'):
        try:
            res = analyze_text(user_input)
            
            def get_data(key):
                return res.get(key, "Information not available")

            # 1. CORRECTION
            st.subheader("Correction")
            st.markdown(f"<div class='correction-box'>{get_data('correction')}</div>", unsafe_allow_html=True)

            # 2. PRONUNCIATION
            st.subheader("Pronunciation")
            phonetic = get_data('phonetic')
            st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic}/</div>", unsafe_allow_html=True)
            
            try:
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            except:
                st.warning("Audio unavailable.")

            # 3. SKRYTÝ PŘEKLAD (Nyní hned pod výslovností)
            with st.expander("🇨🇿 Zobrazit český překlad"):
                st.info(get_data('translation'))

            st.divider()

            # 4. GRAMMAR, SYNONYMS & IDIOMS
            st.subheader("Grammar, Synonyms & Idioms")
            st.markdown(f"""
                <div class='english-box'>
                    <b>Meaning:</b><br>{get_data('meaning')}<br><br>
                    <b>Details & Variations:</b><br>{get_data('details')}
                </div>
            """, unsafe_allow_html=True)

            # 5. DIALEKTY
            st.subheader("Stylistic & Dialect Corner")
            st.markdown(f"<div class='dialect-box'>{get_data('stylistic')}</div>", unsafe_allow_html=True)

            # 6. ANKI
            st.divider()
            csv_row = [user_input, phonetic, "", get_data('meaning'), get_data('translation'), get_data('example'), "NEW"]
            df = pd.DataFrame([csv_row])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba při zpracování: {e}")
