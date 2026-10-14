# RaspiControl-Bot
Recieve status data from your RaspberryPi via a Telegram Bot and control your Pi-hole.

## How to use:

Create a new bot via the @BotFather on Telegram and copy the token.

Clone this repository onto your RaspberryPi.
In this folder, create a file named "token.txt" and paste your bot token into it.

I used a virtual python environment to run the script.
To set this up use following commands:
`python3 -m venv /home/pi/pi-status-bot/venv`

Now install the needed packages into the venv:
`/home/pi/pi-status-bot/venv/bin/pip install -r requirements.txt`
(The script uses python-telegram-bot 13.x, newer versions (20+) are not compatible.)

Now run the `raspicontrol.py` script.

## Pi-hole commands:

The Pi-hole commands (`/pihole_status`, `/disable30s`, `/disable5m`, `/enable`, `/pihole_update`, `/ipv6`) are only
available for allowed chats. Send `/myid` to the bot and put the chat ID into a file named "allowed_chat_ids.txt"
(one ID per line), then restart the bot. Allowed chats also get a message when the disk is over 90% full or the
IPv6 address of the Pi changes.

The bot user needs passwordless sudo for `pihole`.

## Run on autostart:

The service file is part of this repository. It runs the script in the virtual environment as user `pi`
and restarts it if it crashes.

Copy it and enable the service:
`sudo cp raspicontrol.service /etc/systemd/system/`
`sudo systemctl enable --now raspicontrol.service`

You can check the status of the service by using:
`sudo systemctl status raspicontrol.service`

And the logs with:
`journalctl -u raspicontrol -f`
