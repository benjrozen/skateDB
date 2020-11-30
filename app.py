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

# image upload folder and extensions
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = conf['upload_folder']

#################################THIS WILL WORK FOR sure

@app.route('/git_up', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo(conf['remote_repo'])
        origin = repo.remotes.origin
        origin.pull()
        return 'Deploy Success', 200
    else:
        return 'Deploy no success', 400


class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    brand_name = StringField('Brand name')
    founded = StringField('Founded')
    headquarters = StringField('Headquarters')
    products = StringField('Products')
    pic = FileField('Pic')
    submit = SubmitField('Add/Update Record')


# small form
class DeleteForm(FlaskForm):
    id_field = HiddenField()
    purpose = HiddenField()
    submit = SubmitField('Delete This Brand')


class AddField(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    field_name = StringField('Field Name')
    submit = SubmitField('Add/Update Record')


@app.route("/")
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('index.html', brands=brands)


@app.route("/result", methods=['POST'])
def searchresult():
    searchQuery = "%" + request.form.get("query") + "%"
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands WHERE brand_name LIKE %s OR founded LIKE %s OR headquarters LIKE %s OR products LIKE %s",
                (searchQuery, searchQuery, searchQuery, searchQuery))
    brands = cur.fetchall()
    return render_template('search_results.html', brands=brands)


@app.route("/boot")
def boot():
    return render_template('base.html')


# add a new strain to the database
@app.route('/add_strain', methods=['GET', 'POST'])
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        brand_name = request.form['brand_name']
        founded = request.form['founded']
        headquarters = request.form['headquarters']
        products = request.form['products']
        pic = request.files['pic']
        pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic.filename))

        cur = mysql.connection.cursor()
        mySql_insert_query = """INSERT INTO brands (brand_name, founded, headquarters, products, pic) 
                                VALUES (%s, %s, %s, %s, %s) """
        recordTuple = (brand_name, founded, headquarters, products, pic.filename)
        cur.execute(mySql_insert_query, recordTuple)
        mysql.connection.commit()

        # create a message to send to the template
        message = f"The data for strain {brand_name} has been submitted."

        return render_template('add_strain.html', message=message, )
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('add_strain.html', form1=form1)


# select a record to edit or delete
@app.route('/select_record')
def select_record():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('select_strain.html', brands=brands)


# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
def edit_or_delete():
    id = request.form['id']
    choice = request.form['choice']
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM brands WHERE id = %s""", (id,))
    brand = cur.fetchone()
    # two forms in this template
    form1 = AddRecord()
    form2 = DeleteForm()
    return render_template('edit_or_delete.html', brand=brand, form1=form1, form2=form2, choice=choice)


@app.route('/delete_result', methods=['POST'])
def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']

    cur = mysql.connection.cursor()
    deleteSQL = "DELETE FROM brands WHERE id=%s"
    cur.execute("""SELECT * FROM strains WHERE id = %s""", (id,))
    brand = cur.fetchone()

    if purpose == 'delete':
        cur.execute(deleteSQL, (id,))
        mysql.connection.commit()
        message = f"The strain {brand['brand_name']} has been deleted from the database."
        return render_template('result.html', message=message)
    else:
        # this calls an error handler
        abort(405)


# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
def edit_result():
    id = request.form['id_field']
    # call up the record from the database
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM brands WHERE id = %s""", (id,))
    # update all values
    brand_name = request.form['brand_name']
    founded = request.form['founded']
    headquarters = request.form['headquarters']
    products = request.form['products']
    pic = request.files['pic']
    if len(pic.filename) > 0 :
        pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic.filename))
        cur.execute("UPDATE brands SET pic=%s WHERE id=%s", (pic.filename, id))
    form1 = AddRecord()
    if form1.validate_on_submit():
        # update database record
        cur = mysql.connection.cursor()
        cur.execute("UPDATE brands SET brand_name=%s, founded=%s, headquarters=%s, products=%s WHERE id=%s", (brand_name, founded, headquarters, products, id))
        mysql.connection.commit()
        # create a message to send to the template
        message = f"The data for brand {brand_name} has been updated."
        return render_template('result.html', message=message)
    else:
        # show validaton errors
        brand.id = id
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('edit_or_delete.html', form1=form1, brand=brand, choice='edit')


@app.route("/brands")
def brands():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('strains.html', brands=brands)


@app.route("/brand/<id>")
def brand(id):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM brands WHERE id = %s""", (id,))
    brands = cur.fetchall()
    return render_template('product_page.html', brands=brands)


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        req = request.form
        print(req)

        return redirect(request.url)

    return render_template("sign_up.html")

@app.route("/regex", methods=["GET", "POST"])
def regex():

    field = "THC"
    pattern = '(\s*mySql_insert_query = \"\"\"INSERT INTO strains.*)(\)\n'

    with open("templates/product_page.html", "r") as product_page_file, open("out_file.py", "r") as app_py_file:
        buf = product_page_file.readlines()
        buf1 = app_py_file.readlines()


    with open("out_file.py", "w") as out_file_app_py:
        for line in buf1:
            if re.match(r"(\s*mySql_insert_query = \"\"\"INSERT INTO strains.*)(\))\n", line):
                line = re.sub(r"(\s*mySql_insert_query = \"\"\"INSERT INTO strains.*)(\))\n", r"\1," + field + r"\2\n", line)
            out_file_app_py.write(line)

            # search = re.search(r"(\s*mySql_insert_query = \"\"\"INSERT INTO strains.*)(\))\n", line)
            # if line == search:
            #     line = re.sub(r"(\s*mySql_insert_query = \"\"\"INSERT INTO strains.*)(\))\n", r"\1," + field + r"\2\n", line)
            # out_file_app_py.write(line)



    return "Welll done"


# Add a new field to product page
@app.route("/fields-manager", methods=["GET", "POST"])
def field_manager():
    formField = AddField()
    if formField.validate_on_submit():
        field_name = request.form['field_name']
        cur = mysql.connection.cursor()
        mySql_add_field_query = "ALTER TABLE strains ADD %s VARCHAR(255)" % (field_name)
        cur.execute(mySql_add_field_query)
        mysql.connection.commit()
        cur.execute("SELECT * FROM strains")
        fields = cur.fetchall()
        field_titles = [i[0] for i in cur.description]

        sec_prod_page = """      <tr>
            <td class="table_header">""" + (field_titles[-1]) + """</td><td>{{ strain.""" + (field_name) + """}}</td>
         </tr>"""
        sec_app_py_1 = "    " + (field_titles[-1]) + " = StringField('"+ (field_name) + "')"
        sec_app_py_2 = "        " + (field_titles[-1]) + " = request.form['"+ (field_name) + "']"

        with open("templates/product_page.html", "r") as product_page_file, open("app.py", "r") as app_py_file:
            buf = product_page_file.readlines()
            buf1 = app_py_file.readlines()

        with open("templates/product_page.html", "w") as out_file_p_page:
            for line in buf:
                if line == "        </table>\n":
                    line = sec_prod_page + "\n" + line
                out_file_p_page.write(line)

        with open("app.py", "w") as out_file_app_py:
            for line in buf1:
                if line == "    pic = FileField('Pic')\n":
                    line = sec_app_py_1 + "\n" + line
                elif line == "        pic = request.files['pic']\n":
                    line = sec_app_py_2 + "\n" + line
                elif line == '        mySql_insert_query = """INSERT INTO strains (strain_name, strain_type, lineage, pic)':
                    re.sub(r'(\s*mySql_insert_query = """INSERT INTO strains.*)(\))', '\1,' + field_titles[-1] + '\2', line)
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