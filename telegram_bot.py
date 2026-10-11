import os
import logging
from pathlib import Path
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import (
    TELEGRAM_BOT_TOKEN,
    UPLOADS_DIR,
    COMMUNITY_NAME,
    COMMUNITY_GITHUB,
    COMMUNITY_WEBSITE,
    COMMUNITY_TELEGRAM,
    COLLEGE_NAME
)
import database
from ai_analyzer import AIAnalyzer
from report_generator import format_telegram_response, generate_pdf_report

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FOSSBot")

# Initialize AI Engine & Database
ai = AIAnalyzer()
database.init_db()

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the standard interactive main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🌿 Git Quickref", callback_data="menu_git"),
            InlineKeyboardButton("🐧 Linux Essentials", callback_data="menu_linux")
        ],
        [
            InlineKeyboardButton("📜 FOSS Licenses", callback_data="menu_licenses"),
            InlineKeyboardButton("🌟 GSoC & Programs", callback_data="menu_programs")
        ],
        [
            InlineKeyboardButton("📊 Community Stats", callback_data="menu_stats"),
            InlineKeyboardButton("🌐 FOSS MBCCET Org", callback_data="menu_community")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_response_actions_keyboard(query_id: int) -> InlineKeyboardMarkup:
    """Action buttons attached beneath every resolved doubt."""
    keyboard = [
        [
            InlineKeyboardButton("👍 Solved It", callback_data=f"fb_up_{query_id}"),
            InlineKeyboardButton("👎 Still Confused", callback_data=f"fb_down_{query_id}")
        ],
        [
            InlineKeyboardButton("📄 Download PDF Report", callback_data=f"pdf_{query_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    if user:
        database.register_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

    welcome_text = (
        f"🐧 <b>Welcome to {COMMUNITY_NAME}!</b>\n"
        f"<i>The Open Source Knowledge & Doubt Solver for {COLLEGE_NAME}</i>\n\n"
        f"Hello <b>{user.first_name if user else 'Hacker'}</b>! I am <b>Tuxie</b>, your 24/7 FOSS mentor.\n\n"
        f"<b>What I can do for you:</b>\n"
        f"• 💡 <b>Ask Any Doubt:</b> Type your coding or open source question directly.\n"
        f"• 📸 <b>Screenshot Diagnostic:</b> Send a photo of your terminal error, compiler bug, or Git conflict.\n"
        f"• 🌿 <b>Git & GitHub:</b> Master branching, rebasing, and merge conflicts.\n"
        f"• 🐧 <b>Linux CLI:</b> Permissions (chmod), bash scripts, systemctl.\n"
        f"• 📜 <b>FOSS Licensing:</b> Understand GPLv3, MIT, Apache, and Copyleft.\n"
        f"• 🌟 <b>GSoC & Hacktoberfest:</b> How to find issues and make your first PR.\n\n"
        f"👇 <i>Choose a topic below or type your question directly:</i>"
    )

    await update.message.reply_html(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    help_text = (
        f"📖 <b>{COMMUNITY_NAME} Bot Guide</b>\n\n"
        f"<b>Available Commands:</b>\n"
        f"• <code>/start</code> - Restart bot & open main navigation\n"
        f"• <code>/ask &lt;question&gt;</code> - Submit a specific technical doubt\n"
        f"• <code>/classify &lt;topic&gt;</code> - Categorize any doubt & view suggested tags\n"
        f"• <code>/git</code> - Git cheat sheet & workflow guide\n"
        f"• <code>/linux</code> - Essential Linux commands & permissions\n"
        f"• <code>/licenses</code> - Open source license breakdown\n"
        f"• <code>/programs</code> - Guide to GSoC, Hacktoberfest & Outreachy\n"
        f"• <code>/stats</code> - Live community doubts statistics\n"
        f"• <code>/community</code> - FOSS MBCCET GitHub and channels\n"
        f"• <code>/help</code> - Show this manual\n\n"
        f"💡 <i>Tip: You don't even need to type /ask! Just send your question or screenshot directly.</i>"
    )
    await update.message.reply_html(help_text)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /ask <query>."""
    if not context.args:
        await update.message.reply_html(
            "⚠️ <b>Please include your question!</b>\nExample: <code>/ask How do I resolve a Git merge conflict?</code>"
        )
        return

    query_text = " ".join(context.args)
    await process_text_query(update, query_text)

async def classify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /classify <query> to return structured categorization."""
    if not context.args:
        await update.message.reply_html(
            "⚠️ <b>Please specify what to classify!</b>\nExample: <code>/classify What is the difference between MIT and GPL?</code>"
        )
        return

    query_text = " ".join(context.args)
    await update.message.reply_chat_action(constants.ChatAction.TYPING)

    classification = ai.classify_query(query_text)
    tags_formatted = " ".join([f"#{t}" for t in classification.get("tags", [])])
    tools_formatted = ", ".join(classification.get("foss_tools", []))

    response = (
        f"🏷️ <b>Topic Classification</b>\n\n"
        f"📂 <b>Category:</b> {classification.get('category')}\n"
        f"🔹 <b>Subcategory:</b> {classification.get('subcategory')}\n"
        f"📊 <b>Complexity:</b> {classification.get('difficulty')}\n"
        f"🏷️ <b>Tags:</b> {tags_formatted}\n"
        f"🛠️ <b>Relevant FOSS Tools:</b> {tools_formatted}\n\n"
        f"<i>Want the full pedagogical explanation? Simply type: /ask {query_text}</i>"
    )
    await update.message.reply_html(response)

async def git_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /git quick reference."""
    resource = database.get_resource("git")
    text = resource["content"] if resource else "Git essentials cheat sheet."
    await update.message.reply_html(
        f"🌿 <b>Git & Version Control Quickref</b>\n\n<pre><code>{text}</code></pre>"
    )

async def linux_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /linux essentials."""
    resource = database.get_resource("linux")
    text = resource["content"] if resource else "Linux commands."
    await update.message.reply_html(
        f"🐧 <b>Linux Command Essentials</b>\n\n<pre><code>{text}</code></pre>"
    )

async def licenses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /licenses guide."""
    resource = database.get_resource("licenses")
    text = resource["content"] if resource else "Open source licenses."
    await update.message.reply_html(
        f"📜 <b>Open Source Licenses Guide</b>\n\n{text}"
    )

async def programs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /programs guide."""
    resource = database.get_resource("programs")
    text = resource["content"] if resource else "Open source programs."
    await update.message.reply_html(
        f"🌟 <b>Open Source Mentorship Programs</b>\n\n{text}"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /stats live community metrics."""
    stats = database.get_community_stats()
    
    cat_lines = []
    for cat in stats.get("categories", [])[:5]:
        cat_lines.append(f"• {cat['category']}: <b>{cat['count']}</b>")
    categories_str = "\n".join(cat_lines) if cat_lines else "No queries logged yet."

    stats_msg = (
        f"📊 <b>{COMMUNITY_NAME} • Live Community Pulse</b>\n\n"
        f"👥 <b>Active Students:</b> {stats.get('total_students', 0)}\n"
        f"💡 <b>Total Doubts Resolved:</b> {stats.get('total_doubts_resolved', 0)}\n"
        f"📸 <b>Screenshots Diagnosed:</b> {stats.get('code_screenshots_analyzed', 0)}\n\n"
        f"🏆 <b>Top Query Topics:</b>\n{categories_str}\n\n"
        f"<i>Keep asking, hacking, and sharing open source knowledge!</i>"
    )
    await update.message.reply_html(stats_msg)

async def community_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /community info."""
    comm_msg = (
        f"🌐 <b>{COMMUNITY_NAME} Community Hub</b>\n"
        f"<i>{COLLEGE_NAME}</i>\n\n"
        f"• <b>GitHub Org:</b> {COMMUNITY_GITHUB}\n"
        f"• <b>Official Website:</b> {COMMUNITY_WEBSITE}\n"
        f"• <b>Telegram Group:</b> {COMMUNITY_TELEGRAM}\n\n"
        f"🤝 Join our regular hackathons, install fests, and open-source contribution sprints!"
    )
    await update.message.reply_html(comm_msg)

# ==================== MESSAGE PROCESSING ====================

async def process_text_query(update: Update, query_text: str):
    """Common helper to process, log, and respond to text queries."""
    user = update.effective_user
    user_id = user.id if user else None
    
    if user:
        database.register_or_update_user(user.id, user.username, user.first_name, user.last_name)

    # Show typing indicator while AI processes
    await update.message.reply_chat_action(constants.ChatAction.TYPING)

    # Run AI reasoning
    analysis = ai.analyze_text_query(query_text)

    # Log to SQLite
    query_id = database.log_query(
        telegram_id=user_id,
        query_type="text",
        query_text=query_text,
        response_text=analysis.get("direct_answer", ""),
        category=analysis.get("category", "General FOSS"),
        subcategory=analysis.get("subcategory", "General"),
        difficulty=analysis.get("difficulty", "Beginner"),
        tags=analysis.get("tags", [])
    )

    # Format HTML response
    formatted_msg = format_telegram_response(analysis, query_id=query_id)
    reply_markup = get_response_actions_keyboard(query_id)

    await update.message.reply_html(formatted_msg, reply_markup=reply_markup)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages as natural language queries."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    await process_text_query(update, text)

async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photos & screenshots of code or terminal errors."""
    user = update.effective_user
    user_id = user.id if user else None

    if user:
        database.register_or_update_user(user.id, user.username, user.first_name, user.last_name)

    caption = update.message.caption or ""

    # Send status
    status_msg = await update.message.reply_html("🔍 <i>Tuxie is inspecting your screenshot & running diagnostics...</i>")
    await update.message.reply_chat_action(constants.ChatAction.UPLOAD_PHOTO)

    # Download highest-resolution photo
    photo = update.message.photo[-1]
    file = await photo.get_file()

    filename = f"screenshot_{user_id}_{photo.file_unique_id}.jpg"
    local_path = UPLOADS_DIR / filename
    await file.download_to_drive(str(local_path))

    # Run Multimodal AI Vision
    analysis = ai.analyze_image_query(str(local_path), caption=caption)

    # Log in SQLite
    query_id = database.log_query(
        telegram_id=user_id,
        query_type="photo",
        query_text=caption if caption else "Code/Terminal Screenshot Diagnostic",
        response_text=analysis.get("direct_answer", ""),
        category=analysis.get("category", "Programming & Bug Debugging"),
        subcategory=analysis.get("subcategory", "Visual Diagnosis"),
        difficulty=analysis.get("difficulty", "Intermediate"),
        tags=analysis.get("tags", []),
        image_path=str(local_path)
    )

    # Format Response
    formatted_msg = format_telegram_response(analysis, query_id=query_id)
    reply_markup = get_response_actions_keyboard(query_id)

    # Edit status message or send reply
    await status_msg.delete()
    await update.message.reply_html(formatted_msg, reply_markup=reply_markup)

# ==================== CALLBACK QUERY HANDLER ====================

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks for feedback, cheat sheets, and PDF export."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user
    user_id = user.id if user else 0

    if data.startswith("fb_up_"):
        query_id = int(data.split("_")[-1])
        database.add_feedback(query_id, user_id, 1)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_html("🎉 <b>Glad that resolved your doubt! Happy open-source hacking!</b>")

    elif data.startswith("fb_down_"):
        query_id = int(data.split("_")[-1])
        database.add_feedback(query_id, user_id, -1)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_html("🙏 <b>Thanks for the feedback. Feel free to rephrase or send a screenshot so I can dig deeper!</b>")

    elif data.startswith("pdf_"):
        query_id = int(data.split("_")[-1])
        # Generate PDF report for this query
        recent = database.get_recent_queries(limit=50)
        selected = next((q for q in recent if q["id"] == query_id), None)
        
        if selected:
            await query.message.reply_chat_action(constants.ChatAction.UPLOAD_DOCUMENT)
            analysis = {
                "category": selected.get("category"),
                "subcategory": selected.get("subcategory"),
                "difficulty": selected.get("difficulty"),
                "direct_answer": selected.get("snippet", ""),
                "terminal_commands_or_code": "",
                "recommended_foss_tools": [],
                "foss_tip": "Keep learning and contributing to open source software!"
            }
            pdf_path = generate_pdf_report(
                analysis=analysis,
                query_text=selected.get("query_text", ""),
                student_name=user.first_name if user else "FOSS Student"
            )
            with open(pdf_path, "rb") as doc:
                await query.message.reply_document(
                    document=doc,
                    filename=Path(pdf_path).name,
                    caption=f"📄 Here is your technical reference card for Query #{query_id}."
                )
        else:
            await query.message.reply_html("⚠️ Could not locate query reference for PDF generation.")

    elif data == "menu_git":
        await git_command(update, context)
    elif data == "menu_linux":
        await linux_command(update, context)
    elif data == "menu_licenses":
        await licenses_command(update, context)
    elif data == "menu_programs":
        await programs_command(update, context)
    elif data == "menu_stats":
        await stats_command(update, context)
    elif data == "menu_community":
        await community_command(update, context)

def build_bot_application() -> Application:
    """Builds and registers handlers for the Telegram application."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot will not connect to Telegram until configured.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN or "DUMMY_TOKEN").build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("classify", classify_command))
    app.add_handler(CommandHandler("git", git_command))
    app.add_handler(CommandHandler("linux", linux_command))
    app.add_handler(CommandHandler("licenses", licenses_command))
    app.add_handler(CommandHandler("license", licenses_command))
    app.add_handler(CommandHandler("programs", programs_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("community", community_command))

    # Media & Text
    app.add_handler(MessageHandler(filters.PHOTO, photo_message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    # Callbacks
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    return app

def main():
    """Runs the Telegram bot daemon."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "DUMMY_TOKEN":
        print("\n=======================================================")
        print("⚠️  TELEGRAM_BOT_TOKEN is not set in .env or environment!")
        print("Please set TELEGRAM_BOT_TOKEN to launch the live Telegram daemon.")
        print("=======================================================\n")
        return

    logger.info("Starting FOSS MBCCET Telegram Bot Daemon...")
    app = build_bot_application()
    app.run_polling()

if __name__ == "__main__":
    main()
