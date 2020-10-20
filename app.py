import os
from os import abort

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm
from flask_wtf.file import FileField

from wtforms import SubmitField, SelectField, RadioField, HiddenField, StringField, IntegerField, FloatField
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'MLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)



# change to name of your database; add path if necessary
db_name = 'C:\DB\potlopedia.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

# image upload folder and extensions
UPLOAD_FOLDER = 'C:/Users/tunke/PycharmProjects/Potlopedia_2.0/static/prod_pics/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# each table in the database needs a class to be created for it
# db.Model is required - don't change it
# identify all columns by name and data type
class Strain(db.Model):
    __tablename__ = 'strains'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    strain_name = db.Column(db.VARCHAR)
    strain_type = db.Column(db.VARCHAR)
    lineage = db.Column(db.VARCHAR)
    pic = db.Column(db.VARCHAR)

    def __init__(self, strain_name, strain_type, lineage, pic):
        self.strain_name = strain_name
        self.strain_type = strain_type
        self.lineage = lineage
        self.pic = pic


class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    strain_name = StringField('Strain name')
    strain_type = StringField('Strain type')
    lineage = StringField('Lineage')
    pic = FileField('Pic')
    submit = SubmitField('Add/Update Record')


# small form
class DeleteForm(FlaskForm):
    id_field = HiddenField()
    purpose = HiddenField()
    submit = SubmitField('Delete This Strain')


@app.route("/")
def home():
    return render_template('index.html') \

@app.route("/boot")
def boot():
    return render_template('base.html')


# add a new strain to the database
@app.route('/add_strain', methods=['GET', 'POST'])
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        strain_name = request.form['strain_name']
        strain_type = request.form['strain_type']
        lineage = request.form['lineage']
        pic = request.files['pic']
        pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic.filename))

        # the data to be inserted into Strain model - the table, strains
        record = Strain(strain_name, strain_type, lineage, pic.filename)
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        # create a message to send to the template
        message = f"The data for strain {strain_name} has been submitted."

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
    strains = Strain.query.all()
    return render_template('select_strain.html', strains=strains)


# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
def edit_or_delete():
    id = request.form['id']
    choice = request.form['choice']
    strain = Strain.query.filter(Strain.id == id).first()
    # two forms in this template
    form1 = AddRecord()
    form2 = DeleteForm()
    return render_template('edit_or_delete.html', strain=strain, form1=form1, form2=form2, choice=choice)


@app.route('/delete_result', methods=['POST'])
def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']
    strain = Strain.query.filter(Strain.id == id).first()
    if purpose == 'delete':
        db.session.delete(strain)
        db.session.commit()
        message = f"The strain {strain.strain_name} has been deleted from the database."
        return render_template('result.html', message=message)
    else:
        # this calls an error handler
        abort(405)


# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
def edit_result():
    id = request.form['id_field']
    # call up the record from the database
    strain = Strain.query.filter(Strain.id == id).first()
    # update all values
    strain.strain_name = request.form['strain_name']
    strain.strain_type = request.form['strain_type']
    strain.lineage = request.form['lineage']
    strain.pic = request.files['pic'].filename
    strain.pic1 = request.files['pic']
    strain.pic1.save(os.path.join(app.config['UPLOAD_FOLDER'], strain.pic1.filename))

    form1 = AddRecord()
    if form1.validate_on_submit():
        # update database record
        db.session.commit()
        # create a message to send to the template
        message = f"The data for strain {strain.strain_name} has been updated."
        return render_template('result.html', message=message)
    else:
        # show validaton errors
        strain.id = id
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('edit_or_delete.html', form1=form1, strain=strain, choice='edit')


@app.route("/strains")
def strains():
    strains = Strain.query.all()
    return render_template('strains.html', strains=strains)


@app.route("/strain/<id>")
def strain(id):
    strains = Strain.query.filter_by(id=id).all()
    Strain.id == id
    return render_template('product_page.html', strains=strains)


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        req = request.form
        print(req)

        return redirect(request.url)

    return render_template("sign_up.html")


if __name__ == "__main__": app.run(debug=True)
