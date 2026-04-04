import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS
import re
import base64

# --- KONFIGURACE ---
st.set_page_config(page_title="English Master PRO", layout="wide", page_icon="📝")

if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

try:
    api_key = st.secrets.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
except:
    st.error("⚠️ API key error!")

# --- FUNKCE PRO OCR ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def process_upload():
    if st.session_state.upload_key is not None:
        try:
            base64_img = encode_image(st.session_state.upload_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all English text from this image. Return ONLY the raw text. No intro, no apologies."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }]
            )
            st.session_state.ocr_text = response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"OCR Error: {e}")

# --- ANALÝZA (ZDE JSOU TVÁ ŽELEZNÁ PRAVIDLA) ---
def analyze_text(text):
    system_instruction = """MÓD MYŠLENÍ AKTIVOVÁN. Jsi elitní profesor angličtiny. 
    STRIKTNĚ SE DRŽ ZADÁNÍ, NIC NEZJEDNODUŠUJ.
    Musíš vrátit JSON objekt s těmito klíči:
    "correction": [text s <b>červenými tagy</b> pro chyby],
    "meaning": [stručný význam],
    "details": "Meaning: [text]\\nGrammar & Origin: [text]\\nSynonyms & Idioms: [text]",
    "stylistic": "Colloquial (General): [text]\\nCommon Mistake: [text]\\nScottish English (Scots/Informal): [text]\\nCultural Context: [text]",
    "translation": [česky],
    "phonetic": [IPA],
    "example": [věta]"
    NIKDY nepoužívej hvězdičky ani uvozovky pro názvy sekcí uvnitř polí."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def clean_output(text, headers):
    # Odstraní hvězdičky a vyčistí balast
    text = str(text).replace('*', '').strip()
    text = re.sub(r'^[{\s"\']+|[}\s"\']+$', '', text)
    # Formátování nadpisů
    for h in headers:
        # Zachytí nadpis i s případnými uvozovkami kolem něj
        pattern = rf'["\']?{re.escape(h)}["\']?'
        text = re.sub(pattern, f'<span class="section-header">{h}</span>', text)
    return text.replace('\n', '<br>')

# --- CSS ---
st.markdown("""
    <style>
    .english-box, .dialect-box { background-color: #ffffff; color: #1a202c !important; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px; min-height: 200px; }
    .correction-box { background-color: #f0fdf4; color: #166534 !important; padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0; font-size: 1.2rem; margin-bottom: 20px; }
    .correction-box b, .correction-box strong { color: #ff0000 !important; font-weight: 900 !important; }
    .phonetic-display { background-color: #f1f5f9; color: #1e293b; padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6; font-size: 1.1rem; margin-bottom: 15px; }
    .section-header { font-weight: bold; color: #1e3a8a; display: block; margin-top: 12px; font-size: 1.1rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px; margin-bottom: 5px; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# --- UI ---
st.title("Professional English Master PRO")

st.file_uploader("📸 Vyfoťte text nebo nahrajte obrázek", type=["jpg", "jpeg", "png"], key="upload_key", on_change=process_upload)

user_input = st.text_area("Upravte text k analýze:", value=st.session_state.ocr_text, height=150)

if st.button("🚀 Spustit hloubkovou analýzu"):
    if user_input:
        with st.spinner('Učitel analyzuje v módu myšlení...'):
            try:
                res = analyze_text(user_input)
                
                # 1. CORRECTION
                st.subheader("Correction")
                corr = res.get('correction', '')
                display_corr = corr if corr and corr.lower() != user_input.lower() else f"✅ Correct: {user_input}"
                st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

                # 2. PRONUNCIATION
                st.subheader("Pronunciation")
                phonetic = str(res.get('phonetic', 'N/A')).replace('*', '')
                st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic}/</div>", unsafe_allow_html=True)
                
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')

                with st.expander("🇨🇿 Český překlad"):
                    st.info(res.get('translation', 'N/A'))

                st.divider()

                # 3. DETAILS & STYLISTIC
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Grammar & Synonyms")
                    d_raw = res.get('details', '')
                    d_clean = clean_output(d_raw, ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:'])
                    st.markdown(f"<div class='english-box'>{d_clean}</div>", unsafe_allow_html=True)

                with col2:
                    st.subheader("Style & Dialects")
                    s_raw = res.get('stylistic', '')
                    s_clean = clean_output(s_raw, ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:'])
                    st.markdown(f"<div class='dialect-box'>{s_clean}</div>", unsafe_allow_html=True)

                # 4. ANKI
                csv_row = [user_input, phonetic, "", res.get('meaning', ''), res.get('translation', ''), res.get('example', ''), "NEW"]
                df = pd.DataFrame([csv_row])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False, sep=";")
                st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Chyba: {e}")
