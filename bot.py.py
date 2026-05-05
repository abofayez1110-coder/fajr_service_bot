import os
import logging
import tempfile
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
import yt_dlp
import instaloader

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")  # لازم يتحط في environment variable
CHANNEL_USERNAME = "@Zad_Elrooh"

# ================== LOGGING ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================== YTDL OPTIONS ==================
def get_ydl_opts(site_name):
    cookie_file = f"cookies_{site_name}.txt"

    return {
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
        'format': 'best[ext=mp4]/best',
        'nocheckcertificate': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'},
        'cookiefile': cookie_file if os.path.exists(cookie_file) else None,
        'quiet': True,
    }

# ================== CHECK MEMBERSHIP ==================
async def check_membership(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if chat_member.status in ["member", "administrator", "creator"]:
            return True

    except Exception as e:
        logging.warning(f"Membership check error: {e}")

    keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/Zad_Elrooh")]]
    await update.message.reply_text(
        "⚠️ لازم تشترك في القناة عشان البوت يشتغل",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return False

# ================== START ==================
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        return

    await update.message.reply_text(
        "🌹 يسعدنا مساعدتك بعد الصلاة على النبي\nابعت أي لينك من السوشيال"
    )

# ================== HANDLE LINK ==================
async def handle_link(update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        return

    url = update.message.text.strip()
    context.user_data["url"] = url

    await update.message.reply_text("⏳ جاري التحليل...")

    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        keyboard = [
            [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
            [InlineKeyboardButton("🎵 صوت", callback_data="audio")]
        ]
        await update.message.reply_text(
            "اختر النوع:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Instagram
    if "instagram.com" in url:
        await handle_instagram(update, url)
        return

    # Other platforms
    if any(x in url for x in ["tiktok.com", "facebook.com", "twitter.com"]):
        await handle_social(update, url)
        return

    await update.message.reply_text("⚠️ الرابط غير مدعوم")

# ================== INSTAGRAM ==================
async def handle_instagram(update, url):
    await update.message.reply_text("⏳ تحميل من إنستجرام...")

    try:
        loader = instaloader.Instaloader()

        shortcode = url.strip("/").split("/")[-1].split("?")[0]

        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        filename = os.path.join(tempfile.gettempdir(), f"{shortcode}.jpg")

        loader.download_post(post, target=tempfile.gettempdir())

        with open(filename, 'rb') as f:
            await update.message.reply_photo(f)

        os.remove(filename)

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ خطأ في إنستجرام")

# ================== OTHER SOCIAL ==================
async def handle_social(update, url):
    await update.message.reply_text("⏳ جاري التحميل...")

    try:
        site = (
            "tiktok" if "tiktok" in url
            else "facebook" if "facebook" in url
            else "twitter"
        )

        ydl_opts = get_ydl_opts(site)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            await update.message.reply_video(f)

        os.remove(filename)

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ خطأ في التحميل")

# ================== BUTTON HANDLER ==================
async def button_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")

    if not url:
        await query.edit_message_text("⚠️ مفيش لينك")
        return

    await query.edit_message_text("⏳ جاري المعالجة...")

    try:
        if query.data == "audio":
            ydl_opts = get_ydl_opts("youtube")
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = os.path.join(tempfile.gettempdir(), f"{info['id']}.mp3")

            with open(filename, 'rb') as f:
                await context.bot.send_audio(query.message.chat_id, audio=f)

            os.remove(filename)

        elif query.data == "video":
            ydl_opts = get_ydl_opts("youtube")
            ydl_opts['format'] = 'best[height<=720]'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, 'rb') as f:
                await context.bot.send_video(query.message.chat_id, video=f)

            os.remove(filename)

    except Exception as e:
        logging.error(e)
        await query.edit_message_text("❌ حصل خطأ")

# ================== MAIN ==================
def main():
    if not TOKEN:
        raise RuntimeError("Set TOKEN in environment variables")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🔥 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()