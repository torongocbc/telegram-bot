
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configuração do logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Dicionário para armazenar as demandas ativas
demandas = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f'Olá, {user.first_name}! Eu sou o bot de gestão de demandas.')

async def nova_demanda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    descricao = ' '.join(context.args)
    if not descricao:
        await update.message.reply_text('Por favor, forneça uma descrição para a demanda após o comando /nova_demanda.')
        return

    keyboard = [
        [InlineKeyboardButton("Responder", callback_data=f"responder_{update.message.message_id}")],
        [InlineKeyboardButton("Cancelar Demanda", callback_data=f"cancelar_{update.message.message_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    mensagem = (
        f"📝 *Nova Demanda de {user.first_name} (@{user.username}):*\n"
        f"{descricao}\n\n"
        "💬 *Propostas:*"
    )
    msg = await update.message.reply_text(mensagem, parse_mode="Markdown", reply_markup=reply_markup)

    # Armazena a demanda
    demandas[msg.message_id] = {
        'criador_id': user.id,
        'descricao': descricao,
        'propostas': []
    }

    # Apaga a mensagem do comando original
    try:
        await update.message.delete()
    except Exception as e:
        logging.warning(f"Não foi possível apagar a mensagem do comando: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    # Extrai o tipo de ação e o ID da mensagem
    action, msg_id = query.data.split('_')
    msg_id = int(msg_id)

    if action == "responder":
        if msg_id in demandas:
            await query.message.reply_text('Por favor, envie sua proposta como uma resposta a esta mensagem.')
            context.user_data['respondendo'] = msg_id
        else:
            await query.message.reply_text('Esta demanda já foi encerrada ou não existe mais.')

    elif action == "cancelar":
        if msg_id in demandas and demandas[msg_id]['criador_id'] == user.id:
            await query.message.delete()
            del demandas[msg_id]
            await context.bot.send_message(update.effective_chat.id, 'A demanda foi cancelada pelo criador.')
        else:
            await query.message.reply_text('Apenas o criador da demanda pode cancelá-la.')

async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if 'respondendo' in context.user_data:
        msg_id = context.user_data['respondendo']
        if msg_id in demandas:
            proposta = update.message.text
            demandas[msg_id]['propostas'].append((user.first_name, proposta))
            await update.message.reply_text('Sua proposta foi registrada com sucesso.')
            del context.user_data['respondendo']
        else:
            await update.message.reply_text('A demanda para a qual você está tentando responder não existe mais.')
            del context.user_data['respondendo']

def main() -> None:
    application = Application.builder().token("7853403234:AAEQw7MUazTnc9667sQFE64Ex8gVurLT1bg").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("nova_demanda", nova_demanda))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))

    application.run_polling()
