#!/home/pi/pi-status-bot/venv/bin/python
import os
import re
import time
import logging
import subprocess
from functools import wraps
from telegram import BotCommand
from telegram.ext import Updater, CommandHandler
from gpiozero import CPUTemperature, DiskUsage

logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', level=logging.INFO)
log = logging.getLogger('raspicontrol')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def read_lines(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]


TOKEN = read_lines('token.txt')[0]
# Chat IDs allowed to use the Pi-hole commands, one per line. Send /myid to the bot to get yours.
ADMIN_CHAT_IDS = {int(x) for x in read_lines('allowed_chat_ids.txt')}
IPV6_STATE_FILE = os.path.join(BASE_DIR, 'last_ipv6.txt')
DISK_ALERT_PERCENT = 90

cpu = CPUTemperature()
disk = DiskUsage()
disk_alert_sent = False


def run(cmd, timeout=60):
    result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    output = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', result.stdout + result.stderr).replace('\r', '\n')
    return result.returncode, output


def dns_works(attempts=1):
    for attempt in range(attempts):
        if attempt:
            time.sleep(5)
        _, output = run(['dig', '+short', '+time=3', '+tries=1', '@127.0.0.1', 'example.com'], timeout=10)
        answers = output.split()
        if answers and answers[-1] not in ('0.0.0.0', '::'):
            return True
    return False


def current_ipv6():
    # The Pi's global IPv6 address, which has to be entered as DNSv6 server in the router.
    _, output = run(['ip', '-6', '-o', 'addr', 'show', 'dev', 'eth0', 'scope', 'global'])
    for line in output.splitlines():
        address = line.split()[3].split('/')[0]
        if 'deprecated' not in line and not address.startswith('fd'):
            return address
    return None


def admin_only(func):
    @wraps(func)
    def wrapper(update, context):
        chat_id = update.effective_chat.id
        if chat_id not in ADMIN_CHAT_IDS:
            log.warning('Denied /%s for chat %s', func.__name__, chat_id)
            update.message.reply_text(f'Sorry, you are not allowed to use this command. (Your chat ID is {chat_id}.)')
            return
        return func(update, context)
    return wrapper


def notify_admins(context, text):
    for chat_id in ADMIN_CHAT_IDS:
        context.bot.send_message(chat_id=chat_id, text=text)


def start(update, context):
    update.message.reply_text("Hey! Welcome to RaspiControl. I'm a bot that can send you status data about your Raspberry Pi. Best way to start is typing /help")

def help(update, context):
    update.message.reply_text("""
    The following commands are avaiable:

    /start -> Welcome Message
    /help -> This Message
    /temp -> Current CPU temperature
    /storage -> Current disk usage
    /contact -> Information about the developer
    /myid -> Your Telegram chat ID

    Pi-hole (admins only):
    /pihole_status -> Is blocking enabled?
    /disable30s -> Disable blocking for 30 seconds
    /disable5m -> Disable blocking for 5 minutes
    /enable -> Enable blocking again
    /pihole_update -> Update Pi-hole
    /ipv6 -> Current IPv6 address (DNSv6 server for the router)
    """)

def temp(update, context):
    update.message.reply_text(f'The current CPU temperature is: {cpu.temperature:.2f}°C')

def storage(update, context):
    update.message.reply_text(f'The current disk usage is: {disk.usage:.2f}%')

def contact(update, context):
    update.message.reply_text("More about Tim: https://t1ms22.github.io")

def myid(update, context):
    update.message.reply_text(f'Your chat ID is: {update.effective_chat.id}')


@admin_only
def pihole_status(update, context):
    _, output = run(['sudo', '-n', 'pihole', 'status'])
    state = 'enabled ✅' if 'blocking is enabled' in output else 'disabled ⚠️'
    update.message.reply_text(f'Pi-hole blocking is {state}')

def disable_for(duration):
    @admin_only
    def disable(update, context):
        code, output = run(['sudo', '-n', 'pihole', 'disable', duration])
        if code == 0:
            update.message.reply_text(f'Pi-hole blocking disabled for {duration}.')
        else:
            update.message.reply_text(f'Disabling failed:\n{output[-500:]}')
    disable.__name__ = f'disable{duration}'
    return disable

