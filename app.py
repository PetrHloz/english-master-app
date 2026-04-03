import streamlit as st
import openai
import json
import pandas as pd
import io
from gtts import gTTS

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="Professional English Master", layout="wide", page_icon="📝")

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
    </style>
""", unsafe_allow_html=True)

# --- FUNKCE PRO ANALÝZU ---
def analyze_text(text):
    system_instruction = """You are a professional English teacher specializing in active spoken English and Scottish dialects. 
    Analyze the user's text and return a JSON object with these EXACT keys: 
    "original", "correction", "meaning", "grammar", "stylistic", "translation", "phonetic", "example". 
    If a field is not applicable, use an empty string. Output ONLY the JSON."""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- HLAVNÍ UI ---
st.title("Professional English Master")
st.caption("Advanced analysis with pronunciation and dialect insights")

user_input = st.text_area("Zadejte text k analýze:", placeholder="Např.: I'm well-off...", height=100)

if user_input:
    with st.spinner('Učitel analyzuje text...'):
        try:
            res = analyze_text(user_input)
            
            # Bezpečné načtení dat (pokud klíč chybí, použije se "N/A")
            phonetic = res.get('phonetic', 'N/A')
            correction = res.get('correction', 'No changes needed.')
            translation = res.get('translation', 'N/A')
            meaning = res.get('meaning', 'N/A')
            grammar = res.get('grammar', 'N/A')
            stylistic = res.get('stylistic', 'No specific dialect notes.')
            example = res.get('example', '')

            # --- VÝSLOVNOST ---
            st.subheader("Pronunciation")
            st.markdown(f"<div class='phonetic-display'>IPA: /{phonetic}/</div>", unsafe_allow_html=True)
            
            # Audio generátor
            try:
                tts = gTTS(text=user_input, lang='en', tld='co.uk')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')
            except:
                st.warning("Audio generation is currently unavailable.")

            st.divider()

            # --- OPRAVA A PŘEKLAD ---
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Correction")
                st.success(correction)
            with col2:
                st.subheader("Překlad")
                st.info(translation)

            # --- GRAMATIKA A VÝZNAM ---
            st.subheader("Grammar & Meaning")
            st.markdown(f"<div class='english-box'><b>Meaning:</b> {meaning}<br><br><b>Grammar:</b> {grammar}</div>", unsafe_allow_html=True)

            # --- DIALEKTY A STYLISTIKA ---
            st.subheader("Stylistic & Dialect Corner")
            st.markdown(f"<div class='dialect-box'>{stylistic}</div>", unsafe_allow_html=True)

            # --- ANKI EXPORT ---
            st.divider()
            csv_data = [[res.get('original', user_input), phonetic, "", meaning, translation, example, "NEW"]]
            df = pd.DataFrame(csv_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            
            st.download_button(
                label="📥 Export for Anki (CSV)",
                data=csv_buffer.getvalue(),
                file_name="anki_export.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Omlouvám se, došlo k chybě při zpracování: {e}")
