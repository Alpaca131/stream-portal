import json
import random
import string

import dataset
import mildom
import requests
import time

from aiohttp.web_routedef import route
from flask import Flask, request, render_template, redirect, session, url_for

import settings

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SESSION_SECRET
FIVE_DON_BOT_SECRET = settings.FIVE_DON_BOT_SECRET
FIVE_DON_BOT_TOKEN = settings.FIVE_DON_BOT_TOKEN
db: dataset.Database = dataset.connect(url=settings.DB_URL)
mildom_accounts_table: dataset.Table = db['mildom_accounts']
subscribing_streamers_table: dataset.Table = db['subscribing_streamers']

DISCORD_API_BASE_URL = 'https://discordapp.com/api/'
CLIENT_ID = 750141462502572043
CLIENT_SECRET = settings.DISCORD_CLIENT_SECRET
registered_notification = []
mildom_default_streamer_list = [10105254, 10429922, 10846882, 10116311]
mildom_api_cached_response = {}


@app.route('/')
def index():
    if "discord_user_id" not in session:
        streamer_id_list = mildom_default_streamer_list
    else:
        streamer_row = subscribing_streamers_table.find_one(discord_user_id=session["discord_user_id"])
        if streamer_row is None or streamer_row["mildom"] is None:
            streamer_id_list = mildom_default_streamer_list
        else:
            streamer_id_list = streamer_row["mildom"]
    online_streamer_list = {}
    offline_streamer_list = {}
    for user_id in streamer_id_list:
        live_stream = mildom_get_live(int(user_id))
        if live_stream.is_live:
            if live_stream.is_dvr_enabled:
                m3u8_url = live_stream.dvr_videos[-1]["url"]
            else:
                m3u8_url = None
            online_streamer_list[live_stream.author_name] = \
                ["mildom", live_stream.author_avatar_url, live_stream.title,
                 live_stream.thumbnail_url, live_stream.viewers, live_stream.author_id, m3u8_url]
        else:
            offline_streamer_list[live_stream.author_name] = \
                ["mildom", live_stream.author_avatar_url, live_stream.title,
                 live_stream.thumbnail_url, live_stream.viewers, live_stream.author_id]
    offline_col_lg_number = 0
    online_col_lg_number = 0
    if len(online_streamer_list) <= 3:
        online_col_lg_number = 4
    if len(online_streamer_list) >= 4:
        online_col_lg_number = 3
    if len(offline_streamer_list) <= 3:
        offline_col_lg_number = 4
    if len(offline_streamer_list) >= 4:
        offline_col_lg_number = 3
    return render_template("home.html",
                           online_streamer_list=online_streamer_list, online_col_lg_number=online_col_lg_number,
                           offline_streamer_list=offline_streamer_list, offline_col_lg_number=offline_col_lg_number)


@app.route('/login')
def login():
    code = request.args.get('code')
    if code is None:
        session['return_url'] = request.args.get('return_url')
        state = random_strings(n=19)
        session['state'] = state
        return redirect('https://discord.com/api/oauth2/authorize?client_id=750141462502572043&redirect_uri=https%3A'
                        f'%2F%2Fstream-portal.herokuapp.com%2Flogin&response_type=code&scope=identify&state={state}')
    return_url = session.get('return_url')
    if return_url is None:
        return_url = url_for('index')
    if request.args.get("state") != session["state"]:
        return "Authorization Error.", 401
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
    session.pop('state', None)
    return redirect(return_url)


@app.route('/register-mildom-account', methods=['POST'])
def register_mildom_account():
    form_dict = request.form
    discord_id = session["discord_user_id"]
    mildom_id = form_dict["mildom_id"]
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


@app.route('/add-channels', methods=['POST', 'GET'])
def add_channels():
    if "discord_user_id" not in session:
        return redirect(url_for("login", redirect_url=request.url))
    mildom_accounts_row = mildom_accounts_table.find_one(discord_id=session["discord_user_id"])
    if mildom_accounts_row is None:
        return redirect(url_for("settings"))
    following_list = fetch_following_list(mildom_id=mildom_accounts_row["mildom_id"])
    if request.method == "POST":
        form_data = request.form
        if int(form_data["discord_user_id"]) == session["discord_user_id"]:
            if form_data["mode"] == "add":
                add_mildom_channel(discord_user_id=session["discord_user_id"],
                                   mildom_id=form_data["mildom_id"])
            elif form_data["mode"] == "remove":
                remove_mildom_channel(discord_user_id=session["discord_user_id"],
                                      mildom_id=form_data["mildom_id"])
    subscribing_list = subscribing_streamers_table.find_one(discord_user_id=session["discord_user_id"])
    if subscribing_list is None:
        subscribing_list = []
    else:
        subscribing_list = subscribing_list["mildom"]
    return render_template("add_channels.html", following_list=following_list, subscribing_list=subscribing_list)


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


