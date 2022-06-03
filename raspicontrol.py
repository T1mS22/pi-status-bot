import telegram.ext
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

updater = telegram.ext.updater(TOKEN)
disp = updater.dispatcher

disp.add_handler(telegram.ext.CommandHandler("start", start))
disp.add_handler(telegram.ext.CommandHandler("help ", help))
disp.add_handler(telegram.ext.CommandHandler("temp", temp))
disp.add_handler(telegram.ext.CommandHandler("contact", contact))

updater.start_polling()
updater.idle()