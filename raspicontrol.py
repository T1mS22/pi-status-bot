from telegram.ext import Updater, CommandHandler, MessageHandler
from gpiozero import CPUTemperature, DiskUsage


with open('token.txt', 'r') as f:
    TOKEN = f.readline().replace('\n', '')

cpu = CPUTemperature()
disk = DiskUsage()

def start(update, context):
    update.message.reply_text("Hey! Welcome to RaspiControl. I'm a bot that can send you status data about your Raspberry Pi.")

def help(update, context):
    update.message.reply_text("""
    The following commands are avaiable:

    /start -> Welcome Message
    /help -> This Message
    /temp -> Current CPU temperature
    /storage -> Current disk usage
    /contact -> Information about the developer
    """)

def temp(update, context):
    update.message.reply_text(f'The current CPU temperature is: {cpu.temperature:.2f}°C')

def storage(update, context):
    update.message.reply_text(f'The current disk usage is: {disk.usage:.2f}%')
    
def contact(update, context):
    update.message.reply_text("More about Tim: https://t1ms22.github.io")

updater = Updater(TOKEN, use_context=True)
disp = updater.dispatcher

disp.add_handler(CommandHandler("start", start))
disp.add_handler(CommandHandler("help", help))
disp.add_handler(CommandHandler("temp", temp))
disp.add_handler(CommandHandler("storage", storage))
disp.add_handler(CommandHandler("contact", contact))

updater.start_polling()
updater.idle()