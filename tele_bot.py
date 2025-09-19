import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler,CommandHandler,ConversationHandler, filters, ContextTypes
from dotenv import load_dotenv
from processing import analyze_document_with_llama_vision , content, address_to_location
load_dotenv()

# Set up logging for the bot. This helps with debugging.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
groq_api_key = os.environ.get("groq_api_key")

from telegram.ext import ConversationHandler, CommandHandler

# States
PHOTO, LOCATION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please send a photo of the civic issue.")
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    def sanitize_model_output(s: str) -> str:
        s = s.strip()
        if s.startswith("```"):
            # remove fences like ```json or ```
            s = s.split("\n", 1)[1]  # drop first line (```json)
            if s.endswith("```"):
                s = s.rsplit("\n", 1)[0]  # drop last line (```)
        return s.strip()

    logger.info("Received a photo from user %s", update.effective_user.first_name)
    photo_file = await update.message.photo[-1].get_file()
    download_dir = "downloaded_images"
    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, f"{photo_file.file_unique_id}.jpg")
    await photo_file.download_to_drive(file_path)
    context.user_data['photo_path'] = file_path
    summary = await asyncio.to_thread(analyze_document_with_llama_vision,file_path, groq_api_key)
    summary = sanitize_model_output(summary)
    context.user_data['summary'] = summary
    await update.message.reply_text("Great! Now send the location.")
    return LOCATION

async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    user_location = update.message.location
    if not user_location:
        await update.message.reply_text("Please send a location using the location button.")
        return LOCATION
    
    photo_path = context.user_data.get('photo_path')
    summary = context.user_data.get('summary')
    
    loc = {
        "latitude": user_location.latitude,
        "longitude": user_location.longitude
    }
    print(f"Location received: {loc}")
    response = await asyncio.to_thread(content, summary, loc,groq_api_key)
    await update.message.reply_text(f"Generated Tweet: {response}")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
            LOCATION: [MessageHandler(filters.LOCATION, location_received)]
        },
        fallbacks=[]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
