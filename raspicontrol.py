from telegram.ext import Updater, CommandHandler
from gpiozero import CPUTemperature

with open('token.txt', 'r') as f:
    TOKEN = f.read()

cpu = CPUTemperature()

def start(update):
    update.message.replay_text("Hey! Welcome to RaspiControl. I'm a bot that can send you status data about your Raspberry Pi.")

def help(update):
    update.message.replay_text("""
    The following commands are avaiable:

    /start -> Welcome Message
    /help -> This Message
    /temp -> Current CPU temperature
    /contact -> Information about the developer
    """)

def temp(update):
    update.message.replay_text("The current CPU temperature is: " + cpu.temperature)

def contact(update):
    update.message.replay_text("More about Tim: https://t1ms22.github.io")

updater = Updater(TOKEN, use_context=False)
disp = updater.dispatcher

disp.add_handler(CommandHandler("start", start))
disp.add_handler(CommandHandler("help ", help))
disp.add_handler(CommandHandler("temp", temp))
disp.add_handler(CommandHandler("contact", contact))

updater.start_polling()
updater.idle()