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

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ API key missing!")

# --- POMOCNÉ FUNKCE ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

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

# --- ANALÝZA ---
def analyze_content(user_text=None, image_file=None):
    system_instruction = """MÓD MYŠLENÍ AKTIVOVÁN. Jsi elitní profesor angličtiny. 
    STRIKTNĚ SE DRŽ ZADÁNÍ, NIC NEZJEDNODUŠUJ, NIKDY SI NEVYMÝŠLEJ. 
    VŽDY POUŽÍVEJ AKTUÁLNÍ DATA.
    
    Pokud dostaneš obrázek, nejdříve z něj precizně extrahuj text.
    Vrať JSON objekt:
    1. 'correction': Oprava chyb. Změny zvýrazni <b>tučně a budou červeně</b>.
    2. 'meaning': Detailní anglický význam.
    3. 'details': Meaning: [text], Grammar & Origin: [text], Synonyms & Idioms: [text].
    4. 'stylistic': Colloquial (General): [text], Common Mistake: [text], Scottish English (Scots/Informal): [text], Cultural Context: [text].
    5. 'translation': Český překlad.
    6. 'phonetic': IPA transkripce.
    7. 'example': Příkladová věta.
    8. 'original_text': Extrahovaný text (pouze u obrázků)."""

    messages = [{"role": "system", "content": system_instruction}]
    
    if image_file:
        base64_img = encode_image(image_file)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract and analyze text from this image strictly following the rules."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- UI ---
st.title("Professional English Master")

# Primární vstup je text
user_input = st.text_area("Zadejte text k analýze:", placeholder="Type or paste here...", height=150)

# Volitelný vstup je obrázek/foto
img_file = st.file_uploader("Nebo vyfoťte text / nahrajte obrázek", type=["jpg", "jpeg", "png"])

if img_file:
    st.image(img_file, caption="Snímek k analýze", use_container_width=True, width=300)

submit_button = st.button("🚀 Spustit hloubkovou analýzu")

if submit_button:
    if not user_input and not img_file:
        st.warning("Prosím zadejte text nebo nahrajte obrázek.")
    else:
        with st.spinner('Probíhá analýza v módu myšlení...'):
            try:
                res = analyze_content(user_text=user_input, image_file=img_file)
                
                # Zjištění, který text použít pro audio a export (priorita má obrázek, pak text)
                source_text = res.get('original_text', user_input) if img_file else user_input

                # 1. CORRECTION
                st.subheader("Correction")
                corr = res.get('correction', '')
                if not corr or (user_input and corr.lower() == user_input.lower()):
                    display_corr = f"✅ Your text is correct: {source_text}"
                else:
                    display_corr = corr
                st.markdown(f"<div class='correction-box'>{display_corr}</div>", unsafe_allow_html=True)

                # 2. PRONUNCIATION
                st.subheader("Pronunciation")
                phonetic = hard_clean(res, 'phonetic')
                st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic}/</div>", unsafe_allow_html=True)
                
                try:
                    tts = gTTS(text=source_text, lang='en', tld='co.uk')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                except: pass

                with st.expander("🇨🇿 Zobrazit český překlad"):
                    st.info(hard_clean(res, 'translation'))

                st.divider()

                # 4. GRAMMAR & VARIATIONS
                st.subheader("Grammar, Synonyms & Idioms")
                details = hard_clean(res, 'details')
                for h in ['Meaning:', 'Grammar & Origin:', 'Synonyms & Idioms:']:
                    details = details.replace(h, f'<span class="section-header">{h}</span>')
                st.markdown(f"<div class='english-box'>{details.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

                # 5. DIALEKTY
                st.subheader("Stylistic & Dialect Corner")
                stylistic = hard_clean(res, 'stylistic')
                for h in ['Colloquial (General):', 'Common Mistake:', 'Scottish English (Scots/Informal):', 'Cultural Context:']:
                    stylistic = stylistic.replace(h, f'<span class="section-header">{h}</span>')
                st.markdown(f"<div class='dialect-box'>{stylistic.replace('\\n', '<br>').replace('\n', '<br>')}</div>", unsafe_allow_html=True)

                # 6. ANKI EXPORT
                st.divider()
                csv_row = [source_text, phonetic, "", hard_clean(res, 'meaning'), hard_clean(res, 'translation'), res.get('example', ''), "NEW"]
                df = pd.DataFrame([csv_row])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False, sep=";")
                st.download_button("📥 Export for Anki", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Kritická chyba: {e}")