@admin_only
def enable(update, context):
    code, output = run(['sudo', '-n', 'pihole', 'enable'])
    update.message.reply_text('Pi-hole blocking enabled.' if code == 0 else f'Enabling failed:\n{output[-500:]}')

@admin_only
def pihole_update(update, context):
    update.message.reply_text('Updating Pi-hole, this can take a few minutes...')
    try:
        code, output = run(['sudo', '-n', 'pihole', '-up'], timeout=900)
    except subprocess.TimeoutExpired:
        code, output = -1, 'Timed out after 15 minutes.'
    _, versions = run(['sudo', '-n', 'pihole', '-v'])
    # pihole -up restarts FTL, so give DNS up to a minute to come back before reporting.
    dns_ok = dns_works(attempts=12)
    lines = [l for l in output.splitlines() if l.strip()]
    summary = '\n'.join(lines[-8:])
    status = 'Update finished.' if code == 0 else f'Update FAILED (exit code {code}).'
    dns = 'DNS is working ✅' if dns_ok else '⚠️ DNS IS NOT WORKING - check the Pi-hole now!'
    update.message.reply_text(f'{status}\n{dns}\n\n{versions.strip()}\n\nLast output:\n{summary}')

@admin_only
def ipv6(update, context):
    update.message.reply_text(f'Current IPv6 address: {current_ipv6() or "none"}')


def check_system(context):
    global disk_alert_sent
    address = current_ipv6()
    if address:
        last = read_lines(IPV6_STATE_FILE)
        if last and last[0] != address:
            notify_admins(context, f'⚠️ The IPv6 address of the Pi changed (new prefix from the provider).\n'
                                   f'Enter the new one as DNSv6 server in the router:\n{address}\n(old: {last[0]})')
        if not last or last[0] != address:
            with open(IPV6_STATE_FILE, 'w') as f:
                f.write(address + '\n')

    usage = disk.usage
    if usage >= DISK_ALERT_PERCENT and not disk_alert_sent:
        notify_admins(context, f'⚠️ The disk of the Pi is {usage:.0f}% full.')
        disk_alert_sent = True
    elif usage < DISK_ALERT_PERCENT - 5:
        disk_alert_sent = False


updater = Updater(TOKEN, use_context=True)
disp = updater.dispatcher

disp.add_handler(CommandHandler("start", start))
disp.add_handler(CommandHandler("help", help))
disp.add_handler(CommandHandler("temp", temp))
disp.add_handler(CommandHandler("storage", storage))
disp.add_handler(CommandHandler("contact", contact))
disp.add_handler(CommandHandler("myid", myid))
disp.add_handler(CommandHandler("pihole_status", pihole_status))
disp.add_handler(CommandHandler("disable30s", disable_for('30s')))
disp.add_handler(CommandHandler("disable5m", disable_for('5m')))
disp.add_handler(CommandHandler("enable", enable))
disp.add_handler(CommandHandler("pihole_update", pihole_update, run_async=True))
disp.add_handler(CommandHandler("ipv6", ipv6))

updater.job_queue.run_repeating(check_system, interval=600, first=30)

try:
    updater.bot.set_my_commands([
        BotCommand('help', 'Show all commands'),
        BotCommand('temp', 'Current CPU temperature'),
        BotCommand('storage', 'Current disk usage'),
        BotCommand('pihole_status', 'Is Pi-hole blocking enabled?'),
        BotCommand('disable30s', 'Disable blocking for 30 seconds'),
        BotCommand('disable5m', 'Disable blocking for 5 minutes'),
        BotCommand('enable', 'Enable blocking again'),
        BotCommand('pihole_update', 'Update Pi-hole'),
        BotCommand('ipv6', 'Current IPv6 address'),
        BotCommand('myid', 'Your chat ID'),
    ])
except Exception:
    log.exception('Could not register the command menu')

log.info('Bot started, %d admin chat(s) configured', len(ADMIN_CHAT_IDS))
updater.start_polling()
updater.idle()
