import os
import re

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
from os import abort
from flask import Flask, render_template, request, redirect, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField, HiddenField, StringField
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
def brands():
    return pypim.brands()


@app.route("/brand/<id>")
def brand(id):
    return pypim.brand(id)


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        req = request.form
        print(req)

        return redirect(request.url)

    return render_template("sign_up.html")


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


if __name__ == "__main__": app.run(debug=True)
