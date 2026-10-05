# main.py
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import config
import database as db
import user
import admin

def main():
    db.init_db()
    app = Application.builder().token(config.TOKEN).read_timeout(30).write_timeout(30).connect_timeout(30).build()

    # User Routes
    app.add_handler(CommandHandler("start", user.start))
    app.add_handler(CallbackQueryHandler(user.start, pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(user.main_menu, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(user.main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(user.show_brands, pattern="^show_brands$"))
    app.add_handler(CallbackQueryHandler(user.show_models, pattern="^brand_"))
    app.add_handler(CallbackQueryHandler(user.show_product_card, pattern="^prod_"))

    # Admin Direct Commands
    app.add_handler(CommandHandler("myid", admin.get_my_id))
    app.add_handler(CommandHandler("admin", admin.admin_panel))
    app.add_handler(CommandHandler("users", admin.admin_users_list))
    
    # Admin Callbacks for pure buttons
    app.add_handler(CallbackQueryHandler(admin.admin_cancel, pattern="^admin_cancel$"))
    app.add_handler(CallbackQueryHandler(admin.admin_users_list, pattern="^admin_users$"))

    # Admin Conversation Wizards
    app.add_handler(admin.setstart_handler)
    app.add_handler(admin.setmenu_en_handler)
    app.add_handler(admin.setmenu_my_handler)
    app.add_handler(admin.setmenu_img_handler)
    app.add_handler(admin.add_brand_handler)
    app.add_handler(admin.change_price_handler)
    app.add_handler(admin.announce_handler)
    app.add_handler(admin.add_product_handler)
    app.add_handler(admin.delete_product_handler)
    app.add_handler(admin.delete_brand_handler)

    print("🚀 Bot is running! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()
