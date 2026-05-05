from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp
import instaloader
import os

# التوكن مباشر جوه الكود
TOKEN = "8790269629:AAESNyBH7sH5fxYsiDO6m51Sb8shshl6vh8"
CHANNEL_USERNAME = "@Zad_Elrooh"

async def check_membership(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            return True
        else:
            keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/Zad_Elrooh")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("⚠️ الرجاء الاشتراك ف القناه لضمان عمل البوت", reply_markup=reply_markup)
            return False
    except Exception:
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/Zad_Elrooh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ الرجاء الاشتراك ف القناه لضمان عمل البوت", reply_markup=reply_markup)
        return False

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        return
    await update.message.reply_text("🌹 يسعدنا مساعدتك بعد الصلاة علي النبي\nابعت أي لينك من السوشيال (يوتيوب، تيك توك، إنستجرام، تويتر، فيسبوك).")

async def handle_link(update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        return

    url = update.message.text.strip()
    context.user_data["url"] = url

    user_id = update.effective_user.id
    username = update.effective_user.username
    print(f"👤 UserID: {user_id}, Username: {username}, Link: {url}")
    if update.message.contact:
        phone = update.message.contact.phone_number
        print(f"📞 Phone: {phone}")

    await update.message.reply_text("⏳ الرجاء الانتظار ثانية للصلاة علي النبي")

    if "youtube.com" in url or "youtu.be" in url:
        keyboard = [
            [InlineKeyboardButton("🎬 فيديو كامل", callback_data="video")],
            [InlineKeyboardButton("🎵 صوت فقط", callback_data="audio")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختر نوع التحميل:", reply_markup=reply_markup)
        return

    if "instagram.com" in url:
        await update.message.reply_text("⏳ جاري التحميل من إنستجرام...")
        try:
            if "/p/" in url:  # صورة
                loader = instaloader.Instaloader(dirname_pattern=".", filename_pattern="{shortcode}")
                post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
                filename = f"{post.shortcode}.jpg"
                loader.download_post(post, target=".")
                await update.message.reply_photo(open(filename, 'rb'))
                os.remove(filename)
            else:  # فيديو
                ydl_opts = {
                    'outtmpl': '%(id)s.%(ext)s',
                    'format': 'best',
                    'nocheckcertificate': True,
                    'http_headers': {'User-Agent': 'Mozilla/5.0'},
                    'cookiefile': 'cookies_instagram.txt'
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                size_mb = os.path.getsize(filename) / (1024 * 1024)
                if size_mb <= 50:
                    await update.message.reply_video(open(filename, 'rb'))
                else:
                    await update.message.reply_text(f"⚠️ حجم الفيديو {size_mb:.2f}MB أكبر من الحد المسموح (50MB).")
                os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f"❌ حصل خطأ أثناء التحميل من إنستجرام: {e}")
        return

    if any(x in url for x in ["tiktok.com", "facebook.com", "twitter.com"]):
        await update.message.reply_text("⏳ جاري التحميل...")
        try:
            ydl_opts = {
                'outtmpl': '%(id)s.%(ext)s',
                'format': 'bestvideo[height<=480]+bestaudio/best',
                'nocheckcertificate': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0'},
                'cookiefile': 'cookies_youtube.txt'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            size_mb = os.path.getsize(filename) / (1024 * 1024)
            if size_mb <= 50:
                if filename.endswith(".mp4"):
                    await update.message.reply_video(open(filename, 'rb'))
                elif filename.endswith((".mp3", ".wav", ".m4a")):
                    await update.message.reply_audio(open(filename, 'rb'))
            else:
                os.remove(filename)
                ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                size_mb = os.path.getsize(filename) / (1024 * 1024)
                if size_mb <= 50:
                    await update.message.reply_video(open(filename, 'rb'))
                else:
                    await update.message.reply_text(f"⚠️ حجم الفيديو {size_mb:.2f}MB أكبر من الحد المسموح (50MB).")
            os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f"❌ حصل خطأ أثناء التحميل: {e}")
        return

    await update.message.reply_text("⚠️ الرابط مش مدعوم حالياً.")

async def button_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    choice = query.data
    url = context.user_data.get("url")

    if not url:
        await query.edit_message_text("⚠️ مفيش لينك محفوظ.")
        return

    try:
        await query.edit_message_text("⏳ الرجاء الانتظار ثانية للصلاة علي النبي")

        if choice == "audio":
            ydl_opts = {
                'outtmpl': '%(id)s.%(ext)s',
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'nocheckcertificate': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0'},
                'cookiefile': 'cookies_youtube.txt'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['id']}.mp3"

            await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(filename, 'rb'))
            os.remove(filename)

        elif choice == "video":
            ydl_opts = {
                'outtmpl': '%(id)s.%(ext)s',
                'format': 'bestvideo[height<=480]+bestaudio/best',
                'nocheckcertificate': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0'},
                'cookiefile': 'cookies_youtube.txt'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            size_mb = os.path.getsize(filename) / (1024 * 1024)
            if size_mb <= 50:
                await context.bot.send_video(chat_id=query.message.chat_id, video=open(filename, 'rb'))
            else:
                os.remove(filename)
                ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                size_mb = os.path.getsize(filename) / (1024 * 1024)
                if size_mb <= 50:
                    await context.bot.send_video(chat_id=query.message.chat_id, video=open(filename, 'rb'))
                else:
                    await query.edit_message_text(f"⚠️ حجم الفيديو {size_mb:.2f}MB أكبر من الحد المسموح (50MB).")
            os.remove(filename)

    except Exception as e:
        await query.edit_message_text(f"❌ حصل خطأ: {e}")

def main():
    app = Application.builder().
