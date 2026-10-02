import streamlit as st
from openai import OpenAI
from PIL import Image
import re
import base64

# =========================================================
# SAYFA AYARLARI
# =========================================================
st.set_page_config(page_title="meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu", page_icon="✨", layout="wide")

# =========================================================
# ŞİFRE KORUMASI
# =========================================================
def check_password():
    def password_entered():
        correct = st.secrets.get("APP_PASSWORD", "")
        if st.session_state.get("password_input", "") == correct and correct != "":
            st.session_state["password_ok"] = True
            st.session_state["password_input"] = ""
        else:
            st.session_state["password_ok"] = False

    if st.session_state.get("password_ok", False):
        return True

    st.markdown("### 🔒 Bu araç şifre korumalı")
    st.text_input("Şifre:", type="password", key="password_input", on_change=password_entered)

    if "password_ok" in st.session_state and st.session_state["password_ok"] is False:
        st.error("Şifre yanlış, tekrar dene.")

    return False

if not check_password():
    st.stop()

# =========================================================
# MODEL (GROQ)
# =========================================================
MODEL_NAME = "qwen/qwen3.8-27b"

# =========================================================
# HAFIZA (Session State)
# =========================================================
if "boyutlar" not in st.session_state:
    st.session_state.boyutlar = []
if "renkler" not in st.session_state:
    st.session_state.renkler = []
if "sekiller" not in st.session_state:
    st.session_state.sekiller = []

def boyut_ekle():
    val = st.session_state.boyut_input.strip()
    if val and val not in st.session_state.boyutlar:
        st.session_state.boyutlar.append(val)
    st.session_state.boyut_input = ""

def renk_ekle():
    val = st.session_state.renk_input.strip()
    if val and val not in st.session_state.renkler:
        st.session_state.renkler.append(val)
    st.session_state.renk_input = ""

def sekil_ekle():
    val = st.session_state.sekil_input.strip()
    if val and val not in st.session_state.sekiller:
        st.session_state.sekiller.append(val)
    st.session_state.sekil_input = ""

# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================
def parse_blocks(text):
    blocks = {"BASLIK": "", "ACIKLAMA": "", "ETIKETLER": "", "TR_BASLIK": "", "TR_ACIKLAMA": "", "TR_ETIKETLER": ""}
    pattern = r"\[(BASLIK\vert{}ACIKLAMA\vert{}ETIKETLER\vert{}TR_BASLIK\vert{}TR_ACIKLAMA\vert{}TR_ETIKETLER)\]"
    matches = list(re.finditer(pattern, text))
    for i, match in enumerate(matches):
        tag_name = match.group(1)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks[tag_name] = text[start_pos:end_pos].strip()
    return blocks

def clean_tags(tag_str, max_len=20):
    cleaned = []
    for t in tag_str.split(','):
        t = t.strip()
        if not t:
            continue
        if len(t) > max_len:
            cut = t[:max_len]
            if " " in cut:
                cut = cut.rsplit(" ", 1)[0]
            t = cut.strip(" ,.-")
        if t:
            cleaned.append(t)
    return ", ".join(cleaned)

def trim_title(title, max_len=140):
    title = title.strip()
    if len(title) <= max_len:
        return title
    cut = title[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" ,.-")

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def generate_once(prompt_text, uploaded_file):
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=st.secrets.get("GROQ_API_KEY", "")
    )
    
    base64_image = encode_image(uploaded_file)
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=8000,
        )
        return response.choices[0].message.content
    except Exception as e:
        err_str = str(e)
        if "401" in err_str:
            friendly = "API Anahtarı geçersiz. Lütfen secrets dosyasındaki GROQ_API_KEY bilgisini kontrol edin."
        elif "429" in err_str:
            friendly = "Groq hız sınırına takıldınız. Lütfen birkaç saniye bekleyip tekrar deneyin."
        else:
            friendly = "Bir hata oluştu."
        raise RuntimeError(friendly + f"\n\nTeknik detay: {err_str}")


# =========================================================
# ÜST BAŞLIK
# =========================================================
st.title("meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu")

sol_sutun, sag_sutun = st.columns([1, 2], gap="large")

