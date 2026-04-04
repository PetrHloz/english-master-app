import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS
import re
import base64

# --- KONFIGURACE ---
st.set_page_config(page_title="Professional English Master", layout="wide", page_icon="📝")

# Inicializace paměti (session state) pro text
if "user_text" not in st.session_state:
    st.session_state.user_text = ""

try:
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ API key missing in Streamlit Secrets!")
    else:
        client = openai.OpenAI(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Configuration error: {e}")

# --- POMOCNÉ FUNKCE ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_text_from_image(image_file):
    """Funkce pouze pro OCR - vytáhne text z obrázku."""
    base64_img = encode_image(image_file)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all English text from this image. Return ONLY the extracted text, no commentary."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }
        ],
        max_tokens=500
    )
    return response.choices[0].message.content

def analyze_text(text):
    """Hlavní analýza textu podle tvých železných pravidel."""
    system_instruction = """MÓD MYŠLENÍ AKTIVOVÁN. Jsi elitní profesor angličtiny. 
    STRIKTNĚ SE DRŽ ZADÁNÍ, NIC NEZJEDNODUŠUJ, NIKDY SI NEVYMÝŠLEJ. 
    Vrať JSON objekt: correction (zvýrazni chyby <b>červeně</b>), meaning, details, stylistic, translation, phonetic, example."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

def hard_clean(res_dict, key):
    val = res_dict.get(key, "")
    if isinstance(val, (dict, list)):
        if isinstance(val, dict):
            val = "<br>".join([f"{k}: {v}" for k, v in val.items()])
        else:
            val = ", ".join(map(str, val))
    text = str(val).replace('*', '').strip()
    text = re.sub(r'^[{\s"\']+|[}\s"\']+$', '', text)
    return text

# --- CSS STYLING ---
st.markdown("""
    <style>
    .english-box, .dialect-box { background-color: #ffffff; color: #1a202c !important; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .correction-box { background-color: #f0fdf4; color: #166534 !important; padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0; min-height: 150px; font-size: 1.2rem; margin-bottom: 20px; }
    .correction-box b, .correction-box strong { color: #ff0000 !important; font-weight: 900 !important; }
    .phonetic-display { background-color: #f1f5f9; color: #1e293b; padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6; font-family: 'Courier New', monospace; font-size: 1.1rem; margin-bottom: 15px; }
    .section-header { font-weight: bold; color: #1e3a8a; display: block; margin-top: 12px; font-size: 1.1rem; }
    h3 { color: #1e3a8a !important; margin-top: 20px; }
    .stButton>button { width: 100%; background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# --- UI ---
st.title("Professional English Master")

# 1. Nahrávání souboru (pokud se nahraje, přepíše session_state)
img_file = st.file_uploader("📸 Vyfoťte text / nahrajte obrázek pro OCR", type=["jpg", "jpeg", "png"])

if img_file:
    with st.spinner('Čtu text z obrázku...'):
        try:
            # Vytáhneme text a uložíme do paměti
            extracted_text = get_text_from_image(img_file)
            st.session_state.user_text = extracted_text
            st.success("Text byl úspěšně načten z obrázku. Nyní jej můžete upravit níže.")
        except Exception as e:
            st.error(f"Chyba při čtení obrázku: {e}")

# 2. Textová oblast (bere si hodnotu ze session_state)
user_input = st.text_area("Zadaný text k analýze:", 
                          value=st.session_state.user_text, 
                          placeholder="Type or use image upload above...", 
                          height=150,
                          key="main_input")

# Tlačítko pro analýzu (pracuje s tím, co je aktuálně v poli)
submit_button = st.button("🚀 Spustit hloubkovou analýzu")

if submit_button:
    if not user_input:
        st.warning("Pole pro text je prázdné.")
    else:
        with st.spinner('Učitel přemýšlí...'):
            try:
                res = analyze_text(user_input)
                
                # Zobrazení výsledků
                st.subheader("Correction")
                corr = res.get('correction', '')
                display_corr = corr if corr and corr.lower() != user_input.lower() else f"✅ Your text is correct: {user_input}"
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

                with st.expander("🇨🇿 Zobrazit český překlad"):
                    st.info(hard_clean(res, 'translation'))

                st.divider()

                st.subheader("Grammar, Synonyms & Idioms")
                details = hard_clean(res, 'details')
                for h in ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:']:
                    details = details.replace(h, f'<span class="section-header">{h}</span>')
                st.markdown(f"<div class='english-box'>{details.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

                st.subheader("Stylistic & Dialect Corner")
                stylistic = hard_clean(res, 'stylistic')
                for h in ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:']:
                    stylistic = stylistic.replace(h, f'<span class="section-header">{h}</span>')
                st.markdown(f"<div class='dialect-box'>{stylistic.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

                # Export pro Anki
                csv_row = [user_input, phonetic, "", hard_clean(res, 'meaning'), hard_clean(res, 'translation'), res.get('example', ''), "NEW"]
                df = pd.DataFrame([csv_row])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False, sep=";")
                st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Kritická chyba: {e}")
