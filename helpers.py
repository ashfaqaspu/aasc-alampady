from flask import session
from datetime import date
import os
import pandas as pd

from werkzeug.security import generate_password_hash

from extensions import db
from model import (
    User,
    Setting,
    CommitteeMember
)

# 🔥 IMPORTANT: Define these properly
SUPER_ADMIN_PHONE = "7012538103"

# Membership constants
MEMBERSHIP_START = date(2024, 4, 1)
MEMBERSHIP_END = date(2027, 3, 31)


# ======================================================
# AUTH HELPERS
# ======================================================

def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])


def is_admin():
    user = current_user()
    return user and user.is_admin


def is_super_admin():
    user = current_user()
    return user and user.phone == SUPER_ADMIN_PHONE


def is_section_admin():
    user = current_user()
    return user and user.section_admin


def is_renewal_enabled():
    setting = Setting.query.filter_by(key="renewal_enabled").first()
    return setting and setting.value == "1"


def is_expired(user):
    if not user or not user.membership_end:
        return True
    return date.today() > user.membership_end


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )


# ======================================================
# COMMITTEE HELPERS
# ======================================================

def is_committee_member(cid):
    if "user_id" not in session:
        return False

    return CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session["user_id"]
    ).first() is not None


def is_committee_admin(cid):
    if "user_id" not in session:
        return False

    return CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session["user_id"],
        role="admin"
    ).first() is not None


# ======================================================
# MEMBER IMPORT
# ======================================================

def import_members_from_excel():
    print("=== IMPORT STARTED ===")

    EXCEL_FILE = "members.xlsx"

    if not os.path.exists(EXCEL_FILE):
        print("Excel file NOT FOUND")
        return

    df = pd.read_excel(EXCEL_FILE, header=None)

    counter = 2

    for _, row in df.iterrows():
        try:
            phone = str(row[1]).strip()

            existing = User.query.filter_by(phone=phone).first()
            if existing:
                print(f"Skipping duplicate phone: {phone}")
                continue

            user = User(
                name=str(row[0]).strip(),
                phone=phone,
                nativity=str(row[2]).strip(),
                membership_id=f"AASC{str(counter).zfill(3)}",
                password=generate_password_hash(phone),
                membership_start=MEMBERSHIP_START,
                membership_end=MEMBERSHIP_END
            )

            db.session.add(user)
            db.session.commit()

            print(f"Imported: {phone}")
            counter += 1

        except Exception as e:
            db.session.rollback()
            print("Error importing row:", e)

    print("=== IMPORT COMPLETED ===")


def generate_membership_id(num):
    return f"AASC{str(num).zfill(3)}"