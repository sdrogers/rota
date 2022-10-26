from random import choice
from app import db, app
from app import Member, Activity, LogEntry
from faker import Faker
app_ctx = app.app_context()
app_ctx.push()

db.drop_all()
db.session.commit()

db.create_all()

fake = Faker()

# make some members
names = ['Simon', 'Peter', 'Andy M', 'Tom']
members = []
for name in names:
    new_member = Member(name=name)
    db.session.add(new_member)
    members.append(new_member)

db.session.commit()

activities = []
activity_names = ['race', 'ood', 'safety']
for activity in activity_names:
    new_activity = Activity(name=activity)
    db.session.add(new_activity)
    activities.append(new_activity)

db.session.commit()

members = Member.query.all()
activites = Activity.query.all()

n = 20
for i in range(n):
    member = choice(members)
    activity = choice(activities)
    date = fake.date_object()
    new_log = LogEntry(member_id=member.id, activity_id=activity.id, date=date)
    db.session.add(new_log)

db.session.commit()

test = LogEntry.query.all()
for t in test:
    print(t)

from app import compute_totals

print(compute_totals())