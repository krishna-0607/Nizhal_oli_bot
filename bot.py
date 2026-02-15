import logging
import re  # <--- ADD THIS LINE
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---------------- CONFIGURATION ---------------- #
# Replace with your token from BotFather
BOT_TOKEN = "7860937085:AAGfjTVjmfui0TJiHrWlx-xpv5p9h76DPrY"

# Replace with your Telegram User ID (See instructions below to find it)
ADMIN_ID = 1956361254 
# ----------------------------------------------- #

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message to the user."""
    user_id = update.effective_user.id
    
    # If the admin starts the bot, just confirm they are recognized
    if user_id == ADMIN_ID:
        await update.message.reply_text(f"Welcome, Admin! Your ID is {user_id}. I am ready to forward messages.")
    else:
        await update.message.reply_text("Hello! Send me a message (text, photo, etc.) and I will forward it to the admin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Core Logic:
    1. If message is from User -> Forward to Admin + Send ID tag.
    2. If message is from Admin (Reply) -> Copy content to User.
    """
    # Safety check: if update.effective_user is None (e.g. channel updates), ignore
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    
    # --- SCENARIO 1: Message from a Regular User ---
    if user_id != ADMIN_ID:
        # 1. Forward the content to the Admin
        forwarded_msg = await update.message.forward(chat_id=ADMIN_ID)
        
        # 2. Send a "Tag" message so the admin can reply to it easily
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👆 Message from: {update.effective_user.first_name} (ID: `{user_id}`)\nReply to THIS message to send an answer.",
            reply_to_message_id=forwarded_msg.message_id,
            parse_mode='Markdown'
        )

    # --- SCENARIO 2: Message from Admin (The Reply) ---
    else:
        # Check if the Admin is replying to a message
        if update.message.reply_to_message:
            original_message = update.message.reply_to_message
            
            # We try to extract the User ID using Regex (Find numbers after "ID:")
            try:
                text_content = original_message.text or original_message.caption
                
                # This regex looks for "ID:" followed by optional characters/spaces, then catches the numbers
                match = re.search(r"ID:.*?(\d+)", text_content)

                if match:
                    target_user_id = int(match.group(1))
                    
                    # Copy the Admin's message back to that user
                    await update.message.copy(chat_id=target_user_id)
                    
                    # Confirm to Admin
                    await update.message.reply_text("✅ Reply sent!")
                else:
                    await update.message.reply_text("⚠️ I couldn't find the User ID in that message. Are you replying to the bot's tag?")
            
            except Exception as e:
                logging.error(f"Error sending reply: {e}")
                await update.message.reply_text(f"❌ Failed to send. Error: {e}")
        else:
            # Admin sent a random message without replying
            await update.message.reply_text("To reply to a user, you must Reply to the message containing their ID.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    start_handler = CommandHandler('start', start)
    # This filter captures text, photos, video, audio, etc., but ignores commands (like /start)
    message_handler = MessageHandler(filters.ALL & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    print("Bot is running...")
    application.run_polling()