import os
import re

from deapp import app, mysql

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


conf = yaml.load(open('dbconf.yaml'), Loader=yaml.FullLoader)
# image upload folder and extensions
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = conf['upload_folder']


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

def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('index.html', brands=brands)

def searchresult():
    searchQuery = "%" + request.form.get("query") + "%"
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands WHERE brand_name LIKE %s OR founded LIKE %s OR headquarters LIKE %s OR products LIKE %s",
                (searchQuery, searchQuery, searchQuery, searchQuery))
    brands = cur.fetchall()
    return render_template('search_results.html', brands=brands)


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
        mySql_insert_query = ("INSERT INTO brands (brand_name, founded, headquarters, products, pic)"        
                                "VALUES (%s, %s, %s, %s, %s)")
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


def select_record():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('select_strain.html', brands=brands)


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


def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']

    cur = mysql.connection.cursor()
    deleteSQL = "DELETE FROM brands WHERE id=%s"
    cur.execute("""SELECT * FROM brands WHERE id = %s""", (id,))
    brand = cur.fetchone()

    if purpose == 'delete':
        cur.execute(deleteSQL, (id,))
        mysql.connection.commit()
        message = f"The strain {brand['brand_name']} has been deleted from the database."
        return render_template('result.html', message=message)
    else:
        # this calls an error handler
        abort(405)



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


def brands():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands")
    brands = cur.fetchall()
    return render_template('strains.html', brands=brands)


def brand(id):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM brands WHERE id = %s""", (id,))
    brands = cur.fetchall()
    return render_template('product_page.html', brands=brands)