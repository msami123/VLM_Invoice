import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
from dotenv import load_dotenv

from image_processor import preprocess_image
from prompts import get_prompt

# Load environment variables
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("⚠️ API Key not found! Please create a .env file with GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# UI text for both languages
UI_TEXT = {
    'ar': {
        'title': '🧾 استخراج بيانات الفواتير',
        'upload': 'ارفع صورة الفاتورة',
        'camera': 'أو التقط صورة بالكاميرا',
        'extract': '🔍 استخراج البيانات',
        'processing': 'جاري التحليل...',
        'success': '✅ تم الاستخراج بنجاح!',
        'error': '❌ حدث خطأ',
        'original': '📸 الصورة الأصلية',
        'processed': '✨ بعد المعالجة',
        'info': '📊 معلومات الفاتورة',
        'items': '🛒 المنتجات',
        'download': '📥 تنزيل JSON',
        'na': 'غير متوفر'
    },
    'en': {
        'title': '🧾 Invoice Data Extractor',
        'upload': 'Upload Invoice Image',
        'camera': 'Or capture with camera',
        'extract': '🔍 Extract Data',
        'processing': 'Analyzing...',
        'success': '✅ Extracted Successfully!',
        'error': '❌ Error Occurred',
        'original': '📸 Original Image',
        'processed': '✨ Processed',
        'info': '📊 Invoice Information',
        'items': '🛒 Items',
        'download': '📥 Download JSON',
        'na': 'N/A'
    }
}


def extract_invoice_data(image, language='ar'):
    """
    Extract invoice data using Gemini Vision
    """
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    prompt = get_prompt(language)

    try:
        response = model.generate_content([prompt, image])
        response_text = response.text.strip()

        # Remove markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()
        data = json.loads(response_text)
        return data, None

    except Exception as e:
        return None, str(e)


# Initialize session state
if 'language' not in st.session_state:
    st.session_state.language = 'ar'

# Get UI text
text = UI_TEXT[st.session_state.language]

# Page config
st.set_page_config(page_title=text['title'], page_icon='🧾', layout="wide")

# Language selector
col1, col2 = st.columns([5, 1])
with col2:
    lang = st.selectbox(
        'Language',
        ['ar', 'en'],
        format_func=lambda x: '🇸🇦 العربية' if x == 'ar' else '🇬🇧 English',
        label_visibility='collapsed'
    )
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.rerun()

# Title
st.title(text['title'])
st.markdown("---")

# File uploader and camera input
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(text['upload'], type=['png', 'jpg', 'jpeg'])

with col2:
    camera_photo = st.camera_input(text['camera'])

# Use camera photo if available, otherwise use uploaded file
image_source = camera_photo if camera_photo else uploaded_file

if image_source:
    # Display images
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(text['original'])
        image = Image.open(image_source)
        st.image(image, use_container_width=True)

    with col2:
        st.subheader(text['processed'])
        processed_image = preprocess_image(image.copy())
        st.image(processed_image, use_container_width=True)

    st.markdown("---")

    # Extract button
    if st.button(text['extract'], type="primary", use_container_width=True):
        with st.spinner(text['processing']):
            data, error = extract_invoice_data(processed_image, st.session_state.language)

            if error:
                st.error(f"{text['error']}: {error}")
            elif data:
                st.success(text['success'])

                # Basic info
                st.subheader(text['info'])
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Store", data.get('store_name', text['na']))
                    st.metric("Business", data.get('business_type', text['na']))
                    st.metric("Payment", data.get('payment_method', text['na']))

                with col2:
                    st.metric("Date", data.get('date', text['na']))
                    st.metric("Invoice #", data.get('invoice_number', text['na']))
                    if data.get('card_number'):
                        st.metric("Card", data.get('card_number'))

                with col3:
                    st.metric("Items", data.get('items_count', len(data.get('items', []))))
                    st.metric("Total", f"{data.get('total_amount', 0)} {data.get('currency', 'SAR')}")

                # Items
                if data.get('items'):
                    st.subheader(text['items'])
                    for idx, item in enumerate(data['items'], 1):
                        with st.expander(f"{idx}. {item.get('name', text['na'])}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Qty:** {item.get('quantity', text['na'])}")
                            with col2:
                                st.write(f"**Price:** {item.get('unit_price', text['na'])}")
                            with col3:
                                st.write(f"**Total:** {item.get('total', text['na'])}")

                # Full JSON
                with st.expander("📄 Full JSON"):
                    st.json(data)

                # Download
                json_string = json.dumps(data, ensure_ascii=False, indent=2)
                st.download_button(
                    text['download'],
                    json_string,
                    "invoice_data.json",
                    "application/json"
                )