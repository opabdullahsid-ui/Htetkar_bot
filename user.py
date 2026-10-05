# user.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import config

async def clear_orphaned_photo(chat_id, context):
    """Helper to clean up the separate product photo when navigating back."""
    if 'last_photo_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['last_photo_id'])
        except:
            pass
        del context.user_data['last_photo_id']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoUsername"
    db.add_user(user_id, username)

    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇲 မြန်မာစာ (Myanmar)", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = db.get_setting('start_msg')
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await clear_orphaned_photo(update.callback_query.message.chat_id, context)
        if update.callback_query.message.photo:
            await update.callback_query.message.delete()
            await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await clear_orphaned_photo(query.message.chat_id, context)
    db.add_user(update.effective_user.id, update.effective_user.username or "NoUsername")

    if query.data.startswith("lang_"):
        context.user_data["lang"] = query.data.split("_")[1]
    
    lang = context.user_data.get("lang", "en")
    
    if lang == "my":
        text = db.get_setting('menu_msg_my')
        btn_text = "🛍️ အမှတ်တံဆိပ်များကို ကြည့်ရန်"
    else:
        text = db.get_setting('menu_msg_en')
        btn_text = "🛍️ Browse Brands"

    keyboard = [
        [InlineKeyboardButton(btn_text, callback_data="show_brands")],
        [InlineKeyboardButton("🔙 Back / နောက်သို့", callback_data="start_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    img_id = db.get_setting('menu_image')
    has_image = img_id and img_id not in ['none', 'Welcome!']

    if has_image:
        await query.message.delete()
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=img_id, caption=text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

async def show_brands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await clear_orphaned_photo(query.message.chat_id, context)
    
    brands = db.get_brands()
    keyboard = []
    for brand_id, brand_name in brands:
        keyboard.append([InlineKeyboardButton(f"🏷️ {brand_name}", callback_data=f"brand_{brand_id}")])
    
    lang = context.user_data.get("lang", "en")
    if lang == "my":
        back_text = "🔙 နောက်သို့"
        title_text = "📱 <b>အမှတ်တံဆိပ်တစ်ခုကို ရွေးချယ်ပါ:</b> "
    else:
        back_text = "🔙 Back"
        title_text = "📱 <b>Choose a Brand:</b> "
    
    keyboard.append([InlineKeyboardButton(back_text, callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.photo:
        await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, text=title_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await query.edit_message_text(text=title_text, reply_markup=reply_markup, parse_mode="HTML")

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await clear_orphaned_photo(query.message.chat_id, context)
    
    brand_id = int(query.data.split("_")[1])
    brand_name = db.get_brand_name(brand_id)
    products = db.get_products_by_brand(brand_id)
    lang = context.user_data.get("lang", "en")
    
    keyboard = []
    for prod_id, prod_name in products:
        keyboard.append([InlineKeyboardButton(f"📱 {prod_name}", callback_data=f"prod_{prod_id}")])
        
    back_text = "🔙 နောက်သို့" if lang == "my" else "🔙 Back"
    title_text = f"✨ <b>{brand_name} မော်ဒယ်များ:</b>" if lang == "my" else f"✨ <b>{brand_name} Models:</b>"
    
    if not products:
        empty_text = "❌ ပစ္စည်းမရှိသေးပါ။" if lang == "my" else "❌ No products found."
        title_text += f"\n\n{empty_text}"

    keyboard.append([InlineKeyboardButton(back_text, callback_data="show_brands")])
    
    if query.message.photo:
        await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, text=title_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await query.edit_message_text(text=title_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def show_product_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    prod_id = int(query.data.split("_")[1])
    lang = context.user_data.get("lang", "en")
    
    product = db.get_product_details(prod_id)
    if not product:
        await query.answer("Product not found!", show_alert=True)
        return
        
    name, price_myr, price_usdt, specs_en, specs_my, image_url, brand_name, brand_id = product
    
    # Safely convert prices to prevent crash if a letter was accidentally typed
    try:
        myr_val = float(price_myr)
        usdt_val = float(price_usdt)
    except:
        myr_val = 0.0
        usdt_val = 0.0
    
    specs = specs_my if lang == "my" else specs_en
    price_label = "စျေးနှုန်း" if lang == "my" else "Price"
    specs_label = "အသေးစိတ်အချက်အလက်များ" if lang == "my" else "Specifications"
    buy_btn_text = "💬 ဆက်သွယ်ရန် / ဝယ်ယူရန်" if lang == "my" else "💬 Inquire / Buy"
    back_btn_text = "🔙 နောက်သို့" if lang == "my" else "🔙 Back"
    
    caption = (
        f"📱 <b>{brand_name} {name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>{price_label}:</b>\n"
        f"🇲🇾 RM {myr_val:,.2f} | 💵 {usdt_val:,.2f} USDT\n\n"
        f"⚙️ <b>{specs_label}:</b>\n"
        f"{specs}\n"
    )
    
    inquire_url = f"https://t.me/{config.ADMIN_USERNAME}?text=Hello,%20I%20am%20interested%20in%20{name}"
    keyboard = [[InlineKeyboardButton(buy_btn_text, url=inquire_url)], [InlineKeyboardButton(back_btn_text, callback_data=f"brand_{brand_id}")]]
    
    await query.message.delete()
    
    # FIX: Send the photo completely separate from the text to bypass Telegram's Premium Emoji blocks!
    if image_url and image_url not in ['none', 'Welcome!']:
        try:
            photo_msg = await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_url)
            context.user_data['last_photo_id'] = photo_msg.message_id
        except:
            pass

    # Send the specs as a standard text message right below the photo
    try:
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text=caption, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="HTML"
        )
    except Exception:
        # Failsafe fallback if HTML is entirely broken
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text=f"⚠️ Formatting Error:\n\n{caption}", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