# =========================================================
# SOL SÜTUN
# =========================================================
with sol_sutun:
    r1, r2 = st.columns(2)
    with r1:
        urun_tipi_secimi = st.radio("📦 Ürün Tipi:", ["Fiziksel Ürün", "Dijital İndirme"])
        is_digital = "Dijital" in urun_tipi_secimi
    with r2:
        dil_secimi = st.radio("🌍 Hedef Pazar / Dil", ["İngilizce", "Türkçe"])
        is_english = "İngilizce" in dil_secimi

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    i1, i2 = st.columns([1, 2])
    with i1:
        uploaded_file = st.file_uploader("Görsel Yükle", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            preview = image.copy()
            preview.thumbnail((120, 120))
            st.image(preview)
    with i2:
        ipucu = "Örn: Dünya temalı logo..." if is_digital else "Örn: Beyaz vinil çıkartma..."
        urun_tanimi = st.text_area("Bu ürün nedir? (İpucu):", placeholder=ipucu, height=100)

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    col_b_input, col_b_list = st.columns(2)
    with col_b_input:
        boyut_lbl = "Format/Oran (Enter'a bas):" if is_digital else "Ebat/Boyut (Enter'a bas):"
        st.text_input(boyut_lbl, key="boyut_input", on_change=boyut_ekle)
    with col_b_list:
        st.caption("Eklenenler:")
        for item in st.session_state.boyutlar:
            c_text, c_btn = st.columns([4, 1])
            c_text.write(f"▪️ {item}")
            if c_btn.button("❌", key=f"del_b_{item}"):
                st.session_state.boyutlar.remove(item)
                st.rerun()

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    col_r_input, col_r_list = st.columns(2)
    with col_r_input:
        renk_lbl = "Dosya Türü (Enter'a bas):" if is_digital else "Renk Seçeneği (Enter'a bas):"
        st.text_input(renk_lbl, key="renk_input", on_change=renk_ekle)
    with col_r_list:
        st.caption("Eklenenler:")
        for item in st.session_state.renkler:
            c_text, c_btn = st.columns([4, 1])
            c_text.write(f"▪️ {item}")
            if c_btn.button("❌", key=f"del_r_{item}"):
                st.session_state.renkler.remove(item)
                st.rerun()

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    col_s_input, col_s_list = st.columns(2)
    with col_s_input:
        st.text_input("Şekil (Enter'a bas):", key="sekil_input", on_change=sekil_ekle)
    with col_s_list:
        st.caption("Eklenenler:")
        for item in st.session_state.sekiller:
            c_text, c_btn = st.columns([4, 1])
            c_text.write(f"▪️ {item}")
            if c_btn.button("❌", key=f"del_s_{item}"):
                st.session_state.sekiller.remove(item)
                st.rerun()

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    ekstra_not = st.text_area("Ekstra Not (Opsiyonel):", height=60)

    uret_btn = st.button("✨ İçerikleri Üret", type="primary", use_container_width=True)

# =========================================================
# SAĞ SÜTUN
# =========================================================
with sag_sutun:
    if uret_btn and uploaded_file is not None:
        try:
            with st.spinner("Görsel analiz ediliyor, içerikler hazırlanıyor (Groq API)..."):
                target_language = "ENGLISH" if is_english else "TURKISH"
                product_hint = f"\nThe user describes this product as: '{urun_tanimi}'." if urun_tanimi else ""

                size_hint = f"\nAvailable sizes/ratios: {', '.join(st.session_state.boyutlar)}." if st.session_state.boyutlar else ""
                color_hint = f"\nAvailable colors/formats: {', '.join(st.session_state.renkler)}." if st.session_state.renkler else ""
                shape_hint = f"\nAvailable shapes: {', '.join(st.session_state.sekiller)}." if st.session_state.sekiller else ""

                if is_digital:
                    base_instruction = "You are an expert Etsy SEO copywriter focusing on DIGITAL DOWNLOAD products. CRITICAL: Emphasize that this is an INSTANT DIGITAL DOWNLOAD. NO physical item will be shipped."
                else:
                    base_instruction = "You are an expert Etsy SEO copywriter and a creative artisan copywriter analyzing a handmade/custom-designed physical product."

                translation_instruction = ""
                if is_english:
                    translation_instruction = """
                    === TRANSLATION RULES ===
                    Since the target language is ENGLISH, you MUST ALSO provide the exact TURKISH translation. 
                    Append them at the very end using EXACTLY these tags: [TR_BASLIK], [TR_ACIKLAMA], [TR_ETIKETLER].
                    """

                prompt = f"""
                {base_instruction}
                {product_hint}
                {size_hint}
                {color_hint}
                {shape_hint}

                === CONTENT RULES ===
                TITLE: Maximum 140 characters. First 5 words must be directly related to the product.
                DESCRIPTION: EXACTLY 3 paragraphs. Start each with an emoji. Paragraph 1: Warm introduction. Paragraph 2: Bullet list of specs. Paragraph 3: Bullet list of uses.
                TAGS: Exactly 13 SEO tags separated by commas. Maximum 20 characters per tag. Do NOT hallucinate formats not provided.
                {translation_instruction}

                === CRITICAL FORMATTING RULES ===
                You MUST wrap your outputs with the exact bracket tags below. Do NOT use markdown bolding (**) for the tags. Do NOT skip the brackets.
                
                [BASLIK]
                (Write title here)
                [ACIKLAMA]
                (Write description here)
                [ETIKETLER]
                (Write tags here)
                """

                # Groq API'ye resmi ve promptu gönder
                response_text = generate_once(prompt, uploaded_file)
                blocks = parse_blocks(response_text)

                # =========================================================
                # HATA KORUMASI (FALLBACK): Model formata uymazsa ham yazıyı göster
                # =========================================================
                if not blocks["BASLIK"] and not blocks["ACIKLAMA"] and not blocks["ETIKETLER"]:
                    st.warning("⚠️ Model içerikleri başarıyla üretti ancak kutulara yerleştirmek için gereken formata uymadı. Üretilen içerikleri aşağıda görebilirsiniz:")
                    if ekstra_not:
                        st.info(f"Eklenen Ekstra Not: {ekstra_not}")
                    st.text_area("Yapay Zekanın Ham Çıktısı (Kopyalayabilirsiniz):", response_text, height=500)
                else:
                    # Formata uyduysa normal kutulara yerleştir
                    if blocks["BASLIK"]:
                        blocks["BASLIK"] = trim_title(blocks["BASLIK"].title())

                    if is_english and blocks["TR_BASLIK"]:
                        blocks["TR_BASLIK"] = trim_title(blocks["TR_BASLIK"].title())

                    blocks["ETIKETLER"] = clean_tags(blocks["ETIKETLER"])
                    if blocks["TR_ETIKETLER"]:
                        blocks["TR_ETIKETLER"] = clean_tags(blocks["TR_ETIKETLER"])

                    if ekstra_not:
                        blocks["ACIKLAMA"] += f"\n• {ekstra_not}"
                        if is_english and blocks["TR_ACIKLAMA"]:
                            blocks["TR_ACIKLAMA"] += f"\n• {ekstra_not}"

                    st.info("💡 Yapay zeka aracılığıyla yüklediğiniz görsel analiz edilerek oluşturulan ürün bilgileri otomasyonudur. Lütfen kullanmadan önce okuyarak gerekli revize işlemlerinden sonra içerikleri uygulayınız.")
                    st.caption(f"🔧 Kullanılan model: `{MODEL_NAME}`  •  Başlık uzunluğu: {len(blocks['BASLIK'])}/140")

                    if is_english and blocks["TR_BASLIK"]:
                        tab1, tab2 = st.tabs(["🇬🇧 İngilizce (Orijinal)", "🇹🇷 Türkçe Çevirisi (Kontrol İçin)"])

                        with tab1:
                            st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                            st.text_area("Açıklama", blocks["ACIKLAMA"], height=320, label_visibility="collapsed")
                            st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")

                        with tab2:
                            st.text_area("TR Başlık", blocks["TR_BASLIK"], label_visibility="collapsed")
                            st.text_area("TR Açıklama", blocks["TR_ACIKLAMA"], height=320, label_visibility="collapsed")
                            st.text_area("TR Etiketler", blocks["TR_ETIKETLER"], label_visibility="collapsed")
                    else:
                        st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                        st.text_area("Açıklama", blocks["ACIKLAMA"], height=320, label_visibility="collapsed")
                        st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")

        except Exception as e:
            st.error(f"Bir hata oluştu. Lütfen birkaç saniye bekleyip tekrar deneyin. Hata detayları: {str(e)}")

    elif not uploaded_file:
        st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
