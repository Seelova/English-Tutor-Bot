from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler,ContextTypes,filters
import tempfile
import os
from google import genai

from utils import store_answer, get_current_dialog, get_random_line
from config import telegram_api_key, gemini_api_key

# Обработка /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - начинается диалог
       - выбирается тема
       - генерируется первое сообщение диалога """
    print("start handler")
    
    # удаляем историю диалога
    with open(r'dialog.txt', 'w', encoding='utf-8') as file:
        file.write("")

    # print(update.message.from_user.id, update.message.from_user.username)

    topic = get_random_line("dialog_topics.txt")
    
    with open(r'prompts\welcome_phrase_prompt.txt', 'r', encoding='utf-8') as file:
        welcome_prompt_txt = file.read()
    
    final_welcome_prompt = welcome_prompt_txt + topic

    client = genai.Client(api_key=gemini_api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[final_welcome_prompt]
    )
    generated_welcome_phrase = response.text
    generated_welcome_phrase = generated_welcome_phrase.replace("*","")

    await update.message.reply_text(
        generated_welcome_phrase
    )

    store_answer("You", generated_welcome_phrase)


async def transcribe_audio(audio_file_path):
    """Транскрибация аудио с помощью Gemini Flash"""
    client = genai.Client(api_key=gemini_api_key)

    myfile = client.files.upload(file=audio_file_path)

    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=["Generate a transcript of the speech.", myfile]
                    )
    transcribed_text = response.text

    return transcribed_text


# Обработка голосовых сообщений
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает голосовые сообщения и отправляет расшифровку."""
    print("voice handler")
    voice = update.message.voice
    voice_file = await context.bot.get_file(voice.file_id)
    
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
        temp_audio_path = temp_audio.name

    await voice_file.download_to_drive(temp_audio_path)
    
    try:
        transcript = await transcribe_audio(temp_audio_path)
        await update.message.reply_text(f"Transcript: {transcript}")
        store_answer("User", transcript)

        #продолжение диалога
        with open(r'prompts\next_dialog_phrase_prompt.txt', 'r', encoding='utf-8') as file:
            next_phrase_prompt = file.read()
        
        dialog = get_current_dialog()
        prompt = next_phrase_prompt + dialog + "You:\nGenerate your next answer"
        client = genai.Client(api_key=gemini_api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=[prompt]
        )
        generated_welcome_phrase = response.text

        await update.message.reply_text(
            generated_welcome_phrase
        )

        store_answer("You", generated_welcome_phrase)

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при расшифровке: {str(e)}")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# Обработка текстовых сообщений
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения."""
    print("text handler")
    user_text = update.message.text
    store_answer("User", user_text)

    # продолжение диалога
    with open(r'prompts\next_dialog_phrase_prompt.txt', 'r', encoding='utf-8') as file:
        next_phrase_prompt = file.read()
    
    dialog = get_current_dialog()
    prompt = next_phrase_prompt + dialog + "You:\nGenerate your next answer"
    client = genai.Client(api_key=gemini_api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=[prompt]
    )
    generated_welcome_phrase = response.text

    await update.message.reply_text(
        generated_welcome_phrase
    )

    store_answer("You", generated_welcome_phrase)


# Обработка feedback
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    dialog = get_current_dialog()
    if len(dialog) == 0:
        await update.message.reply_text(
        "Sorry, there is no dialog with you to have feedback :(.\nText /start to start a dialog with me!"
    )
    else:
        with open(r'prompts\feedback_prompt.txt', 'r', encoding='utf-8') as file:
                feedback_prompt = file.read()
        prompt = feedback_prompt + dialog + "You:\n"

        client = genai.Client(api_key=gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=[prompt]
        )
        generated_feedback = response.text

        await update.message.reply_text(
            generated_feedback
        )

        store_answer("You", generated_feedback)



def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(telegram_api_key).build()
    print("Я запущен")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(CommandHandler("feedback", feedback))

    application.run_polling()


if __name__ == "__main__":
    main()