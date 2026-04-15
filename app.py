import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS
import re
import base64

# --- KONFIGURACE ---
st.set_page_config(page_title="Professional English Master PRO", layout="wide", page_icon="📝")

# Inicializace paměti pro OCR text
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
    """Automatické vytažení textu z fotky při nahrání."""
    if st.session_state.upload_key is not None:
        try:
            base64_img = encode_image(st.session_state.upload_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all English text from this image. Return ONLY raw text. No chatter."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }]
            )
            st.session_state.ocr_text = response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"OCR Error: {e}")

# --- ANALÝZA (HLOUBKOVÝ MÓD MYŠLENÍ) ---
def analyze_text(text):
    system_instruction = """MÓD MYŠLENÍ AKTIVOVÁN. Jsi elitní lingvista. STRIKTNĚ SE DRŽ ZADÁNÍ, NIC NEZJEDNODUŠUJ.
    Vrať JSON objekt s těmito klíči:
    "correction": [text s <b>červenými tagy</b> pro chyby],
    "meaning": [stručný význam],
    "details": "Meaning: [hluboký rozbor]\\nGrammar & Origin: [komplexní gramatika a etymologie]\\nSynonyms & Idioms: [seznam]",
    "stylistic": "Colloquial (General): [US/UK slang]\\nCommon Mistake: [chyby]\\nScottish English (Scots/Informal): [autentické skotské verze]\\nCultural Context: [skotský/britský kontext]",
    "translation": [česky],
    "phonetic": [IPA],
    "example": [věta]"
    NIKDY nepoužívej hvězdičky pro nadpisy sekcí uvnitř polí."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def clean_output(text, headers):
    text = str(text).replace('*', '').strip()
    text = re.sub(r'^[{\s"\']+|[}\s"\']+$', '', text)
    for h in headers:
        pattern = rf'["\']?{re.escape(h)}["\']?'
        text = re.sub(pattern, f'<span class="section-header">{h}</span>', text)
    return text.replace('\n', '<br>')

# --- CSS STYLING ---
st.markdown("""
    <style>
    /* Zmenšení výšky boxu pro nahrávání souborů */
.stFileUploader section {
    padding: 0;
    min-height: 80px;
}
/* Zmenšení textu uvnitř boxu (Drop files here) */
.stFileUploader section div div {
    font-size: 0.8rem;
}

    .english-box, .dialect-box { 
        background-color: #ffffff; color: #1a202c !important; 
        padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; 
        margin-bottom: 25px; width: 100%;
    }
    .correction-box { 
        background-color: #f0fdf4; color: #166534 !important; 
        padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0; 
        font-size: 1.2rem; margin-bottom: 20px; 
    }
    .correction-box b { color: #ff0000 !important; font-weight: 900 !important; }
    .phonetic-display { 
        background-color: #f1f5f9; color: #1e293b; padding: 10px; 
        border-radius: 8px; border-left: 5px solid #3b82f6; font-size: 1.1rem; 
    }
    .section-header { 
        font-weight: bold; color: #1e3a8a; display: block; 
        margin-top: 15px; font-size: 1.1rem; border-bottom: 1px solid #e2e8f0; 
        padding-bottom: 3px; margin-bottom: 8px;
    }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; height: 3.5em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- UI ROZHRANÍ ---
st.title("Professional English Master PRO")

# OCR Vstup
st.file_uploader("📸 nahraj obrázek", type=["jpg", "jpeg", "png"], key="upload_key", on_change=process_upload,label_visibility="collapsed")

# Zadávací pole
user_input = st.text_area("Upravte text k analýze:", value=st.session_state.ocr_text, height=100)
if st.button("🚀 Spustit hloubkovou analýzu"):
    if user_input:
        with st.spinner('Učitel analyzuje v módu myšlení...'):
            try:
                res = analyze_text(user_input)
                
                # 1. CORRECTION (Hned pod tlačítkem)
                st.subheader("Correction")
                corr = res.get('correction', '')
                display_corr = corr if corr and corr.lower() != user_input.lower() else f"✅ Correct: {user_input}"
                st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

                # 2. PRONUNCIATION
                st.subheader("Pronunciation")
                phon = str(res.get('phonetic', 'N/A')).replace('*', '')
                st.markdown(f"<div class='phonetic-display'>/{phon}/</div>", unsafe_allow_html=True)
                
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')

                with st.expander("🇨🇿 Zobrazit český překlad"):
                    st.info(res.get('translation', 'N/A'))

                st.divider()

                # 3. GRAMMAR, SYNONYMS & IDIOMS (Na celou šířku)
                st.subheader("Grammar, Synonyms & Idioms")
                d_clean = clean_output(res.get('details', ''), ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:'])
                st.markdown(f"<div class='english-box'>{d_clean}</div>", unsafe_allow_html=True)

                # 4. STYLISTIC & DIALECT CORNER (Na celou šířku pod tím)
                st.subheader("Stylistic & Dialect Corner")
                s_clean = clean_output(res.get('stylistic', ''), ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:'])
                st.markdown(f"<div class='dialect-box'>{s_clean}</div>", unsafe_allow_html=True)

                # 5. ANKI EXPORT
                csv_row = [user_input, phon, "", res.get('meaning', ''), res.get('translation', ''), res.get('example', ''), "NEW"]
                df = pd.DataFrame([csv_row])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False, sep=";")
                st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Chyba: {e}")
