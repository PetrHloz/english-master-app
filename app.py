import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS
import re

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
        min-height: 150px; font-size: 1.2rem; margin-bottom: 20px;
    }
    /* Červené a tučné zvýraznění opravy */
    .correction-box b, .correction-box strong { 
        color: #ff0000 !important; 
        font-weight: 900 !important; 
    }
    .phonetic-display { 
        background-color: #f1f5f9; color: #1e293b; 
        padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6;
        font-family: 'Courier New', monospace; font-size: 1.1rem; margin-bottom: 15px;
    }
    .section-header { font-weight: bold; color: #1e3a8a; display: block; margin-top: 12px; font-size: 1.1rem; }
    h3 { color: #1e3a8a !important; margin-top: 20px; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

def analyze_text(text):
    system_instruction = """You are a professional English teacher. 
    Analyze the text and return a JSON object with EXACTLY these keys:
    "correction", "meaning", "details", "stylistic", "translation", "phonetic", "example".
    
    Rules:
    - 'correction': Use <b>tags</b> to highlight corrected parts in RED.
    - 'details' & 'stylistic': Use plain headers like 'Meaning:', 'Grammar & Origin:', etc. No asterisks.
    - Return ONLY pure JSON."""
    
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
    with st.spinner('Učitel přemýšlí...'):
        try:
            res = analyze_text(user_input)
            
            def clean_text(key):
                val = res.get(key, "")
                if isinstance(val, (dict, list)): val = str(val)
                # Odstraní ošklivé závorky a uvozovky na začátku/konci
                val = re.sub(r'^[{\s"\']+|[}\s"\']+$', '', str(val))
                return val.replace('*', '').strip()

            # 1. CORRECTION
            st.subheader("Correction")
            corr = res.get('correction', '')
            if not corr or corr.lower() == user_input.lower():
                display_corr = f"✅ Your text is correct: {user_input}"
            else:
                display_corr = corr
            st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

            # 2. PRONUNCIATION
            st.subheader("Pronunciation")
            phonetic = clean_text('phonetic')
            st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic if phonetic else 'N/A'}/</div>", unsafe_allow_html=True)
            
            tts = gTTS(text=user_input, lang='en', tld='co.uk')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')

            with st.expander("🇨🇿 Zobrazit český překlad"):
                st.info(clean_text('translation'))

            st.divider()

            # 4. GRAMMAR & VARIATIONS
            st.subheader("Grammar, Synonyms & Idioms")
            details = clean_text('details')
            for h in ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:']:
                details = details.replace(h, f'<span class="section-header">{h}</span>')
            st.markdown(f"<div class='english-box'>{details.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

            # 5. DIALEKTY
            st.subheader("Stylistic & Dialect Corner")
            stylistic = clean_text('stylistic')
            for h in ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:']:
                stylistic = stylistic.replace(h, f'<span class="section-header">{h}</span>')
            st.markdown(f"<div class='dialect-box'>{stylistic.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

            # 6. ANKI EXPORT
            st.divider()
            csv_row = [user_input, phonetic, "", clean_text('meaning'), clean_text('translation'), clean_text('example'), "NEW"]
            df = pd.DataFrame([csv_row])
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba při zpracování: {e}")
