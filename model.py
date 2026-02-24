from extensions import db
from datetime import datetime
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    phone = db.Column(db.String(30), unique=True)
    nativity = db.Column(db.String(120))
    membership_id = db.Column(db.String(20), unique=True)
    photo = db.Column(db.String(255))
    password = db.Column(db.String(255))

    membership_start = db.Column(db.Date)
    membership_end = db.Column(db.Date)

    is_admin = db.Column(db.Boolean, default=False)
    section_admin = db.Column(db.Boolean, default=False)

    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    whatsapp = db.Column(db.String(20))
    dob = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    interests = db.Column(db.Text)

    # ✅ FIXED INDENTATION
    renewals = db.relationship(
        "Renewal",
        backref="user",
        cascade="all, delete"
    )

    receipts = db.relationship(
        "Receipt",
        backref="user",
        cascade="all, delete"
    )
# ---------------- ANNOUNCEMENTS ----------------

class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    image = db.Column(db.String(255))
    created_at = db.Column(db.Date)

# ---------------- RENEWALS ----------------

class Renewal(db.Model):
    __tablename__ = "renewals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    amount = db.Column(db.Integer)
    screenshot = db.Column(db.String(255))
    status = db.Column(db.String(20), default="PENDING")
    requested_at = db.Column(db.Date)

# ---------------- RECEIPTS ----------------

class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    amount = db.Column(db.Integer)
    issued_date = db.Column(db.Date)
    membership_start = db.Column(db.Date)
    membership_end = db.Column(db.Date)

# ---------------- SETTINGS ----------------

class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(100))

# ---------------- EVENTS ----------------

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.String(20))   # keep string for flexibility
    description = db.Column(db.Text)

    image = db.Column(db.Text)              # used in website
    pinned = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class EventParticipant(db.Model):
    __tablename__ = "event_participants"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    registered_at = db.Column(db.Date)

    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id"),
    )
# ---------------- COMMITTEES ----------------

# ---------------- MEDICAL ----------------

# ======================================================
# MEDICAL INVENTORY MODELS
# ======================================================

class EquipmentCategory(db.Model):
    __tablename__ = "equipment_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    prefix = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text)


class EquipmentItem(db.Model):
    __tablename__ = "equipment_items"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("equipment_categories.id"),
        nullable=False
    )

    item_code = db.Column(db.String(20), unique=True)
    status = db.Column(db.String(20), default="AVAILABLE")
    condition = db.Column(db.String(50), default="GOOD")

    category = db.relationship("EquipmentCategory")


class EquipmentMovement(db.Model):
    __tablename__ = "equipment_movements"

    id = db.Column(db.Integer, primary_key=True)

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("equipment_items.id"),
        nullable=False
    )

    taker_name = db.Column(db.String(120))
    taker_phone = db.Column(db.String(20))

    issue_date = db.Column(db.Date)
    expected_return_date = db.Column(db.Date)
    actual_return_date = db.Column(db.Date)

    status = db.Column(db.String(20), default="ISSUED")  # ISSUED, RETURNED, OVERDUE

    item = db.relationship("EquipmentItem")

# ---------------- COMMITTEES ----------------

class Committee(db.Model):
    __tablename__ = "committees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class CommitteeMember(db.Model):
    __tablename__ = "committee_members"

    id = db.Column(db.Integer, primary_key=True)
    committee_id = db.Column(db.Integer, db.ForeignKey('committees.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(20), default="member")


class CommitteeMeeting(db.Model):
    __tablename__ = "committee_meetings"

    id = db.Column(db.Integer, primary_key=True)
    committee_id = db.Column(db.Integer, db.ForeignKey('committees.id'))

    title = db.Column(db.String(200))

    meeting_date = db.Column(db.Date)
    start_time = db.Column(db.String(10))   # Scheduled
    end_time = db.Column(db.String(10))     # Scheduled

    actual_start = db.Column(db.DateTime)   # 🔥 NEW
    actual_end = db.Column(db.DateTime)     # 🔥 NEW

    status = db.Column(db.String(20), default="SCHEDULED")  # 🔥 NEW

    token = db.Column(db.String(100))


class CommitteeMeetingAttendance(db.Model):
    __tablename__ = "committee_meeting_attendance"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('committee_meetings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scan_time = db.Column(db.DateTime, default=datetime.utcnow)
    attended_minutes = db.Column(db.Integer) 



class BaseContent:
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ADMIN(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)  # ✅ REQUIRED

    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)




class Sport(db.Model):
    __tablename__ = "sports"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    event_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Charity(db.Model):
    __tablename__ = "charity"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    event_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Award(db.Model):
    __tablename__ = "awards"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    year = db.Column(db.String(10))
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