@app.route('/neo-miyako-auth/2fa')
def neo_miyako_auth_redirect():
    return redirect(url_for("neo_miyako_auth"))


@app.route('/neo-miyako/2fa-auth')
def neo_miyako_auth():
    code = request.args.get("code")
    if code is None:
        state = random_strings(n=19)
        session['state'] = state
        return redirect('https://discord.com/api/oauth2/authorize?client_id=718034684533145605&redirect_uri=https%3A'
                        '%2F%2Fstream-portal.herokuapp.com%2Fneo-miyako%2F2fa-auth&response_type=code&scope=identify '
                        f'&state={state}')
    if session["state"] != request.args.get("state"):
        return "Authorization failed.", 401
    res_token = exchange_code(code=code, redirect_url=url_for("neo_miyako_auth", _external=True),
                              client_id=718034684533145605, client_secret=FIVE_DON_BOT_SECRET, scope="identify")
    token = res_token['access_token']
    res_info = requests.get(DISCORD_API_BASE_URL + 'users/@me', headers={'Authorization': f'Bearer {token}'})
    res_dict = res_info.json()
    if res_dict["mfa_enabled"] is False:
        return "二段階認証を有効にしてから再度お試しください。"
    user_id = int(res_dict['id'])
    r = requests.get(DISCORD_API_BASE_URL + f"/guilds/484102468524048395/members/{user_id}",
                     headers={"authorization": f"Bot {FIVE_DON_BOT_TOKEN}"})
    r_dict = r.json()
    roles: list = r_dict["roles"]
    roles.append(873017896983482379)
    requests.patch(DISCORD_API_BASE_URL + f"/guilds/484102468524048395/members/{user_id}",
                   json={"roles": roles}, headers={"authorization": f"Bot {FIVE_DON_BOT_TOKEN}"})
    return "正常に付与されました。"


def exchange_code(code, redirect_url, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope="identify guilds"):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url,
        'scope': scope
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('https://discordapp.com/api/oauth2/token', data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def fetch_following_list(mildom_id: int):
    url = f"https://cloudac-cf-jp.mildom.com/nonolive/gappserv/user/followList?__platform=web&__user_id={mildom_id}"
    r = requests.get(url)
    r_list: list = r.json()["body"]
    return r_list


def mildom_get_live(user_id: int):
    if user_id not in mildom_api_cached_response:
        live_stream = mildom.LiveStream(user_id)
        mildom_api_cached_response[user_id] = [live_stream, time.time()]
    else:
        live_stream: mildom.LiveStream = mildom_api_cached_response[user_id][0]
        last_updated = mildom_api_cached_response[user_id][1]
        if time.time() - last_updated > 60:
            live_stream.update()
            mildom_api_cached_response[user_id] = [live_stream, time.time()]
    return live_stream


def add_mildom_channel(discord_user_id, mildom_id):
    db_data = subscribing_streamers_table.find_one(discord_user_id=discord_user_id)
    if db_data is None:
        db_data = []
    else:
        db_data = db_data["mildom"]
    db_data.append(str(mildom_id))
    subscribing_streamers_table.upsert(dict(discord_user_id=discord_user_id, mildom=db_data),
                                       ["discord_user_id"])
    return


def remove_mildom_channel(discord_user_id, mildom_id):
    db_data = subscribing_streamers_table.find_one(discord_user_id=discord_user_id)
    db_data = db_data["mildom"]
    db_data.remove(str(mildom_id))
    subscribing_streamers_table.update(dict(discord_user_id=discord_user_id, mildom=db_data),
                                       ["discord_user_id"])
    return


def random_strings(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


if __name__ == '__main__':
    app.run(threaded=True)
