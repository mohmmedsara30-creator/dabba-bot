import os
import threading
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CODE = "Dabba2026"
ADMIN_CHAT_ID = None

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📝 شكوى", callback_data="complaint")],
        [InlineKeyboardButton("💡 اقتراح", callback_data="suggestion")],
        [InlineKeyboardButton("❓ استفسار", callback_data="question")],
        [InlineKeyboardButton("❤️ شكر وتقدير", callback_data="thanks")]
    ]

    await update.message.reply_text(
        "مرحبًا بك 🌷\n\n"
        "في بوت رابطة طلاب الدبة للاقتراحات والشكاوى.\n\n"
        "اختار/ي نوع الرسالة التي تريد/ين إرسالها:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global ADMIN_CHAT_ID

    if context.args and context.args[0] == ADMIN_CODE:

        ADMIN_CHAT_ID = update.effective_chat.id

        await update.message.reply_text(
            "✅ تم تسجيلك كمسؤولة البوت بنجاح.\n\n"
            "ستصلك رسائل الأعضاء هنا، ويمكنك الرد عليهم مباشرة."
        )

    else:

        await update.message.reply_text(
            "❌ رمز الإدارة غير صحيح."
        )


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    types = {
        "complaint": "شكوى",
        "suggestion": "اقتراح",
        "question": "استفسار",
        "thanks": "شكر وتقدير"
    }

    context.user_data["type"] = types[query.data]

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 إرسال باسمي",
                callback_data="named"
            )
        ],
        [
            InlineKeyboardButton(
                "🕊️ إرسال مجهول",
                callback_data="anonymous"
            )
        ]
    ]

    await query.edit_message_text(
        f"تم اختيار: {types[query.data]} ✅\n\n"
        "هل تريد/ين إرسال الرسالة باسمك أم بشكل مجهول؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose_identity(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["identity"] = query.data

    if query.data == "named":

        await query.edit_message_text(
            "👤 سيتم إرسال الرسالة باسمك.\n\n"
            "اكتب/ي رسالتك الآن:"
        )

    else:

        await query.edit_message_text(
            "🕊️ سيتم إرسال الرسالة بشكل مجهول.\n\n"
            "اكتب/ي رسالتك الآن:"
        )


def get_auto_reply(message_type):

    replies = {

        "استفسار":
            "🌷 شكرًا لاستفساركم.\n\n"
            "تم استلام استفساركم، وسيصلكم الرد من إدارة البوت قريبًا.",

        "شكوى":
            "🌷 شكرًا لتواصلكم معنا.\n\n"
            "تم استلام شكواكم، وسيتم متابعتها، وسيصلكم الرد من إدارة البوت.",

        "اقتراح":
            "🌷 شكرًا لكم على اقتراحكم.\n\n"
            "تم استلام اقتراحكم، وسيتم النظر فيه، وسيصلكم الرد من إدارة البوت.",

        "شكر وتقدير":
            "❤️ شكرًا لكم على كلماتكم الطيبة وتقديركم.\n\n"
            "نسعد دائمًا بتواصلكم معنا.\n\n"
            "#مكتب_شؤون_العضوية"
    }

    return replies.get(
        message_type,
        "🌷 شكرًا لتواصلكم معنا.\n\n"
        "تم استلام رسالتكم، وسيصلكم الرد من إدارة البوت."
    )


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global ADMIN_CHAT_ID

    if "type" not in context.user_data:
        return

    message_text = update.message.text
    message_type = context.user_data["type"]

    user = update.effective_user

    if context.user_data.get("identity") == "named":

        sender = user.full_name

        if user.username:
            sender += f"\n@{user.username}"

    else:

        sender = "🕊️ مجهول"

    admin_message = (
        "📩 رسالة جديدة\n"
        "━━━━━━━━━━━━━━\n\n"
        "📚 بوت رابطة طلاب الدبة للاقتراحات والشكاوى\n\n"
        f"📌 نوع الرسالة: {message_type}\n\n"
        f"👤 المرسل: {sender}\n\n"
        f"📝 الرسالة:\n{message_text}"
    )

    if ADMIN_CHAT_ID:

        keyboard = [
            [
                InlineKeyboardButton(
                    "↩️ الرد على العضو",
                    callback_data=f"reply_{user.id}"
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        auto_reply = get_auto_reply(message_type)

        await update.message.reply_text(
            "✅ تم إرسال رسالتك بنجاح.\n\n"
            + auto_reply
        )

    else:

        await update.message.reply_text(
            "⚠️ لم يتم تسجيل حساب الإدارة بعد."
        )

    context.user_data.clear()


async def start_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if ADMIN_CHAT_ID != query.message.chat.id:
        return

    user_id = int(
        query.data.replace("reply_", "")
    )

    context.user_data["replying_to"] = user_id

    await query.message.reply_text(
        "✍️ اكتب/ي الآن الرد الذي تريد/ين إرساله للعضو:"
    )


async def send_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global ADMIN_CHAT_ID

    if ADMIN_CHAT_ID != update.effective_chat.id:
        return

    if "replying_to" not in context.user_data:
        return

    user_id = context.user_data["replying_to"]
    reply_text = update.message.text

    try:

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "📚 رد من إدارة بوت رابطة طلاب الدبة:\n\n"
                f"{reply_text}"
            )
        )

        await update.message.reply_text(
            "✅ تم إرسال الرد للعضو بنجاح."
        )

    except Exception:

        await update.message.reply_text(
            "❌ تعذر إرسال الرد.\n\n"
            "قد يكون العضو قد قام بحظر البوت."
        )

    context.user_data.pop("replying_to", None)


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def main():

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register_admin", register_admin))
    application.add_handler(
        CallbackQueryHandler(
            choose_type,
            pattern="^(complaint|suggestion|question|thanks)$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            choose_identity,
            pattern="^(named|anonymous)$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            start_reply,
            pattern="^reply_[0-9]+$"
        )
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            send_admin_reply
        ),
        group=0
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_message
        ),
        group=1
    )

    print("🚀 البوت يعمل الآن...")

    application.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
