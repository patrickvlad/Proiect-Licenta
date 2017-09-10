from flask import Flask, flash, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length
from utils_mongo import create_user, validate_user, get_user, search_mongodb, save_user_history, get_user_history
from utils_postgre import search_postgresql
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AppVerySecretKey!'
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Pentru a folosi aplicatia autentificati-va!'
login_manager.login_message_category = 'warning'

class User():
  def __init__(self, user):
    self.username = user['username']
  def is_authenticated(self):
    return True
  def is_active(self):
    return True
  def is_anonymous(self):
    return False
  def get_id(self):
    return self.username

@login_manager.user_loader
def load_user(username):
  user = get_user(username)
  if user:
    return User(user)
  return None

class LoginForm(FlaskForm):
  username = StringField('Utilizator', validators=[InputRequired(), Length(min=4, max=15)])
  password = PasswordField('Parola', validators=[InputRequired(), Length(min=8, max=80)])

class RegisterForm(FlaskForm):
  username = StringField('Utilizator', validators=[InputRequired(), Length(min=4, max=15)])
  password = PasswordField('Parola', validators=[InputRequired(), Length(min=8, max=80)])

# LOCK SECTION (no more changes)
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
# UNLOCK SECTION
  print 'PROCESSING REQUEST'
  print "--------------------------------------------------"

  form = {
    'select-words': "",
    'select-location-x': "",
    'select-location-y': "",
    'select-author-gender': "",
    'select-author-age-min': "",
    'select-author-age-max': "",
    'select-date-start': "",
    'select-date-stop': "",
    'checkboxes': {
      'group-words': False,
      'group-location-x': False,
      'group-location-y': False,
      'group-author-gender': False,
      'group-author-age-min': False,
      'group-author-age-max': False,
      'group-date-start': False,
      'group-date-stop': False
    }
  }

  if request.method == 'POST':
    selectBy = {}
    if request.form.get('select-words') != '':
      form['select-words'] = request.form.get('select-words')
      selectBy['words'] = request.form.get('select-words')
    if request.form.get('select-location-x') != '':
      form['select-location-x'] = request.form.get('select-location-x')
      selectBy['location.x'] = request.form.get('select-location-x')
    if request.form.get('select-location-y') != '':
      form['select-location-y'] = request.form.get('select-location-y')
      selectBy['location.y'] = request.form.get('select-location-y')
    if request.form.get('select-author-gender') != '':
      form['select-author-gender'] = request.form.get('select-author-gender')
      selectBy['author.gender'] = request.form.get('select-author-gender')
    if request.form.get('select-author-age-min') != '':
      form['select-author-age-min'] = request.form.get('select-author-age-min')
      selectBy['author.age.min'] = request.form.get('select-author-age-min')
    if request.form.get('select-author-age-max') != '':
      form['select-author-age-max'] = request.form.get('select-author-age-max')
      selectBy['author.age.max'] = request.form.get('select-author-age-max')
    if request.form.get('select-date-start') != '':
      form['select-date-start'] = request.form.get('select-date-start')
      selectBy['date.start'] = request.form.get('select-date-start')
    if request.form.get('select-date-stop') != '':
      form['select-date-stop'] = request.form.get('select-date-stop')
      selectBy['date.stop'] = request.form.get('select-date-stop')
    mongoGroupBy = {}
    postgreGroupBy = ''
    if request.form.get('group-words') == 'on':
      form['checkboxes']['group-words'] = request.form.get('group-words') == 'on'
      mongoGroupBy['words.word'] = '$words.word'
      postgreGroupBy += ', ' + 'word'
    if request.form.get('group-location-x') == 'on':
      form['checkboxes']['group-location-x'] = request.form.get('group-location-x') == 'on'
      mongoGroupBy['location.x'] = '$location.x'
      postgreGroupBy += ', ' + 'x'
    if request.form.get('group-location-y') == 'on':
      form['checkboxes']['group-location-y'] = request.form.get('group-location-y') == 'on'
      mongoGroupBy['location.y'] = '$location.y'
      postgreGroupBy += ', ' + 'y'
    if request.form.get('group-author-gender') == 'on':
      form['checkboxes']['group-author-gender'] = request.form.get('group-author-gender') == 'on'
      mongoGroupBy['author.gender'] = '$author.gender'
      postgreGroupBy += ', ' + 'gender'
    if request.form.get('group-author-age-min') == 'on' or request.form.get('group-author-age-max') == 'on':
      form['checkboxes']['group-author-age-min'] = request.form.get('group-author-age-min') == 'on'
      form['checkboxes']['group-author-age-max'] = request.form.get('group-author-age-max') == 'on'
      mongoGroupBy['author.age'] = '$author.age'
      postgreGroupBy += ', ' + 'age'
    if request.form.get('group-date-start') == 'on' or request.form.get('group-date-stop') == 'on':
      form['checkboxes']['group-date-start'] = request.form.get('group-date-start') == 'on'
      form['checkboxes']['group-date-stop'] = request.form.get('group-date-stop') == 'on'
      mongoGroupBy['date'] = '$date'
      postgreGroupBy += ', ' + 'date'

    if request.form['submit'] == 'import':
      flash('Datele au fost importate cu succes!', 'success')
      return render_template("index.html", user=current_user.get_id(), form=form, times={}, data={})
    else:
      print 'Select By ', selectBy
      print 'Mongo Group By ', mongoGroupBy
      print 'Postgre Group By ', postgreGroupBy[1:]
      print "--------------------------------------------------"

      mongoConnectTime, mongoFilterTime, docs = search_mongodb(selectBy, mongoGroupBy)
      postgreConnectTime, postgreFilterTime = search_postgresql(selectBy, postgreGroupBy[1:])
      times = {
        'connectTimes': [mongoConnectTime, postgreConnectTime],
        'filterTimes': [mongoFilterTime, postgreFilterTime]
      }
      save_user_history(current_user.get_id(), times, docs)
      flash('Datele au fost filtrate cu succes!', 'info')
      return render_template("index.html", user=current_user.get_id(), form=form, times=times, data=docs)

  return render_template("index.html", user=current_user.get_id(), form=form, times={}, data={})

