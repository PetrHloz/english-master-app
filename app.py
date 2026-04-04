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

# Inicializace session_state
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

try:
    api_key = st.secrets.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
except:
    st.error("⚠️ API key error v Secrets!")

# --- FUNKCE ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def process_upload():
    """Funkce volaná automaticky při nahrání souboru (on_change)."""
    if st.session_state.upload_key is not None:
        with st.spinner('Automaticky čtu text z fotky...'):
            try:
                base64_img = encode_image(st.session_state.upload_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all English text from this image. Return ONLY the raw text. No intro, no apologies, no commentary."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }],
                    max_tokens=1000
                )
                txt = response.choices[0].message.content
                # Ošetření odmítnutí ze strany AI
                if "sorry" in txt.lower() or "apologize" in txt.lower() or len(txt) < 2:
                    st.session_state.ocr_text = "Chyba: AI text nerozpoznala. Zkuste jiný snímek."
                else:
                    st.session_state.ocr_text = txt
            except Exception as e:
                st.session_state.ocr_text = f"Chyba při čtení: {str(e)}"

def analyze_text(text):
    system_instruction = """MÓD MYŠLENÍ AKTIVOVÁN. Jsi elitní profesor angličtiny. 
    STRIKTNĚ SE DRŽ ZADÁNÍ. Vrať JSON: correction (<b>red tags</b>), meaning, details, stylistic, translation, phonetic, example."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def hard_clean(res_dict, key):
    val = res_dict.get(key, "")
    text = str(val).replace('*', '').strip()
    return re.sub(r'^[{\s"\']+|[}\s"\']+$', '', text)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .english-box, .dialect-box { background-color: #ffffff; color: #1a202c !important; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .correction-box { background-color: #f0fdf4; color: #166534 !important; padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0; min-height: 150px; font-size: 1.2rem; margin-bottom: 20px; }
    .correction-box b, .correction-box strong { color: #ff0000 !important; font-weight: 900 !important; }
    .phonetic-display { background-color: #f1f5f9; color: #1e293b; padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6; font-size: 1.1rem; margin-bottom: 15px; }
    .section-header { font-weight: bold; color: #1e3a8a; display: block; margin-top: 12px; font-size: 1.1rem; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# --- UI ---
st.title("Professional English Master")

# 1. Nahrávání s automatickou funkcí (on_change)
st.file_uploader("📸 Vyfoťte text nebo nahrajte obrázek", 
                 type=["jpg", "jpeg", "png"], 
                 key="upload_key", 
                 on_change=process_upload)

# 2. Hlavní zadávací pole (propojené se session_state)
# Používáme text_input/area s klíčem 'ocr_text', aby se po změně v process_upload hned přepsalo
user_input = st.text_area("Upravte text k analýze:", 
                          value=st.session_state.ocr_text, 
                          height=150)

# Tlačítko analýzy
if st.button("🚀 Spustit hloubkovou analýzu"):
    if not user_input or "Chyba:" in user_input:
        st.warning("Zadejte prosím platný text k analýze.")
    else:
        with st.spinner('Učitel analyzuje...'):
            try:
                res = analyze_text(user_input)
                
                # Zobrazení výsledků (Correction, Pronunciation atd.)
                st.subheader("Correction")
                corr = res.get('correction', '')
                display_corr = corr if corr and corr.lower() != user_input.lower() else f"✅ Correct: {user_input}"
                st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

                st.subheader("Pronunciation")
                phonetic = hard_clean(res, 'phonetic')
                st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic}/</div>", unsafe_allow_html=True)
                
                try:
                    tts = gTTS(text=user_input, lang='en', tld='co.uk')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except: pass

                with st.expander("🇨🇿 Český překlad"):
                    st.info(hard_clean(res, 'translation'))

                st.divider()

                # Detaily a Stylistika
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Grammar & Synonyms")
                    d = hard_clean(res, 'details')
                    for h in ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:']:
                        d = d.replace(h, f'<span class="section-header">{h}</span>')
                    st.markdown(f"<div class='english-box'>{d}</div>", unsafe_allow_html=True)

                with c2:
                    st.subheader("Style & Dialects")
                    s = hard_clean(res, 'stylistic')
                    for h in ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:']:
                        s = s.replace(h, f'<span class="section-header">{h}</span>')
                    st.markdown(f"<div class='dialect-box'>{s}</div>", unsafe_allow_html=True)

                # Anki export
                csv_row = [user_input, phonetic, "", hard_clean(res, 'meaning'), hard_clean(res, 'translation'), res.get('example', ''), "NEW"]
                df = pd.DataFrame([csv_row])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False, sep=";")
                st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Chyba: {e}")
