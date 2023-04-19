import os
import telegram
from telegram.ext import (
    ConversationHandler,
    Application,
    MessageHandler,
    CommandHandler,
    filters
)
from consts import BOT_TOKEN
from storage_api_controller import get_files_list, upload_file, download_file

UPLOAD_FILE, FILENAME, VIEW_FILES, DOWNLOAD_FILE = range(4)


async def start(update, context):
    keyboard = [
        [telegram.KeyboardButton('/view_photos_list')],
        [telegram.KeyboardButton('/upload_photo')],
        [telegram.KeyboardButton('/download_photo')],
    ]

    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Обери одну з команд нижче:',
        reply_markup=reply_markup
    )


async def handle_view_photos(update, context):
    files_list = '\n\n'.join(get_files_list())
    await update.message.reply_text(
        f"Наявні фото: \n{files_list}" if files_list else 'Поки немає жодної фотографії'
    )
    await start(update, context)


async def ask_for_filename(update, context):
    await update.message.reply_text(
        'Надішліть назву з якою буде збереженне фото'
        )
    return FILENAME


async def record_filename(update, context):
    filename = update.message.text.strip()
    context.user_data['filename'] = filename
    await update.message.reply_text("Надішліть фото")
    return UPLOAD_FILE


async def handle_photos(update, context):
    photos = update.message.photo
    photo = photos[-1]

    filename = context.user_data['filename']
    file_name = f"{filename}.jpg"

    file_data = await photo.get_file()
    file_data = await file_data.download_as_bytearray()

    with open(file_name, "wb") as f:
        f.write(file_data)

    upload_file(file_name)

    os.remove(file_name)

    await update.message.reply_text(
        "Фото успішно завантажено до Google Cloud Storage!"
    )
    await start(update, context)
    return ConversationHandler.END


async def choose_file(update, context):
    files_list = get_files_list()
    if not files_list:
        await update.message.reply_text('Поки немає жодної фотографії')
        await start(update, context)
        return ConversationHandler.END

    keyboard = [
        [telegram.KeyboardButton(file)] for file in files_list
    ]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Оберіть файл, який бажаєте завантажити",
        reply_markup=reply_markup
    )
    return DOWNLOAD_FILE


async def handle_download_file(update, context):
    file_name = update.message.text.strip()
    download_file(file_name)

    with open(file_name, "rb") as f:
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=f
        )

    os.remove(file_name)

    await start(update, context)
    return ConversationHandler.END

if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(ConversationHandler(
            entry_points=[CommandHandler('upload_photo', ask_for_filename)],
            states={
                FILENAME: [MessageHandler(filters.TEXT, record_filename)],
                UPLOAD_FILE: [MessageHandler(filters.PHOTO, handle_photos)],
            },
            fallbacks=[],
        ))
    application.add_handler(ConversationHandler(
            entry_points=[CommandHandler('download_photo', choose_file)],
            states={
                DOWNLOAD_FILE: [
                    MessageHandler(filters.TEXT, handle_download_file)
                    ],
            },
            fallbacks=[],
        ))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photos))
    application.add_handler(
        CommandHandler("view_photos_list", handle_view_photos)
        )
    application.add_handler(CommandHandler('start', start))

    application.run_polling(1.0)