# LOCK SECTION (no more changes)
@app.route('/history', methods=['GET', 'POST'])
# original: @app.route('/history')
@login_required
def history():
# UNLOCK SECTION
  data = get_user_history(current_user.get_id())
  return render_template("history.html", user=current_user.get_id(), data=data)

# LOCK FUNCTION (no more changes)
@app.route('/login', methods=['GET', 'POST'])
def login():
  form = LoginForm()

  if request.method == 'POST':
    if request.form['submit'] == 'register':
      return redirect(url_for('register'))
    if form.validate_on_submit():
      user = validate_user({
        'username': form.username.data,
        'password': form.password.data
      })
      if user:
        login_user(User(user))
        return redirect(url_for('index'))
      flash('Utilizator sau parola invalide!', 'danger')

  return render_template('login.html', form=form)

# LOCK FUNCTION (no more changes)
@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegisterForm()

  if request.method == 'POST':
    if request.form['submit'] == 'login':
      return redirect(url_for('login'))
    if form.validate_on_submit():
      userCreated = create_user({
        'username': form.username.data,
        'password': generate_password_hash(form.password.data, method='sha256')
      })
      if userCreated:
        flash('Utilizatorul a fost creat cu succes!', 'success')
        return redirect(url_for('login'))
      else:
        flash('Utilizatorul exista deja!', 'warning')

  return render_template('register.html', form=form)

# LOCK FUNCTION (no more changes)
@app.route('/logout')
def logout():
  logout_user()
  flash('V-ati delogat cu success!', 'success')
  return redirect(url_for('login'))

if __name__ == "__main__":
  app.run()
