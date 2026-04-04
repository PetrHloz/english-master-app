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
    .section-header { font-weight: bold; color: #1e3a8a; display: block; margin-top: 10px; font-size: 1.1rem; }
    h3 { color: #1e3a8a !important; margin-top: 20px; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def analyze_text(text):
    system_instruction = """You are a top-tier English teacher.
    Analyze the text and return a JSON object with EXACTLY these keys:
    "original", "correction", "meaning", "details", "stylistic", "translation", "phonetic", "example".
    
    Rules for 'details':
    Format exactly like this (no asterisks):
    Meaning: [text]
    Grammar & Origin: [text]
    Synonyms & Idioms: [text]
    
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
            
            # Bezpečná funkce pro zpracování jakéhokoli výstupu z AI
            def safe_get(key):
                data = res.get(key, "")
                if isinstance(data, list): return ", ".join(map(str, data))
                if isinstance(data, dict): return str(data)
                return str(data).strip()

            # 1. CORRECTION
            st.subheader("Correction")
            corr = safe_get('correction')
            if not corr or corr.lower() == user_input.lower():
                display_corr = f"✅ Your text is correct: **{user_input}**"
            else:
                display_corr = corr
            st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

            # 2. PRONUNCIATION
            st.subheader("Pronunciation")
            phonetic = safe_get('phonetic')
            st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic if phonetic else 'N/A'}/</div>", unsafe_allow_html=True)
            
            try:
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            except:
                st.warning("Audio unavailable.")

            # 3. PŘEKLAD
            with st.expander("🇨🇿 Zobrazit český překlad"):
                st.info(safe_get('translation'))

            st.divider()

            # 4. GRAMMAR, SYNONYMS & IDIOMS
            st.subheader("Grammar, Synonyms & Idioms")
            details = safe_get('details').replace('*', '')
            formatted_details = details.replace('Meaning:', '<span class="section-header">Meaning:</span>')\
                                       .replace('Grammar & Origin:', '<span class="section-header">Grammar & Origin:</span>')\
                                       .replace('Synonyms & Idioms:', '<span class="section-header">Synonyms & Idioms:</span>')
            
            st.markdown(f"""
                <div class='english-box'>
                    {formatted_details.replace('\n', '<br>')}
                </div>
            """, unsafe_allow_html=True)

            # 5. DIALEKTY
            st.subheader("Stylistic & Dialect Corner")
            st.markdown(f"<div class='dialect-box'>{safe_get('stylistic').replace('*', '')}</div>", unsafe_allow_html=True)

            # 6. ANKI
            st.divider()
            csv_row = [user_input, phonetic, "", safe_get('meaning'), safe_get('translation'), safe_get('example'), "NEW"]
            df = pd.DataFrame([csv_row])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba při zpracování: {e}")
