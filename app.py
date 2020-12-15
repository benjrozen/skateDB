import hashlib
import os
import re

from flask_login import login_required, LoginManager, UserMixin, login_user, logout_user

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
from os import abort
from flask import Flask, render_template, request, redirect, flash, url_for, session, Response
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, HiddenField, StringField, PasswordField
import yaml
import git
import pypim

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'MLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)

conf = yaml.load(open('dbconf.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = conf['mysql_host']
app.config['MYSQL_USER'] = conf['mysql_user']
app.config['MYSQL_PASSWORD'] = conf['mysql_password']
app.config['MYSQL_DB'] = conf['mysql_db']
app.config['MYSQL_CURSORCLASS'] = conf['mysql_cursor_class']
mysql = MySQL(app)


@app.route('/git_up', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo(conf['remote_repo'])
        origin = repo.remotes.origin
        origin.pull()
        return 'Deploy Success', 200
    else:
        return 'Deploy no success', 400


class AddField(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    field_name = StringField('Field Name')
    submit = SubmitField('Add/Update Record')


# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# silly user model
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


class AddUser(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Register')


class uLogin(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Login')





@app.route("/logout")
@login_required
def logout():
    logout_user()
    session['logged_in'] = False
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    form3 = uLogin()
    if form3.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        cur = mysql.connection.cursor()
        user = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        password = hashlib.md5(password.encode())
        enpass = password.hexdigest()

        if (enpass == user['password']):
            message = f"{username} has successfully logged in!."
            id = user['id']
            user = User(id)
            login_user(User(id))
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('brands', message=message))
        else:
            return redirect(url_for('login'))
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form3.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form3, field).label.text,
                    error
                ), 'error')
        return render_template('login.html', form3=form3)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form2 = AddUser()
    if form2.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        cur = mysql.connection.cursor()
        mySql_insert_query = ("INSERT INTO users (username, password)"
                              "VALUES (%s, MD5(%s))")
        recordTuple = (username, password)
        cur.execute(mySql_insert_query, recordTuple)
        mysql.connection.commit()
        # create a message to send to the template
        message = f"The user {username} has been added."
        return render_template('login.html', message=message, )
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form2.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form2, field).label.text,
                    error
                ), 'error')
        return render_template('signup.html', form2=form2)


@app.route("/")
def home():
    return pypim.home()


@app.route("/result", methods=['POST'])
def searchresult():
    return pypim.searchresult()


# add a new strain to the database
@app.route('/add_strain', methods=['GET', 'POST'])
def add_record():
    return pypim.add_record()


# select a record to edit or delete
@app.route('/select_record')
def select_record():
    return pypim.select_record()


# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
def edit_or_delete():
    return pypim.edit_or_delete()


@app.route('/delete_result', methods=['POST'])
def delete_result():
    return pypim.delete_result()


# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
def edit_result():
    return pypim.edit_result()


@app.route("/brands")
@login_required
def brands():
    return pypim.brands()


@app.route("/brand/<id>")
def brand(id):
    return pypim.brand(id)





# Add a new field to product page
@app.route("/fields-manager", methods=["GET", "POST"])
def field_manager():
    formField = AddField()
    if formField.validate_on_submit():
        field_name = request.form['field_name']
        cur = mysql.connection.cursor()
        mySql_add_field_query = "ALTER TABLE brands ADD %s VARCHAR(255)" % (field_name)
        cur.execute(mySql_add_field_query)
        mysql.connection.commit()
        cur.execute("SELECT * FROM brands")
        fields = cur.fetchall()
        field_titles = [i[0] for i in cur.description]

        sec_prod_page = """      <tr>
            <td class="table_header">""" + (field_titles[-1]) + """</td><td>{{ brand.""" + (field_name) + """}}</td>
         </tr>"""
        sec_app_py_1 = "    " + (field_titles[-1]) + " = StringField('" + (field_name) + "')"
        sec_app_py_2 = "        " + (field_titles[-1]) + " = request.form['" + (field_name) + "']"
        sec_app_py_3 = "    " + (field_titles[-1]) + " = request.form['" + (field_name) + "']"


        with open("templates/product_page.html", "r") as product_page_file, open("pypim.py", "r") as app_py_file:
            buf = product_page_file.readlines()
            buf1 = app_py_file.readlines()

        with open("templates/product_page.html", "w") as out_file_p_page:
            for line in buf:
                if line == "        </table>\n":
                    line = sec_prod_page + "\n" + line
                out_file_p_page.write(line)

        with open("pypim.py", "w") as out_file_app_py:
            for line in buf1:

                if line == "    pic = FileField('Pic')\n":
                    line = sec_app_py_1 + "\n" + line
                elif line == "        pic = request.files['pic']\n":
                    line = sec_app_py_2 + "\n" + line
                elif re.search('(\s*.*\(\"SELECT \* FROM brands WHERE brand_name LIKE.*)(\".*)', line):
                    line = re.sub(r'(\s*.*)(\".*)', r'\1' + " OR " + field_titles[-1] + " LIKE %s" + r'\2', line)
                elif re.search('(\s*\(searchQuery.*)(\)\))', line):
                    line = re.sub(r'(\s*\(searchQuery, searchQuery.*)(\)\))', r'\1' + ", searchQuery" + r'\2', line)
                elif re.search('(\s*mySql_insert_query = """INSERT INTO brands.*)(\))', line):
                    line = re.sub(r'(\s*mySql_insert_query = """INSERT INTO brands.*)(\))', r'\1' + ", " + field_titles[-1] + r'\2', line)
                elif re.search('(\s*VALUES.*)(\)".*)', line):
                    line = re.sub(r'(\s*VALUES.*)(\)".*)', r'\1' + ", %s" + r'\2', line)
                elif line == "    pic = request.files['pic']\n":
                    line = sec_app_py_3 + "\n" + line
                elif re.search('(.*)(\sWHERE id=%s.*)(,.*(!pic.filename), id.*)', line):
                    line = re.sub(r'(.*)(\sWHERE id=%s.*)(, id.*)', r'\1' + ", " + field_titles[-1] + "=%s" + r'\2' + ", " + field_titles[-1] + r'\3', line)
                out_file_app_py.write(line)


        # create a message to send to the template
        message = f"The field {field_name} has been add to products table."

        return render_template('fields_manager.html', message=message, )
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in formField.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(formField, field).label.text,
                    error
                ), 'error')
        return render_template('fields_manager.html', formField=formField)



# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__": app.run(debug=True)
