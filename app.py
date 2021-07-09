import json

import dataset
import mildom
import requests
import time
from flask import Flask, request, render_template, redirect, session, url_for

import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SESSION_SECRET
db: dataset.Database = dataset.connect(url=settings.DB_URL)
mildom_accounts_table: dataset.Table = db['mildom_accounts']

DISCORD_API_BASE_URL = 'https://discordapp.com/api/'
CLIENT_ID = 750141462502572043
CLIENT_SECRET = "-Ad6iC9jXG2TWJ8hDbCec-dM2HNC5DsY"
registered_notification = []
mildom_streamer_list = [mildom.User(10105254), mildom.User(10429922), mildom.User(10846882), mildom.User(10116311)]
last_updated = time.time()


@app.route('/')
def index():
    if time.time() - last_updated > 60:
        update = True
    else:
        update = False
    streamer_list = {}
    for i in mildom_streamer_list:
        if update is True:
            i.update()
        streamer_list[i.name] = ["mildom", i.is_live, i.avatar_url, i.id]
    col_lg_number = int(12 / len(streamer_list))
    if col_lg_number < 3:
        col_lg_number = 3
    return render_template("home.html", streamer_list=streamer_list, col_lg_number=col_lg_number)


@app.route('/login')
def login():
    code = request.args.get('code')
    if code is None:
        session['return_url'] = request.args.get('return_url')
        return redirect('https://discord.com/api/oauth2/authorize?client_id=750141462502572043&redirect_uri=https%3A'
                        '%2F%2Fstream-portal.herokuapp.com%2Flogin&response_type=code&scope=identify')
    return_url = session.get('return_url')
    if return_url is None:
        return_url = url_for('index')
    res_token = exchange_code(code=code, redirect_url=url_for("login", _external=True))
    token = res_token['access_token']
    refresh_token = res_token['refresh_token']
    res_info = requests.get(DISCORD_API_BASE_URL + 'users/@me', headers={'Authorization': f'Bearer {token}'})
    res_dict = json.loads(res_info.content.decode())
    session['logged_in'] = True
    session['discord_user_id'] = int(res_dict['id'])
    session['discord_user_name'] = res_dict['username']
    session['discord_refresh_token'] = refresh_token
    session.pop('return_url', None)
    return redirect(return_url)


@app.route('/register-mildom-account', methods=['POST'])
def register_mildom_account():
    discord_id = session["discord_user_id"]
    mildom_id = request.args["mildom_id"]
    mildom_accounts_table.upsert(dict(discord_id=discord_id, mildom_id=mildom_id),
                                 ["discord_id"])
    return redirect(url_for("index"))


@app.route('/logout')
def logout():
    return_url = request.args.get('return_url')
    if return_url is None:
        return_url = url_for('index')
    session_keys = list(session.keys())
    for key in session_keys:
        del session[key]
    session['logged_in'] = False
    return redirect(return_url)


@app.route('/add-channels')
def add_channels():
    if "discord_user_id" not in session:
        return redirect(url_for("login", redirect_url=request.url))
    mildom_accounts_row = mildom_accounts_table.find_one(discord_id=session["discord_user_id"])
    if mildom_accounts_row is None:
        return redirect(url_for("settings"))
    following_list = fetch_following_list(mildom_id=mildom_accounts_row["mildom_id"])
    return render_template("add_channels.html", following_list=following_list)


@app.route('/settings')
def settings():
    if "discord_user_id" not in session:
        return redirect(url_for("login", redirect_url=request.url))
    mildom_accounts_row = mildom_accounts_table.find_one(discord_id=session["discord_user_id"])
    mildom_id = ""
    if mildom_accounts_row is not None:
        mildom_id = mildom_accounts_row["mildom_id"]
    return render_template("settings.html", mildom_id=mildom_id)


@app.route('/api/notification-register', methods=["POST"])
def notification_register():
    global registered_notification
    request_dict: dict = request.get_json()
    if "remove" in request.args:
        print(request_dict)
        registered_notification.remove(request_dict)
    else:
        print(request_dict)
        registered_notification.append(request_dict)
    return "success"


def exchange_code(code, redirect_url):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url,
        'scope': 'identify guilds'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('https://discordapp.com/api/oauth2/token', data=data, headers=headers)
    print(data)
    r.raise_for_status()
    return r.json()


def fetch_following_list(mildom_id: int):
    url = f"https://cloudac-cf-jp.mildom.com/nonolive/gappserv/user/followList?__platform=web&__user_id={mildom_id}"
    r = requests.get(url)
    r_list: list = r.json()["body"]
    return r_list


if __name__ == '__main__':
    app.run()
