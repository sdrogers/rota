import os
from dotenv import load_dotenv
from sre_constants import LITERAL_LOC_IGNORE
from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired


load_dotenv()


app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy(app)

Bootstrap(app)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __repr__(self):
        return self.name

class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    member = db.relationship('Member', backref=db.backref('mlogs', lazy=True))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    activity = db.relationship('Activity', backref=db.backref('alogs', lazy=True))
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<{self.member} {self.activity}>'

class MemberForm(FlaskForm):
    name = StringField("Member's name", validators=[DataRequired()])
    submit = SubmitField('Submit')


def member_choices():
    return Member.query.all()
def activity_choices():
    return Activity.query.all()

class LogEntryForm(FlaskForm):
    member = QuerySelectField('Member', validators=[DataRequired()], query_factory=member_choices)
    activity = QuerySelectField('Activity', validators=[DataRequired()], query_factory=activity_choices)
    date = DateField('Date')
    submit = SubmitField('Submit')

    

def compute_totals():
    log_items = LogEntry.query.all()
    members = Member.query.all()
    activities = Activity.query.all()
    totals_list = []

    for m in members:
        new_dict = {'member': m.name}
        for activity in activities:
            a = list(filter(lambda x: x.activity_id == activity.id and x.member_id == m.id, log_items))
            new_dict[activity.name] = len(a)
        try:
            new_dict['duty_ratio'] = 100 * (new_dict['ood'] + new_dict['safety']) / (new_dict['ood'] + new_dict['race'] + new_dict['safety'])
        except ZeroDivisionError:
            new_dict['duty_ratio'] = 100
        totals_list.append(new_dict)

  
    
    totals_list.sort(key=lambda x: x['duty_ratio'])
    return totals_list

    
@app.route("/")
def index():
    totals_list = compute_totals()
    return render_template("index.html", totals_list=totals_list)

@app.route("/add_member", methods=['GET', 'POST'])
def add_member():
    form = MemberForm()
    current_member_names = set([m.name.lower() for m in Member.query.all()])
    message = ''
    if form.validate_on_submit():
        name = form.name.data
        if name.lower() in current_member_names:
            message = 'Member with that name already exists'
        else:
            new_member = Member(name=name)
            db.session.add(new_member)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('add_member.html', form=form, message=message)

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    form = LogEntryForm()
    if form.validate_on_submit():
        member_id = form.member.data.id
        activity_id = form.activity.data.id
        new_entry = LogEntry(member_id=member_id, activity_id=activity_id, date=form.date.data)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_entry.html', form=form)

@app.route('/single_member', methods=['GET'])
def single_member():
    member_id = request.args.get('member_id', None)
    if member_id is None:
        member_name = request.args.get('member_name')
        member_id = Member.query.filter_by(name=member_name).first().id
    entries = LogEntry.query.filter_by(member_id=member_id).order_by('date')
    member = Member.query.filter_by(id=member_id).first()
    return render_template('entry_list.html', entries=entries, member_name=member.name)

@app.route('/all_entries', methods=['GET'])
def all_entries():
    entries = LogEntry.query.all()
    entries.sort(key=lambda x: x.date, reverse=True)
    member_name = 'All members'
    return render_template('entry_list.html', entries=entries, member_name=member_name)

@app.route('/delete_entry', methods=['GET'])
def delete_entry():
    entry_id = request.args.get('entry_id')
    entry = LogEntry.query.filter_by(id=entry_id).first()
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_member', methods=['GET'])
def delete_member():
    member_id = request.args.get('member_id')
    entries = LogEntry.query.filter_by(member_id=member_id)
    for entry in entries:
        db.session.delete(entry)
    member = Member.query.filter_by(id=member_id).first()
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('index'))

    
@app.route('/list_members', methods=['GET'])
def list_members():
    members = Member.query.all()
    return render_template('member_list.html', members=members)