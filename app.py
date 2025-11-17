import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
from dotenv import load_dotenv

from image_processor import preprocess_image, extract_single_document
from prompts import get_prompt

# Load environment variables
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("⚠️ API Key not found! Please create a .env file with GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# YOLO model path
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "'/Users/anody/Downloads/best (1).pt'")

# UI text for both languages
UI_TEXT = {
    'ar': {
        'title': '🧾 استخراج بيانات الفواتير',
        'upload': 'ارفع صورة الفاتورة',
        'camera': 'أو التقط صورة بالكاميرا',
        'processing': 'جاري المعالجة والتحليل...',
        'success': '✅ تم الاستخراج بنجاح!',
        'error': '❌ حدث خطأ',
        'no_invoice': '⚠️ لم يتم العثور على فاتورة في الصورة',
        'processed': '✨ الفاتورة المعالجة',
        'info': '📊 معلومات الفاتورة',
        'items': '🛒 المنتجات',
        'download': '📥 تنزيل JSON',
        'na': 'غير متوفر'
    },
    'en': {
        'title': '🧾 Invoice Data Extractor',
        'upload': 'Upload Invoice Image',
        'camera': 'Or capture with camera',
        'processing': 'Processing and analyzing...',
        'success': '✅ Extracted Successfully!',
        'error': '❌ Error Occurred',
        'no_invoice': '⚠️ No invoice found in image',
        'processed': '✨ Processed Invoice',
        'info': '📊 Invoice Information',
        'items': '🛒 Items',
        'download': '📥 Download JSON',
        'na': 'N/A'
    }
}


def extract_invoice_data(image, language='ar'):
    """
    Extract invoice data using Gemini Vision API

    Args:
        image: PIL Image object
        language: Language code ('ar' or 'en')

    Returns:
        tuple: (data dict, error string or None)
    """
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    prompt = get_prompt(language)

    try:
        response = model.generate_content([prompt, image])
        response_text = response.text.strip()

        # Remove markdown code block formatting
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


# Initialize session state for language
if 'language' not in st.session_state:
    st.session_state.language = 'ar'

# Get UI text based on selected language
text = UI_TEXT[st.session_state.language]

# Page configuration
st.set_page_config(page_title=text['title'], page_icon='🧾', layout="wide")

# Language selector in top right
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

# Page title
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
    # Load original image
    image = Image.open(image_source)

    # Process invoice: detect, crop, and enhance
    with st.spinner(text['processing']):
        # Step 1: Detect and crop invoice using YOLO segmentation
        result = extract_single_document(
            image=image,
            model_path=MODEL_PATH,
            confidence=0.5,
            preprocess=False
        )

        if result:
            cropped_invoice, confidence = result

            # Step 2: Enhance cropped invoice
            processed_image = preprocess_image(cropped_invoice.copy())

            # Display only the final processed image
            st.image(processed_image, caption=text['processed'], use_container_width=True)

            st.markdown("---")

            # Step 3: Extract data using Gemini Vision
            data, error = extract_invoice_data(processed_image, st.session_state.language)

            if error:
                st.error(f"{text['error']}: {error}")
            elif data:
                st.success(text['success'])

                # Invoice information section
                st.subheader(text['info'])

                # Row 1: Store information
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Store", data.get('store_name', text['na']))
                with col2:
                    st.metric("Tax Number", data.get('tax_number', text['na']))
                with col3:
                    st.metric("CR Number", data.get('cr_number', text['na']))

                # Row 2: Branch, business type, payment method
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Branch", data.get('branch', text['na']))
                with col2:
                    st.metric("Business Type", data.get('business_type', text['na']))
                with col3:
                    st.metric("Payment Method", data.get('payment_method', text['na']))

                # Row 3: Date, time, invoice number
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Date", data.get('date', text['na']))
                with col2:
                    st.metric("Time", data.get('time', text['na']))
                with col3:
                    st.metric("Invoice #", data.get('invoice_number', text['na']))

                # Row 4: Card number, delivery app, cashier
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Card Number", data.get('card_number', text['na']))
                with col2:
                    st.metric("🛵 Delivery App", data.get('delivery_app', text['na']))
                with col3:
                    st.metric("Cashier", data.get('cashier', text['na']))

                # Row 5: Financial summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Subtotal", f"{data.get('subtotal', 0)} {data.get('currency', 'SAR')}")
                with col2:
                    st.metric("Tax", f"{data.get('tax_amount', 0)} ({data.get('tax_percentage', 0)}%)")
                with col3:
                    st.metric("Discount", f"{data.get('discount', 0)} {data.get('currency', 'SAR')}")

                # Row 6: Items count, total amount, notes
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Items Count", data.get('items_count', len(data.get('items', []))))
                with col2:
                    st.metric("💰 Total Amount", f"{data.get('total_amount', 0)} {data.get('currency', 'SAR')}")
                with col3:
                    if data.get('additional_notes'):
                        st.metric("Notes", data.get('additional_notes', text['na']))

                # Items list
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

                # Full JSON data expandable section
                with st.expander("📄 Full JSON"):
                    st.json(data)

                # Download button for JSON file
                json_string = json.dumps(data, ensure_ascii=False, indent=2)
                st.download_button(
                    text['download'],
                    json_string,
                    "invoice_data.json",
                    "application/json"
                )
        else:
            # No invoice detected in image
            st.warning(text['no_invoice'])
            st.info("💡 Try another image or ensure the invoice is clearly visible")