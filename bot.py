import asyncio
import logging
import os
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9015413956:AAHkhxf-CgbEYquiH0q-QsGFQWPBSPHJl84")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBwV0Jpf7ReYWcSVpjLuV8O-jJ6ZTXvc3A")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
أنت مستشار قانوني خبير ومختص حصرياً في نظام العمل السعودي ولائحته التنفيذية.
مهمتك استقبال استفسارات الموظفين وأصحاب العمل بأي صيغة أو لهجة كانت (فصحى، عامية سعودية، أو لهجات قبلية ومحلية دارجة).

قواعد العمل الصارمة:
1. افهم المقصد الحقيقي خلف الكلمات العامية والقبلية (مثلاً: "سحب على الدوام"، "طفش وطلع"، "كفيله ما نقل كفالته"، "فصلوه تعسفي") وترجمها للمفهوم النظامي الصحيح.
2. اعتمد حصرياً على نصوص نظام العمل السعودي ولائحته التنفيذية المعتمدين في المملكة العربية السعودية. لا تخترع أي معلومة أو مادة غير موجودة.
3. نظم إجابتك دائماً بهذا الشكل:
   📌 **المادة النظامية:** (رقم المادة).
   ⚖️ **الحكم في حالتك:** (شرح واضح ومباشر).
   📝 **التفصيل المختصر:** (شروط أو تفاصيل المادة إن وجدت).
4. أضف في نهاية أول رسالة تنبيهاً بأن هذا البوت استرشادي مبني على نظام العمل السعودي ولا يُغني عن الاستشارة القانونية الرسمية.
"""

law_file = None
if os.path.exists("labor_law.pdf"):
    try:
        law_file = client.files.upload(file="labor_law.pdf")
        logging.info("تم تحميل ملف نظام العمل بنجاح!")
    except Exception as e:
        logging.error(f"خطأ في رفع الملف: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        contents = [law_file, user_text] if law_file else [user_text]
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            )
        )
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("عذراً، حدث ضغط تقني بسيط. أعد إرسال سؤالك الآن.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("البوت يعمل الآن وجاهز لاستقبال الأسئلة...")
    app.run_polling(drop_pending_updates=True)
