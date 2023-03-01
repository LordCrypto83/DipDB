#!/bin/bash
import telegram.constants
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from bot_functions import *


MENU, SET_CHAIN, SET_TOKEN_ADDRESS, SET_DIP, CONFIRM, DELETE = range(6)
BSC, ETH = range(2)
YES, NO = range(2)
DIP_DETECT, SHOW_DETECT, CANCEL_DETECT, ABOUT, BACK = range(5)
logo = "<b>\U0001F575 Dip Detector Bot \U0001F575</b>\n"
parse_mode = telegram.constants.ParseMode.HTML


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
    except Exception as e:
        pass

    chat_type = str(update.effective_message.chat.type)

    if chat_type != "private":
        keyboard = [[InlineKeyboardButton(
            text="Visit our website to learn more", url="https://dipdetectorbot.tech/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"\n<i>Never miss a DIP again!</i>\n\nSend me a DM to get started!",
                                       reply_markup=reply_markup,
                                       parse_mode=parse_mode)
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("SET", callback_data=str(DIP_DETECT)),
            InlineKeyboardButton("SHOW", callback_data=str(SHOW_DETECT)),
            InlineKeyboardButton("CANCEL", callback_data=str(CANCEL_DETECT)),
            InlineKeyboardButton("ABOUT", callback_data=str(ABOUT)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=logo+"Choose from the Menu options below:",
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)
    return MENU


async def detect_dip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_check(user_id)
    keyboard = [
        [
            InlineKeyboardButton("BSC", callback_data=str(BSC)),
            InlineKeyboardButton("ETH", callback_data=str(ETH)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=logo+"Let's get started...\nSelect <b>BSC</b> or <b>ETH</b> Chain:",
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)
    return SET_CHAIN


async def set_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    query = update.callback_query
    await query.answer()
    select = update.callback_query.data
    chain = "bsc" if select == "0" else "eth"
    sqlStr = """Update users set chain = ? where id = ?"""
    updateSQL(sqlStr, (chain, user_id))
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=logo+"Enter the <b>Token Address</b>:",
                                   parse_mode=parse_mode)
    return SET_TOKEN_ADDRESS


async def set_token_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    token_address = update.message.text
    data = get_user_data(user_id)[0]
    chain = data[5]
    symbol = token_check(token_address, chain)
    if symbol == None:
        sql = f"""DELETE FROM users WHERE id='{user_id}'"""
        deleteSQL(sql)
        await context.bot.send_message(chat_id=update.message.chat_id,
                                       text=logo+"OOPS! That's an invalid Token Address...",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)
        return MENU
    set_price = get_token_price(token_address, chain)
    set_price = str(set_price)
    sqlStr = """Update users set address = ?, symbol = ?, set_price = ? where id = ?"""
    updateSQL(sqlStr, (token_address, symbol, set_price, user_id))
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text=f"{logo}<b>Current Price</b> of {symbol} is {set_price}.\nEnter your target <b>Dip Price</b>:",
                                   parse_mode=parse_mode)
    return SET_DIP


async def set_dip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    dip_price = update.message.text
    user_data = get_user_data(user_id)[0]
    address = user_data[1]
    symbol = user_data[2]
    set_price = user_data[3]

    try:
        float_test = float(dip_price)
    except:
        sql = f"""DELETE FROM users WHERE id='{user_id}'"""
        deleteSQL(sql)
        await context.bot.send_message(chat_id=update.message.chat_id,
                                    text=logo+"Invalid entry!\nDip Price MUST be a number...",
                                    reply_markup=back_button(),
                                    parse_mode=parse_mode)
        return MENU
    
    if float(dip_price) > float(set_price):
        sql = f"""DELETE FROM users WHERE id='{user_id}'"""
        deleteSQL(sql)
        await context.bot.send_message(chat_id=update.message.chat_id,
                                    text=logo+"Invalid entry!\nDip Price MUST be lower than the Current Price...",
                                    reply_markup=back_button(),
                                    parse_mode=parse_mode)
        return MENU
    sql = ''' UPDATE users set dip_price = ? where id = ? '''
    updateSQL(sql, (dip_price, user_id))

    keyboard = [
        [
            InlineKeyboardButton("YES", callback_data=str(YES)),
            InlineKeyboardButton("NO", callback_data=str(NO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text=f"{logo}<b><u>Please confirm the following:</u></b>\n<b>Token Address:</b>\n{address}\n<b>Symbol:</b>\n{symbol}\n<b>Current Price:</b>\n{set_price}\n<b>Target Dip Price:</b>\n{dip_price}",
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    query = update.callback_query
    await query.answer()
    response = update.callback_query.data

    if response == "1":
        sql = f"""DELETE FROM users WHERE id='{user_id}'"""
        deleteSQL(sql)
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"Okay no problem! Try again later!",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)

    if response == "0":
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"\U0001F3AF Target Acquired! \U0001F3AF \nThanks for using <b>Dip Detector Bot</b>!\nYou will be notified when your DIP is detected!",
                                       parse_mode=parse_mode)
    return ConversationHandler.END


async def show_detect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)

    if not user_data:
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"No active Dip targets.",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)
        return MENU
    user_data = user_data[0]
    id = user_data[0]
    address = user_data[1]
    symbol = user_data[2]
    dip_price = user_data[4]
    chain = user_data[5]

    if not dip_price:
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"No active Dip targets.",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)
        sql = f"""DELETE FROM users WHERE id='{id}'"""
        deleteSQL(sql)
        return MENU

    current_price = get_token_price(address, chain)
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=f"{logo}<b><u>Your Dips:</u></b>\n<b>Chain:</b>\n{chain}\n<b>Token Address:</b>\n{address}\n<b>Symbol:</b>\n{symbol}\n<b>Current Price:</b>\n{str(current_price)}\n<b>Target Dip Price:</b>\n{dip_price}",
                                   reply_markup=back_button(),
                                   parse_mode=parse_mode)
    return MENU


