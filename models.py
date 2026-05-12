from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from bson import ObjectId


# ── Enums (kept identical so templates / app.py need no changes) ──────────────

class ItemStatusEnum(Enum):
    LOST = 'lost'
    FOUND = 'found'

class CourseEnum(Enum):
    BTECH = 'Btech'
    BARCH = 'Barch'
    MTECH = 'Mtech'
    MSC = 'Msc'
    PHD = 'PHD'

class BranchEnum(Enum):
    CSE = 'CSE'
    ECE = 'ECE'
    EEE = 'EEE'
    ICE = 'ICE'
    CHEM = 'Chem'
    CIVIL = 'Civil'
    MECH = 'MECH'
    PROD = 'Prod'
    OTHER = 'Other'


# ── Flask-Login compatible User wrapper ────────────────────────────────────────
# MongoDB stores users as plain dicts; this class wraps a doc so flask-login
# and all existing app.py references (current_user.email, etc.) keep working.

class User(UserMixin):
    def __init__(self, doc: dict):
        self._doc = doc

    # flask-login requires get_id() to return a string
    def get_id(self):
        return str(self._doc['_id'])

    # Attribute-style access so current_user.email etc. still work
    def __getattr__(self, name):
        try:
            return self._doc[name]
        except KeyError:
            raise AttributeError(f"User has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._doc[name] = value

    # Convenience: expose the raw ObjectId
    @property
    def id(self):
        return str(self._doc['_id'])

    @property
    def is_verified(self):
        return self._doc.get('is_verified', False)

    def to_dict(self):
        return self._doc


# ── MongoDB collection helpers (used inside app.py via mongo.db.*) ─────────────
# No ORM needed — pure PyMongo.  Keeping this file lightweight.
