# RaspiControl-Bot
Recieve status data from your RaspberryPi via a Telegram Bot.

## How to use:

Create a new bot via the @BotFather on Telegram and copy the token.

Clone this repository onto your RaspberryPi.
In this folder, create a file named "token.txt" and paste your bot token into it.
You also have  to open your terminal and install:
`pip install gpiozero`  and `pip install python-telegram-bot==12.8`
(Using version 12.8 is important. In the future i might be updating the script to use version 20+.)

Now run the `raspicontrol.py` script.

## Run on autostart:

I used a virtual python environment to run the script.
To set this up use following commands:
`python3 -m venv /home/pi/pi-status-bot/venv`

To navigate into the virtual envirenment use:
`source /home/pi/pi-status-bot/venv/bin/activate`

Now install to needed packages into the venv:
`pip install gpiozero` and `pip install python-telegram-bot==12.8`

Let's create the system serive using following command:
`sudo nano /lib/systemd/system/raspicontrol.service`

In there paste the following:
```
[Unit]
Description=RaspiControl-Telegram-Bot
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/pi/pi-status-bot/venv/bin/python /home/pi/pi-status-bot/raspicontrol.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
This ensures that the service runs in the virtual environment and runs after the system fully started up.
Exit nano with `CTRL + X` and save with `Y` followed by `ENTER`.

Now you can enable the service:
`sudo systemctl enable raspicontrol.service`

And start it:
`sudo systemctl start raspicontrol.service`

You can check the status of the service by using:
`sudo systemctl status raspicontrol.service`