async def cancel_detect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    if not user_data:
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"No active Dip targets.",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)
        return MENU
    user_data = user_data[0]
    symbol = user_data[2]
    dip_price = user_data[4]

    keyboard = [
        [
            InlineKeyboardButton("YES", callback_data=str(YES)),
            InlineKeyboardButton("NO", callback_data=str(NO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=f"{logo}You are currently tracking {symbol} with a Dip Price of {dip_price}.\nDo you want to cancel?",
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)

    return DELETE


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    query = update.callback_query
    await query.answer()
    response = update.callback_query.data

    if response == "1":
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"Dip Detect wasn't canceled!",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)

    if response == "0":
        sql = f"""DELETE FROM users WHERE id='{user_id}'"""
        deleteSQL(sql)
        await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                       text=logo+"Your Dip Detect was canceled. Come back soon!",
                                       reply_markup=back_button(),
                                       parse_mode=parse_mode)

    return MENU


async def about_ddb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(text="WEBSITE", url="https://dipdetectorbot.tech/"),
                 InlineKeyboardButton("BACK", callback_data=str(BACK)), ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=logo+"\n<i>Never miss a DIP again!</i>\n\nCheck out our website to learn more!",
                                   reply_markup=reply_markup,
                                   parse_mode=parse_mode)
    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_message.chat_id,
                                   text=logo+"Operation canceled.",
                                   reply_markup=back_button(),
                                   parse_mode=parse_mode)
    return MENU


def back_button():
    keyboard = [
        [
            InlineKeyboardButton("BACK", callback_data=str(BACK)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


if __name__ == "__main__":
    application = Application.builder().token(
        "5641491493:AAHXyldaaB-FynwrsaYiQAI7LN8PFyCyDIA").build()
    detect_ch = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(
                    detect_dip, pattern="^" + str(DIP_DETECT) + "$"),
                CallbackQueryHandler(
                    show_detect, pattern="^" + str(SHOW_DETECT) + "$"),
                CallbackQueryHandler(
                    cancel_detect, pattern="^" + str(CANCEL_DETECT) + "$"),
                CallbackQueryHandler(
                    about_ddb, pattern="^" + str(ABOUT) + "$"),
                CallbackQueryHandler(start, pattern="^" + str(BACK) + "$"),
            ],
            SET_CHAIN: [
                CallbackQueryHandler(set_chain, pattern="^" + str(BSC) + "$"),
                CallbackQueryHandler(set_chain, pattern="^" + str(ETH) + "$"), ],
            SET_TOKEN_ADDRESS: [MessageHandler(filters.TEXT & (~filters.COMMAND), set_token_address)],
            SET_DIP: [MessageHandler(filters.TEXT & (~filters.COMMAND), set_dip)],
            CONFIRM: [
                CallbackQueryHandler(confirm, pattern="^" + str(YES) + "$"),
                CallbackQueryHandler(confirm, pattern="^" + str(NO) + "$"), ],
            DELETE: [
                CallbackQueryHandler(delete, pattern="^" + str(YES) + "$"),
                CallbackQueryHandler(delete, pattern="^" + str(NO) + "$"), ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],

    )

    application.add_handler(detect_ch)
    application.run_polling()
