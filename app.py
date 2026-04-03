import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS # Nová knihovna pro výslovnost

# --- KONFIGURACE ---
st.set_page_config(page_title="Professional English Master", layout="wide", page_icon="🏴󠁧󠁢󠁳󠁣󠁴󠁿")

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ Chybí API klíč v Secrets!")

# --- GRAFIKA ---
st.markdown("""
    <style>
    .english-box, .scottish-box { 
        background-color: #ffffff; color: #1a202c !important; 
        padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 15px;
    }
    .phonetic-text { color: #4a5568; font-style: italic; font-size: 1.2rem; margin-top: -10px; margin-bottom: 10px; }
    .english-box *, .scottish-box * { color: #1a202c !important; }
    </style>
""", unsafe_allow_html=True)

# --- MOZEK AI ---
def analyze_text(text):
    system_instruction = """Jsi profesionální učitel angličtiny. 
    Vrať JSON: original, correction, meaning (en), grammar (en), stylistic (en/scot), translation (cz), phonetic (IPA), example (en)."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- ROZHRANÍ ---
st.title("🏴󠁧󠁢󠁳󠁣󠁴󠁿 Professional English Master")

user_input = st.text_area("Zadejte text k analýze:", placeholder="I didn't saw him...", height=100)

if user_input:
    with st.spinner('Učitel připravuje rozbor a výslovnost...'):
        try:
            res = analyze_text(user_input)
            
            # --- NOVÁ SEKCE: FONETIKA A HLAS ---
            st.markdown(f"<div class='phonetic-text'>[{res['phonetic']}]</div>", unsafe_allow_html=True)
            
            col_audio, col_link = st.columns([1, 4])
            with col_audio:
                # Generování audia přes Google TTS
                tts = gTTS(text=user_input, lang='en', tld='co.uk') # Britská angličtina
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            
            with col_link:
                # Odkaz na Cambridge Dictionary pro detailní studium
                search_term = user_input.split()[0] if len(user_input.split()) > 0 else ""
                st.markdown(f"[🔍 Detailní výslovnost na Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/{search_term})")

            # --- ZBYTEK ANALÝZY ---
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("✅ Correction")
                st.success(res['correction'])
            with c2:
                st.subheader("🇨🇿 Překlad")
                st.info(res['translation'])

            st.subheader("🧠 Grammar & Meaning")
            st.markdown(f"<div class='english-box'><b>Meaning:</b> {res['meaning']}<br><br><b>Grammar:</b> {res['grammar']}</div>", unsafe_allow_html=True)

            st.subheader("🏴󠁧󠁢󠁳󠁣󠁴󠁿 Stylistic & Scottish Corner")
            st.markdown(f"<div class='scottish-box'>{res['stylistic']}</div>", unsafe_allow_html=True)

            # ANKI EXPORT
            csv_data = [[res['original'], res['phonetic'], "", res['meaning'], res['translation'], res['example'], "NEW"]]
            df = pd.DataFrame(csv_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            st.download_button("📥 Stáhnout pro Anki (CSV)", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba: {e}")
