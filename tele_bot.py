import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from image_detection import analyze_document_with_llama_vision 
load_dotenv()

# Set up logging for the bot. This helps with debugging.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
groq_api_key = os.environ.get("groq_api_key")



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(f"Please send a photo of the civic issue you want to report.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help! Send a photo of the civic issue you want to report.")



async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming photos, downloads the largest size, and saves it."""
    global file_path
    logger.info("Received a photo from user %s", update.effective_user.first_name)
    photo_file = await update.message.photo[-1].get_file()
    download_dir = "downloaded_images"
    os.makedirs(download_dir, exist_ok=True)
    # Define the file path where the image will be saved.
    # We use the file_unique_id to ensure a unique filename.
    file_path = os.path.join(download_dir, f"{photo_file.file_unique_id}.jpg")
    # Download the file to the specified path.
    # The download_to_drive() method handles the download asynchronously.
    await photo_file.download_to_drive(file_path)
    #SENDS THE IMAGE TO BE ANALYZED
    response = analyze_document_with_llama_vision(file_path, groq_api_key)

    # Acknowledge the download to the user.
    await update.message.reply_text(f"Thank you! Your report has been submitted.: {response}")
    with open('img.txt','w+') as file:
        file.write(f'{file_path}')
        file.close()

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming location messages."""
    user_location = update.message.location
    if user_location:
        latitude = user_location.latitude
        longitude = user_location.longitude
        logger.info("Received location from user %s: (%f, %f)", update.effective_user.first_name, latitude, longitude)
        await update.message.reply_text(f"Location received: Latitude {latitude}, Longitude {longitude}")
    else:
        await update.message.reply_text("No location data found.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    # RESPONSES
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start_command))
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/help$'), help_command))   
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    # Run the bot until the user presses Ctrl-C.
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
