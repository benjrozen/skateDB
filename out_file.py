from flask import request, render_template, flash
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, FileField, SubmitField
from flask_mysqldb import MySQL
mysql = MySQL(app)


class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    strain_name = StringField('Strain name')
    strain_type = StringField('Strain type')
    lineage = StringField('Lineage')
    pic = FileField('Pic')
    submit = SubmitField('Add/Update Record')

@app.route('/add_strain', methods=['GET', 'POST'])
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        strain_name = request.form['strain_name']
        strain_type = request.form['strain_type']
        lineage = request.form['lineage']
        pic = request.files['pic']

        cur = mysql.connection.cursor()
        mySql_insert_query = """INSERT INTO strains (strain_name, strain_type, lineage, pic,THC,THC,THC,THC,THC)
                                        VALUES (%s, %s, %s, %s) """
        recordTuple = (strain_name, strain_type, lineage, pic.filename)
        cur.execute(mySql_insert_query, recordTuple)
        mysql.connection.commit()

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

