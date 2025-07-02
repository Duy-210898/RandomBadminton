from . import db
from sqlalchemy import ForeignKey

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    groups = db.relationship("Group", backref="tournament", lazy=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    tournament_id = db.Column(db.Integer, db.ForeignKey("tournament.id"), nullable=False)
    teams = db.relationship("Team", backref="group", lazy=True)
    matches = db.relationship("Match", backref="group", lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    tier1 = db.Column(db.String(50))
    tier2 = db.Column(db.String(50))
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey("tournament.id"), nullable=True)
    team1 = db.Column(db.String(100))
    team2 = db.Column(db.String(100))
    score1 = db.Column(db.Integer)
    score2 = db.Column(db.Integer)

    tournament = db.relationship("Tournament", backref="knockout_matches", lazy=True)
