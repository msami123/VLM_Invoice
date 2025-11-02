"""
Prompts configuration for invoice data extraction
"""

PROMPTS = {
    'ar': """
قم بتحليل صورة الفاتورة هذه بدقة واستخرج جميع المعلومات التالية.
أرجع البيانات بصيغة JSON فقط بدون أي نص إضافي:

{
  "store_name": "اسم المتجر أو المؤسسة",
  "tax_number": "الرقم الضريبي",
  "cr_number": "رقم السجل التجاري إن وجد",
  "branch": "الفرع إن وجد",
  "date": "التاريخ بصيغة YYYY-MM-DD",
  "time": "الوقت",
  "invoice_number": "رقم الفاتورة",
  "business_type": "حدد نوع النشاط التجاري بدقة عالية بناءً على: (1) اسم المحل وعلامته التجارية (2) نوع المنتجات المباعة (3) طبيعة الخدمة المقدمة. استخدم التصنيف الأدق والأكثر تحديداً (مثال: مقهى، مطعم وجبات سريعة، مطعم فاخر، سوبرماركت، هايبرماركت، صيدلية، محطة وقود، محل ملابس، محل أحذية، مخبز، حلويات، محل إلكترونيات، محل أثاث، بنك، صراف آلي، مكتبة، صالون تجميل، مغسلة، ورشة، إلخ)",
  "payment_method": "طريقة الدفع (نقدي، مدى، فيزا، ماستركارد، أمريكان إكسبريس، آبل باي، STC Pay، إلخ)",
  "card_number": "آخر 4 أرقام من البطاقة إن وجدت (مثال: ****1234)، أو null إن لم توجد",
  "delivery_app": "هل الطلب من تطبيق توصيل؟ إذا كان نعم اكتب اسم التطبيق (مثال: هنقرستيشن، جاهز، مرسول، طلبات، نينجا، توصيل، كريم ناو، تو يو، كيتا، Careem، HungerStation، Jahez، Marsool、Talabat، Ninja، Toters، Deliveroo، Carriage، The Chefz، Wssel، ToYou، TO_YOU، Keeta، Quiqup、Rafeeq، Chefz، Shgardi، Barq، Snoonu، Yemeksepeti، Delivery Hero، Smsa Express، Zajel، Fetchr، Aramex، Nana، Express، أي تطبيق توصيل آخر)، أو null إن لم يكن من تطبيق توصيل. ابحث عن أي إشارة لتطبيق التوصيل في: (1) اسم القناة Channel Name (2) رقم الطلب الخارجي External Order (3) نوع الطلب Order Type (4) أي نص يشير لتطبيق توصيل في الملاحظات",
  "items": [
    {
      "name": "اسم المنتج",
      "quantity": العدد,
      "unit_price": السعر_الفردي,
      "total": الإجمالي
    }
  ],
  "items_count": عدد_المنتجات_الإجمالي,
  "subtotal": المجموع_الفرعي,
  "tax_amount": قيمة_الضريبة,
  "tax_percentage": نسبة_الضريبة,
  "discount": الخصم_إن_وجد,
  "total_amount": المبلغ_الإجمالي_النهائي,
  "currency": "العملة (SAR عادة)",
  "cashier": "اسم الكاشير إن وجد",
  "additional_notes": "أي ملاحظات إضافية"
}

ملاحظات مهمة:
- إذا لم تجد معلومة معينة، ضع null
- تأكد من دقة الأرقام والمبالغ
- احسب عدد المنتجات من قائمة items
- استخرج كل التفاصيل الموجودة في الفاتورة
- كن محللاً ذكياً: استنتج نوع النشاط من سياق الفاتورة بالكامل وليس من معلومة واحدة فقط
- استخدم معرفتك بالعلامات التجارية والأسماء المشهورة لتحديد النشاط بدقة

⚠️ تحذير مهم جداً بخصوص المبلغ الإجمالي (total_amount):
- المبلغ الإجمالي النهائي يجب أن يكون المبلغ الكامل المكتوب في الفاتورة كـ "الإجمالي" أو "Total" أو "المبلغ المستحق"
- الضريبة (tax_amount) عادة تكون مشمولة ومحسوبة بالفعل داخل المبلغ الإجمالي
- لا تجمع الضريبة على المبلغ الإجمالي مرة أخرى
- مثال: إذا كان المجموع الفرعي 38 ريال والضريبة 2 ريال والإجمالي النهائي المكتوب 40 ريال، فالـ total_amount يجب أن يكون 40 وليس 42
- اقرأ المبلغ الإجمالي مباشرة من الفاتورة كما هو مكتوب بالضبط
""",

    'en': """
Analyze this invoice image carefully and extract all the following information.
Return the data in JSON format only without any additional text:

{
  "store_name": "Store or business name",
  "tax_number": "Tax number",
  "cr_number": "Commercial registration number if available",
  "branch": "Branch if available",
  "date": "Date in YYYY-MM-DD format",
  "time": "Time",
  "invoice_number": "Invoice number",
  "business_type": "Determine the business type with high accuracy based on: (1) store name and brand (2) type of products sold (3) nature of service provided. Use the most specific and accurate classification (e.g., cafe, fast food restaurant, fine dining restaurant, supermarket, hypermarket, pharmacy, gas station, clothing store, shoe store, bakery, sweets shop, electronics store, furniture store, bank, ATM, bookstore, beauty salon, laundry, workshop, etc.)",
  "payment_method": "Payment method (cash, mada, visa, mastercard, american express, apple pay, STC Pay, etc.)",
  "card_number": "Last 4 digits of card if available (example: ****1234), or null if not found",
  "delivery_app": "Is this order from a delivery app? If yes, write the app name (examples: HungerStation, Jahez, Marsool, Talabat, Ninja, Toters, Careem Now, Deliveroo, Carriage, The Chefz, Wssel, ToYou, TO_YOU, Keeta, Quiqup, Rafeeq, Chefz, Shgardi, Barq, Snoonu, Yemeksepeti, Delivery Hero, Smsa Express, Zajel, Fetchr, Aramex, Nana, Express, or any other delivery app), or null if not from delivery app. Look for any indication of delivery app in: (1) Channel Name (2) External Order number (3) Order Type (4) any text indicating delivery app in notes",
  "items": [
    {
      "name": "Product name",
      "quantity": quantity,
      "unit_price": unit_price,
      "total": total
    }
  ],
  "items_count": total_number_of_items,
  "subtotal": subtotal_amount,
  "tax_amount": tax_amount,
  "tax_percentage": tax_percentage,
  "discount": discount_if_any,
  "total_amount": final_total_amount,
  "currency": "Currency (usually SAR)",
  "cashier": "Cashier name if available",
  "additional_notes": "Any additional notes"
}

Important notes:
- If you can't find specific information, put null
- Ensure accuracy of numbers and amounts
- Calculate the number of items from the items list
- Extract all details present in the invoice
- Be an intelligent analyzer: deduce the business type from the entire invoice context, not just one piece of information
- Use your knowledge of brands and famous names to accurately determine the business type

⚠️ CRITICAL WARNING about total_amount:
- The total_amount must be the EXACT final total written on the invoice as "Total" or "Amount Due" or "الإجمالي"
- Tax (tax_amount) is usually ALREADY INCLUDED in the total amount
- DO NOT add tax to total_amount again
- Example: If subtotal is 38 SAR, tax is 2 SAR, and the invoice shows final total as 40 SAR, then total_amount should be 40, NOT 42
- Read the total_amount directly from the invoice exactly as written
"""
}


def get_prompt(language='ar'):
    """
    Get the appropriate prompt based on the selected language
    """
    return PROMPTS.get(language, PROMPTS['ar'])