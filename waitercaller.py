from flask import Flask
from flask import render_template
from flask import request
from flask_login import LoginManager
from flask_login import login_required
from flask_login import login_user
from flask_login import current_user
import config
if config.test:
    from mockdbhelper import MockDBHelper as DBHelper
else:
    from dbhelper import DBHelper
#from mockdbhelper import MockDBHelper as DBHelper
from user import User
from flask import redirect
from flask import url_for
from flask_login import logout_user

from passwordhelper import PasswordHelper
import datetime
from forms import RegistrationForm

app = Flask(__name__)
app.secret_key = 'ApXHpNyVLvjL2VpxsfnUdPZBauPda/c9UpV+fBhNlRwgzDPKnoenGzl1GQiGGMQEaER5Uiurxcfn5ciwdpkXaqhaSLMsxm/Js6nX'
login_manager = LoginManager(app)
DB = DBHelper()
PH = PasswordHelper()

@app.route("/")
def home():
    registrationform = RegistrationForm()
    return render_template("home.html", registrationform=registrationform)

@app.route("/login", methods=["POST"])
def login():
   email = request.form.get("email")
   password = request.form.get("password")
   stored_user = DB.get_user(email)
   #password = password.encode('utf-8')
   if stored_user and PH.validate_password(password, stored_user['salt'], stored_user['hashed']):
      user = User(email)
      login_user(user,remember=True)
      return redirect(url_for('account'))
   return home()

@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
       return User(user_id)

@app.route("/logout")
def logout():
   logout_user()
   return redirect(url_for("home"))

@app.route("/register", methods=["POST"])
def register():
    form = RegistrationForm(request.form)
    if form.validate():
        if DB.get_user(form.email.data):
            form.email.errors.append("Email address already registered")
            return render_template('home.html', registrationform=form)
        salt = PH.get_salt()
        #print('type salt',type(salt))
        #print('type pw1',type(pw1))
        #pw1 = pw1.encode('utf-8')
        hashed = PH.get_hash(form.password2.data.encode() + salt)
        DB.add_user(form.email.data,salt, hashed)
        return render_template("home.html", registrationform=form, onloadmessage="Registration successful. Please log in.")
    return render_template("home.html", registrationform=form)

@app.route("/dashboard")
@login_required
def dashboard():
    now = datetime.datetime.now()
    requests = DB.get_requests(current_user.get_id())
    for req in requests:
        deltaseconds = (now - req['time']).seconds
        req['wait_minutes'] = "{}.{}".format((deltaseconds/60), str(deltaseconds % 60).zfill(2))
    return render_template("dashboard.html", requests=requests)

@app.route("/dashboard/resolve")
@login_required
def dashboard_resolve():
  request_id = request.args.get("request_id")
  DB.delete_request(request_id)
  return redirect(url_for('dashboard'))


@app.route("/account")
@login_required
def account():
    tables = DB.get_tables(current_user.get_id())
    return render_template("account.html",tables = tables)

@app.route("/account/createtable", methods=["POST"])
@login_required
def account_createtable():
  tablename = request.form.get("tablenumber")
  tableid = DB.add_table(tablename, current_user.get_id())
  new_url = config.base_url + "newrequest/" + str(tableid) # because in mongodb, we used objectID()
  DB.update_table(tableid, new_url)
  return redirect(url_for('account'))

@app.route("/account/deletetable")
@login_required
def account_deletetable():
    tableid = request.args.get("tableid")
    DB.delete_table(tableid)
    return redirect(url_for('account'))

@app.route("/newrequest/<tid>")
def new_request(tid):
    DB.add_request(tid, datetime.datetime.now())
    return "Your request has been logged and a waiter will be withyou shortly"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
