from flask import Flask, request, render_template, json, url_for, session

import settings, mildom

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SESSION_SECRET

registered_notification = []


@app.route('/')
def index():
    streamer_list = {"KUN": ["mildom", mildom.is_live(10105254), "https://isscdn.mildom.tv/download/file/"
                                                                 "jp/mildom/nnphotos/9db7bd31a308e84f6999"
                                                                 "9eb39994311f.png", 10105254],
                     "Mondo": ["mildom", mildom.is_live(10429922), "https://isscdn.mildom.tv/download/file"
                                                                   "/jp/mildom/nnphotos/be49b330ff73aad114"
                                                                   "0e53ff17622db7.png", 10429922],
                     "はつめ": ["mildom", mildom.is_live(10846882), "https://isscdn.mildom.tv/download/file/"
                                                                 "jp/mildom/nnphotos/86a90401e9f3baa539bc7c"
                                                                 "7ce26a6c07.png", 10846882],
                     "Sovault": ["mildom", mildom.is_live(10116311), "https://lh3.googleusercontent.com/a-/"
                                                                     "AAuE7mD3CJYjcE5X03bWZS0Gre09PbZURLS2n"
                                                                     "X1OAQqctA", 10116311]
                     }
    col_lg_number = int(12 / len(streamer_list))
    if col_lg_number < 3:
        col_lg_number = 3
    return render_template("home.html", streamer_list=streamer_list, col_lg_number=col_lg_number)


@app.route('/login')
def login():
    return "This function is not ready yet...."


@app.route('/logout')
def logout():
    return "This function is not ready yet...."


@app.route('/settings')
def settings():
    return render_template("settings.html")


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


if __name__ == '__main__':
    app.run()
