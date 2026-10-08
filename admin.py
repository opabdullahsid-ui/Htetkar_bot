# admin.py
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
import database as db
import config

(A_BRAND, A_NAME, A_MYR, A_USDT, A_EN, A_MY, A_IMG) = range(7)
(SET_START_MSG,) = range(10, 11)
(NEW_BRAND_NAME,) = range(20, 21)
(CP_BRAND, CP_PROD, CP_MYR, CP_USDT) = range(30, 34)
(ANN_MSG,) = range(40, 41)
(DEL_P_BRAND, DEL_P_PROD, DEL_P_CONFIRM) = range(50, 53)
(DEL_B_BRAND, DEL_B_CONFIRM) = range(60, 62)
(SET_MENU_EN,) = range(70, 71)
(SET_MENU_MY,) = range(80, 81)
(SET_MENU_IMG,) = range(90, 91)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return
    keyboard = [
        [InlineKeyboardButton("➕ Add Product", callback_data="admin_add_start"),
         InlineKeyboardButton("➕ Add Brand", callback_data="admin_add_brand_btn")],
        [InlineKeyboardButton("🗑️ Delete Product", callback_data="del_p_start"),
         InlineKeyboardButton("🗑️ Delete Brand", callback_data="del_b_start")],
        [InlineKeyboardButton("💰 Change Price", callback_data="cp_start"),
         InlineKeyboardButton("📢 Announce", callback_data="ann_start")],
        [InlineKeyboardButton("👥 Get all Users", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Exit", callback_data="admin_cancel")]
    ]
    
    panel_text = (
        "🛡️ <b>Admin Panel</b>\nChoose an action below.\n\n"
        "<i>Customization Commands:</i>\n"
        "/setstart - Change welcome message\n"
        "/setmenu_en - Change English menu text\n"
        "/setmenu_my - Change Myanmar menu text\n"
        "/setmenu_image - Set image for the main menu"
    )
    
    if update.message:
        await update.message.reply_text(panel_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(panel_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ Action Cancelled. Type /admin to open again.")
    else:
        await update.message.reply_text("❌ Action Cancelled.")
    return ConversationHandler.END

async def setstart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return
    await update.message.reply_text("📝 Send new welcome message:")
    return SET_START_MSG

async def save_start_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.update_setting('start_msg', update.message.text_html)
    await update.message.reply_text("✅ Start message updated!")
    return ConversationHandler.END

async def setmenu_en_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return
    await update.message.reply_text("📝 Send new ENGLISH main menu message:")
    return SET_MENU_EN

async def save_menu_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.update_setting('menu_msg_en', update.message.text_html)
    await update.message.reply_text("✅ English menu message updated!")
    return ConversationHandler.END

async def setmenu_my_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return
    await update.message.reply_text("📝 Send new MYANMAR main menu message:")
    return SET_MENU_MY

async def save_menu_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.update_setting('menu_msg_my', update.message.text_html)
    await update.message.reply_text("✅ Myanmar menu message updated!")
    return ConversationHandler.END

async def setmenu_img_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return
    await update.message.reply_text("🖼️ Send me the new photo for the main menu:\n*(Type /remove_image to delete current photo)*")
    return SET_MENU_IMG

async def save_menu_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/remove_image":
        db.update_setting('menu_image', 'none')
        await update.message.reply_text("✅ Menu image removed! It is now text-only.")
        return ConversationHandler.END

    if not update.message.photo:
        await update.message.reply_text("❌ Please send a PHOTO, not text. (Or type /cancel)")
        return SET_MENU_IMG

    file_id = update.message.photo[-1].file_id
    db.update_setting('menu_image', file_id)
    await update.message.reply_text("✅ Main menu image updated successfully!")
    return ConversationHandler.END

async def del_p_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    brands = db.get_brands()
    keyboard = [[InlineKeyboardButton(f"🏷️ {b[1]}", callback_data=f"dp_b_{b[0]}")] for b in brands]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    await update.callback_query.edit_message_text("Select Brand to find the product:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DEL_P_BRAND

async def del_p_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    brand_id = update.callback_query.data.split("_")[2]
    products = db.get_products_by_brand(brand_id)
    if not products:
        await update.callback_query.edit_message_text("❌ No products in this brand.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"📱 {p[1]}", callback_data=f"dp_p_{p[0]}")] for p in products]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    await update.callback_query.edit_message_text("Select Product to Delete:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DEL_P_PROD

async def del_p_prod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    prod_id = update.callback_query.data.split("_")[2]
    context.user_data['del_prod_id'] = prod_id
    prod = db.get_product_details(prod_id)
    keyboard = [[InlineKeyboardButton("⚠️ YES, DELETE IT", callback_data="dp_confirm")], [InlineKeyboardButton("❌ NO, CANCEL", callback_data="admin_cancel")]]
    await update.callback_query.edit_message_text(f"Are you sure you want to delete **{prod[0]}**?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DEL_P_CONFIRM

async def del_p_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    db.delete_product(context.user_data['del_prod_id'])
    await update.callback_query.edit_message_text("✅ Product deleted!")
    return ConversationHandler.END

async def del_b_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    brands = db.get_brands()
    keyboard = [[InlineKeyboardButton(f"🏷️ {b[1]}", callback_data=f"db_b_{b[0]}")] for b in brands]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    await update.callback_query.edit_message_text("Select Brand to Delete:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DEL_B_BRAND

async def del_b_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    brand_id = update.callback_query.data.split("_")[2]
    context.user_data['del_brand_id'] = brand_id
    keyboard = [[InlineKeyboardButton("⚠️ YES, DELETE BRAND & ALL PHONES", callback_data="db_confirm")], [InlineKeyboardButton("❌ NO, CANCEL", callback_data="admin_cancel")]]
    await update.callback_query.edit_message_text("⚠️️ **WARNING** ⚠️\nDeleting this brand deletes EVERY product inside it!\nAre you sure?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DEL_B_CONFIRM

async def del_b_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    db.delete_brand(context.user_data['del_brand_id'])
    await update.callback_query.edit_message_text("✅ Brand deleted!")
    return ConversationHandler.END

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = db.get_all_users()
    with open("users_list.txt", "w") as f:
        f.write(f"--- H-Tech Catalog Users ---\nTotal Users: {len(users)}\n\n")
        for u in users: f.write(f"ID: {u[0]} | Username: @{u[1]}\n")
    await query.message.reply_document(document=open("users_list.txt", "rb"), caption=f"📊 Total Users: {len(users)}")
    os.remove("users_list.txt")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID is: `{update.effective_user.id}`", parse_mode="Markdown")

async def ann_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return ConversationHandler.END
    text = "📢 Send announcement message:\n*(Type /cancel to stop)*"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)
    return ANN_MSG

async def ann_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_html = update.message.text_html
    users = db.get_all_users()
    await update.message.reply_text(f"🚀 Broadcasting to {len(users)} users...")
    success = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=msg_html, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Sent to {success} users!")
    return ConversationHandler.END

async def add_brand_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🏷️ Type new Brand Name:")
    return NEW_BRAND_NAME

async def add_brand_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.add_brand(update.message.text): await update.message.reply_text("✅ Brand added!")
    else: await update.message.reply_text("❌ Failed!")
    return ConversationHandler.END

async def cp_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS: return ConversationHandler.END
    brands = db.get_brands()
    keyboard = [[InlineKeyboardButton(f"🏷️ {b[1]}", callback_data=f"cp_b_{b[0]}")] for b in brands]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    text = "Select Brand to change price:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CP_BRAND

async def cp_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    products = db.get_products_by_brand(update.callback_query.data.split("_")[2])
    keyboard = [[InlineKeyboardButton(f"📱 {p[1]}", callback_data=f"cp_p_{p[0]}")] for p in products]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    await update.callback_query.edit_message_text("Select Product:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CP_PROD

async def cp_prod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    prod_id = update.callback_query.data.split("_")[2]
    prod = db.get_product_details(prod_id)
    context.user_data['cp_id'] = prod_id
    context.user_data['cp_name'] = prod[0]
    context.user_data['cp_old_myr'] = prod[1]
    context.user_data['cp_bname'] = prod[6]
    await update.callback_query.edit_message_text(f"Current Price: RM {prod[1]}\nType NEW price in *MYR*:", parse_mode="Markdown")
    return CP_MYR

async def cp_myr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cp_new_myr'] = float(update.message.text)
    await update.message.reply_text("Type NEW price in *USDT*:", parse_mode="Markdown")
    return CP_USDT

async def cp_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_usdt, new_myr, old_myr = float(update.message.text), context.user_data['cp_new_myr'], context.user_data['cp_old_myr']
    db.update_price(context.user_data['cp_id'], new_myr, new_usdt)
    await update.message.reply_text("✅ Price updated!")
    bname, pname = context.user_data['cp_bname'], context.user_data['cp_name']
    
    if new_myr < old_myr: msg = f"📉 <b>PRICE DROP ALERT!</b> 🎉\n\n<b>{bname} {pname}</b> price just dropped!\n❌ Was: RM {old_myr:,.2f}\n✅ <b>Now: RM {new_myr:,.2f}</b>\n\nCheck the catalog to buy!"
    elif new_myr > old_myr: msg = f"📈 <b>Price Update</b>\n\nThe price for <b>{bname} {pname}</b> has been adjusted to <b>RM {new_myr:,.2f}</b>."
    else: return ConversationHandler.END

    for u in db.get_all_users():
        try:
            await context.bot.send_message(chat_id=u[0], text=msg, parse_mode="HTML")
            await asyncio.sleep(0.05)
        except: pass
    return ConversationHandler.END

async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton(f"🏷️ {b[1]}", callback_data=f"add_b_{b[0]}")] for b in db.get_brands()]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")])
    await update.callback_query.edit_message_text("Select Brand:", reply_markup=InlineKeyboardMarkup(keyboard))
    return A_BRAND

async def admin_add_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['new_brand_id'] = update.callback_query.data.split("_")[2]
    await update.callback_query.edit_message_text("Type Model Name:")
    return A_NAME

async def admin_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_name'] = update.message.text
    await update.message.reply_text("Type price in MYR:")
    return A_MYR

async def admin_add_myr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_myr'] = update.message.text
    await update.message.reply_text("Type price in USDT:")
    return A_USDT

async def admin_add_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_usdt'] = update.message.text
    await update.message.reply_text("Send English Specs:")
    return A_EN

async def admin_add_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_en'] = update.message.text_html
    await update.message.reply_text("Send Myanmar Specs:")
    return A_MY

async def admin_add_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_my'] = update.message.text_html
    await update.message.reply_text("Send a Photo:")
    return A_IMG

# --- THIS IS THE UPDATED FUNCTION ---
async def admin_add_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id if update.message.photo else update.message.text
    brand_id = context.user_data['new_brand_id']
    name = context.user_data['new_name']
    myr = context.user_data['new_myr']
    
    # Save the product to the database
    db.add_product(brand_id, name, myr, context.user_data['new_usdt'], context.user_data['new_en'], context.user_data['new_my'], file_id)
    await update.message.reply_text(f"✅ Added {name} to the database!")

    # Format the Automated Broadcast Message
    brand_name = db.get_brand_name(brand_id)
    try:
        myr_val = float(myr)
    except:
        myr_val = 0.0

    announcement_msg = (
        f"🚨 <b>NEW STOCK ARRIVAL!</b> 🚨\n\n"
        f"✨ <b>{brand_name} {name}</b> is now available in our catalog!\n"
        f"💰 <b>Starting at:</b> RM {myr_val:,.2f}\n\n"
        f"Open the bot menu to check out the full specs and reserve yours today! 🚀"
    )

    # Broadcast to all users
    users = db.get_all_users()
    await update.message.reply_text(f"🚀 Broadcasting New Stock Alert to {len(users)} users...")
    
    success_count = 0
    for u in users:
        try:
            if update.message.photo:
                await context.bot.send_photo(chat_id=u[0], photo=file_id, caption=announcement_msg, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=u[0], text=announcement_msg, parse_mode="HTML")
            success_count += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    await update.message.reply_text(f"✅ New stock alert successfully sent to {success_count} users!")
    return ConversationHandler.END


# --- EXPORTS ---

delete_product_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(del_p_start, pattern="^del_p_start$")],
    states={
        DEL_P_BRAND: [CallbackQueryHandler(del_p_brand, pattern="^dp_b_")],
        DEL_P_PROD: [CallbackQueryHandler(del_p_prod, pattern="^dp_p_")],
        DEL_P_CONFIRM: [CallbackQueryHandler(del_p_confirm, pattern="^dp_confirm$")]
    },
    fallbacks=[CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")]
)

delete_brand_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(del_b_start, pattern="^del_b_start$")],
    states={
        DEL_B_BRAND: [CallbackQueryHandler(del_b_brand, pattern="^db_b_")],
        DEL_B_CONFIRM: [CallbackQueryHandler(del_b_confirm, pattern="^db_confirm$")]
    },
    fallbacks=[CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")]
)

setstart_handler = ConversationHandler(
    entry_points=[CommandHandler("setstart", setstart_cmd)], 
    states={
        SET_START_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_start_msg)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

setmenu_en_handler = ConversationHandler(
    entry_points=[CommandHandler("setmenu_en", setmenu_en_cmd)], 
    states={
        SET_MENU_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_menu_en)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

setmenu_my_handler = ConversationHandler(
    entry_points=[CommandHandler("setmenu_my", setmenu_my_cmd)], 
    states={
        SET_MENU_MY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_menu_my)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

setmenu_img_handler = ConversationHandler(
    entry_points=[CommandHandler("setmenu_image", setmenu_img_cmd)], 
    states={
        SET_MENU_IMG: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, save_menu_img)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

add_brand_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_brand_start, pattern="^admin_add_brand_btn$")], 
    states={
        NEW_BRAND_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_brand_save)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

change_price_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(cp_start, pattern="^cp_start$"), 
        CommandHandler("changeprice", cp_start)
    ], 
    states={
        CP_BRAND: [CallbackQueryHandler(cp_brand, pattern="^cp_b_")], 
        CP_PROD: [CallbackQueryHandler(cp_prod, pattern="^cp_p_")], 
        CP_MYR: [MessageHandler(filters.TEXT & ~filters.COMMAND, cp_myr)], 
        CP_USDT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cp_usdt)]
    }, 
    fallbacks=[
        CommandHandler("cancel", admin_cancel), 
        CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
    ]
)

announce_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(ann_start, pattern="^ann_start$"), 
        CommandHandler("announce", ann_start)
    ], 
    states={
        ANN_MSG: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, ann_send)]
    }, 
    fallbacks=[CommandHandler("cancel", admin_cancel)]
)

add_product_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_add_start, pattern="^admin_add_start$")], 
    states={
        A_BRAND: [CallbackQueryHandler(admin_add_brand, pattern="^add_b_")], 
        A_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_name)], 
        A_MYR: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_myr)], 
        A_USDT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_usdt)], 
        A_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_en)], 
        A_MY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_my)], 
        A_IMG: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, admin_add_img)]
    }, 
    fallbacks=[
        CommandHandler("cancel", admin_cancel), 
        CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
    ]
)
