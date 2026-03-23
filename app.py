import re
import streamlit as st
import PyPDF2
from groq import Groq

# ─── API Anahtarı ─────────────────────────────────────────────────────────────
GROQ_API_KEY = "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"

# ─── Sayfa Yapılandırması ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI CV Career Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f0f1a; color: #cdd6f4; }
    .hero-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #16213e 50%, #0d1b2a 100%);
        border: 1px solid #313244;
        border-radius: 18px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero-card h1 { font-size: 2.4rem; margin: 0; color: #cba6f7; }
    .hero-card p  { color: #a6adc8; margin-top: 0.5rem; font-size: 1.05rem; }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 700;
        width: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.45);
    }
    .score-badge { font-size: 3.5rem; font-weight: 900; line-height: 1; }
    [data-testid="stSidebar"] { background: #12121f; }
</style>
""", unsafe_allow_html=True)

# ─── Dil Seçimi ──────────────────────────────────────────────────────────────
lang = st.radio(
    "",
    options=["🇹🇷 Türkçe", "🇬🇧 English"],
    horizontal=True,
    label_visibility="collapsed",
)
TR = lang == "🇹🇷 Türkçe"

# ─── Metin Sözlüğü ───────────────────────────────────────────────────────────
T = {
    "title":        "🎯 AI CV Kariyer Koçu"          if TR else "🎯 AI CV Career Coach",
    "subtitle":     "CV'nizi yükleyin · Pozisyonunuzu belirtin · Kariyer yolunuzu çizin"
                    if TR else
                    "Upload your CV · Enter your target role · Map your career path",
    "upload":       "📄 CV'nizi Yükleyin (PDF formatında)"
                    if TR else "📄 Upload Your CV (PDF format)",
    "upload_help":  "Sadece metin tabanlı PDF desteklenir."
                    if TR else "Only text-based PDFs are supported.",
    "position":     "🎯 Hedeflediğiniz Pozisyon"
                    if TR else "🎯 Target Position",
    "position_ph":  "Örn: Junior Backend Developer, Veri Bilimci..."
                    if TR else "E.g: Junior Backend Developer, Data Scientist...",
    "button":       "🚀 Kariyer Yolumu Çiz!"
                    if TR else "🚀 Map My Career Path!",
    "no_file":      "⚠️ Lütfen PDF formatında bir CV yükleyin."
                    if TR else "⚠️ Please upload a CV in PDF format.",
    "no_pos":       "⚠️ Lütfen hedeflediğiniz pozisyonu girin."
                    if TR else "⚠️ Please enter your target position.",
    "reading":      "📖 CV okunuyor..."
                    if TR else "📖 Reading CV...",
    "pdf_error":    "❌ PDF'den yeterli metin okunamadı. Metin tabanlı bir PDF kullandığınızdan emin olun."
                    if TR else "❌ Could not extract enough text from the PDF. Make sure it's a text-based PDF.",
    "analyzing":    "🤖 AI analiz yapıyor... (5–10 saniye)"
                    if TR else "🤖 AI is analyzing... (5–10 seconds)",
    "api_error":    "❌ Groq API Hatası: "
                    if TR else "❌ Groq API Error: ",
    "api_hint":     "💡 Kota aşımı veya ağ sorunu olabilir. Birkaç saniye bekleyip tekrar deneyin."
                    if TR else "💡 Possible quota limit or network issue. Wait a moment and try again.",
    "success":      "✅ Analiz tamamlandı!"
                    if TR else "✅ Analysis complete!",
    "sec1":         "📊 ATS Uyumluluğu"          if TR else "📊 ATS Compatibility",
    "sec2":         "🔴 Kritik Eksikler"           if TR else "🔴 Critical Gaps",
    "sec3":         "✏️ STAR Tekniği ile Revizyon" if TR else "✏️ STAR Technique Revision",
    "sec4":         "💡 Fark Yaratacak Proje"      if TR else "💡 Stand-Out Project Idea",
    "orig":         "**Orijinal Zayıf İfade:**"    if TR else "**Original Weak Statement:**",
    "revised":      "**STAR ile Güçlendirilmiş Hali:**"
                    if TR else "**Strengthened with STAR:**",
    "parse_fail":   "Bu bölüm ayrıştırılamadı."   if TR else "This section could not be parsed.",
    "debug":        "🔧 Ham API Çıktısı"           if TR else "🔧 Raw API Output",
}

# ─── Hero Başlık ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-card">
    <h1>{T['title']}</h1>
    <p>{T['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# ─── Giriş Alanları ──────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")
with col1:
    uploaded_file = st.file_uploader(T["upload"], type=["pdf"], help=T["upload_help"])
with col2:
    target_position = st.text_input(T["position"], placeholder=T["position_ph"])

st.markdown("---")


# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

def extract_pdf_text(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages_text).strip() or None
    except Exception as exc:
        st.error(f"❌ PDF okunamadı: {exc}")
        return None


def build_prompt(cv_text: str, position: str) -> str:
    if TR:
        return f"""Sen deneyimli bir İK uzmanı ve kariyer koçusun. Aşağıdaki CV'yi verilen pozisyon için analiz et.

===CV İÇERİĞİ===
{cv_text}
===SON===

Hedeflenen Pozisyon: {position}

ÇIKTI FORMATINI TAM OLARAK AŞAĞIDAKİ GİBİ KULLAN (başlıkları değiştirme):

## ATS_SCORE
[0-100 arası sayısal puan] | [Tek satır özet yorum]

## ATS_DETAILS
[ATS uyumluluğu hakkında 3-5 cümle. Anahtar kelimeler, biçimlendirme, bölüm başlıkları, okunabilirlik.]

## KRITIK_EKSIKLER
- [Eksik Yetkinlik 1]: [Bu pozisyon için neden kritik]
- [Eksik Yetkinlik 2]: [Bu pozisyon için neden kritik]
- [Eksik Yetkinlik 3]: [Bu pozisyon için neden kritik]
- [Eksik Yetkinlik 4]: [Bu pozisyon için neden kritik]

## ZAYIF_CUMLE
[CV'den aynen kopyala: zayıf, ölçümsüz tek bir cümle]

## STAR_REVIZE
**Situation (Durum):** [Bağlamı kısaca açıkla]
**Task (Görev):** [Üstlenilen sorumluluğu belirt]
**Action (Eylem):** [Atılan somut adımlar]
**Result (Sonuç):** [Ölçülebilir çıktı, örn. "%20 hız artışı"]

## PROJE_TAVSIYE
**Proje Adı:** [Özgün isim]
**Açıklama:** [2-3 cümle açıklama]
**Teknolojiler:** [Virgülle ayrılmış liste]
**Fark Yaratacak Nokta:** [CV'ye ve söyleşilere katkısı — 2 cümle]"""
    else:
        return f"""You are an experienced HR specialist and career coach. Analyze the CV below for the given target position.

===CV CONTENT===
{cv_text}
===END===

Target Position: {position}

USE EXACTLY THE FOLLOWING OUTPUT FORMAT (do not change section headers):

## ATS_SCORE
[Numeric score 0-100] | [One-line summary comment]

## ATS_DETAILS
[3-5 sentences on ATS compatibility: keywords, formatting, section headers, readability.]

## KRITIK_EKSIKLER
- [Missing Skill 1]: [Why it's critical for this role]
- [Missing Skill 2]: [Why it's critical for this role]
- [Missing Skill 3]: [Why it's critical for this role]
- [Missing Skill 4]: [Why it's critical for this role]

## ZAYIF_CUMLE
[Copy verbatim from CV: one weak, unmeasured statement]

## STAR_REVIZE
**Situation:** [Briefly describe the context]
**Task:** [Describe the responsibility taken]
**Action:** [List concrete steps taken]
**Result:** [Measurable outcome, e.g. "20% speed improvement"]

## PROJE_TAVSIYE
**Project Name:** [Creative name]
**Description:** [2-3 sentence description]
**Technologies:** [Comma-separated list]
**Why It Stands Out:** [How it benefits the CV and interviews — 2 sentences]"""


def analyze_cv(cv_text: str, position: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": build_prompt(cv_text, position)}],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def parse_section(text: str, section: str):
    marker = f"## {section}"
    start = text.find(marker)
    if start == -1:
        return None
    nl = text.find("\n", start)
    if nl == -1:
        return None
    start = nl + 1
    end = text.find("## ", start)
    return text[start: end if end != -1 else len(text)].strip() or None


# ─── Analiz Butonu ────────────────────────────────────────────────────────────
if st.button(T["button"], use_container_width=True):

    if not uploaded_file:
        st.warning(T["no_file"])
        st.stop()
    if not target_position.strip():
        st.warning(T["no_pos"])
        st.stop()

    with st.spinner(T["reading"]):
        cv_text = extract_pdf_text(uploaded_file)

    if not cv_text or len(cv_text) < 80:
        st.error(T["pdf_error"])
        st.stop()

    with st.spinner(T["analyzing"]):
        try:
            raw_result = analyze_cv(cv_text, target_position.strip())
        except Exception as exc:
            st.error(T["api_error"] + str(exc))
            st.info(T["api_hint"])
            st.stop()

    st.success(T["success"])
    st.markdown("---")

    # ── 1. ATS Skoru ──────────────────────────────────────────────────────────
    ats_score_raw = parse_section(raw_result, "ATS_SCORE")
    ats_details   = parse_section(raw_result, "ATS_DETAILS")

    with st.expander(T["sec1"], expanded=True):
        if ats_score_raw:
            parts   = ats_score_raw.split("|", 1)
            score   = parts[0].strip()
            summary = parts[1].strip() if len(parts) > 1 else ""
            match = re.search(r'\d+', score)
            score_int = int(match.group()) if match else 0
            color = "#a6e3a1" if score_int >= 70 else ("#f9e2af" if score_int >= 50 else "#f38ba8")
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<span class='score-badge' style='color:{color};'>{score}</span>"
                    f"<br><small style='color:#a6adc8;'>/ 100</small></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                if summary:
                    st.markdown(f"**{summary}**")
                if ats_details:
                    st.markdown(ats_details)
        else:
            st.info(T["parse_fail"])

    # ── 2. Kritik Eksikler ────────────────────────────────────────────────────
    eksikler = parse_section(raw_result, "KRITIK_EKSIKLER")
    with st.expander(T["sec2"], expanded=True):
        if eksikler:
            st.markdown(eksikler)
        else:
            st.info(T["parse_fail"])

    # ── 3. STAR Revizyonu ─────────────────────────────────────────────────────
    zayif = parse_section(raw_result, "ZAYIF_CUMLE")
    star  = parse_section(raw_result, "STAR_REVIZE")
    with st.expander(T["sec3"], expanded=True):
        if zayif:
            st.markdown(T["orig"])
            st.error(f'❌ *"{zayif}"*')
        if star:
            st.markdown(T["revised"])
            st.success(star)
        if not zayif and not star:
            st.info(T["parse_fail"])

    # ── 4. Proje Tavsiyesi ────────────────────────────────────────────────────
    proje = parse_section(raw_result, "PROJE_TAVSIYE")
    with st.expander(T["sec4"], expanded=True):
        if proje:
            st.markdown(proje)
        else:
            st.info(T["parse_fail"])

    # ── Ham Çıktı (Debug) ─────────────────────────────────────────────────────
    with st.expander(T["debug"], expanded=False):
        st.code(raw_result, language="markdown")
