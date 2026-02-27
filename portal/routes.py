from . import portal_bp
from flask import render_template, redirect, url_for, request, session

from extensions import db
from model import *
from flask import request, session, redirect, url_for, render_template, flash
from helpers import *
from werkzeug.security import generate_password_hash, check_password_hash




from flask import request, session, redirect
from werkzeug.security import check_password_hash

@portal_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = User.query.filter_by(phone=request.form["phone"]).first()

        if not user or not check_password_hash(user.password, request.form["password"]):
            error = "Invalid phone or password"
        else:
            session["user_id"] = user.id
            return redirect(url_for("portal.dashboard"))

    return render_template("login.html", error=error)
def update_overdue_items():
    today = date.today()

    overdue_items = EquipmentMovement.query.filter(
        EquipmentMovement.status == "ISSUED",
        EquipmentMovement.expected_return_date < today
    ).all()

    for movement in overdue_items:
        movement.status = "OVERDUE"

    db.session.commit()

@portal_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user = current_user()

    announcements = Announcement.query.order_by(
        Announcement.id.desc()
    ).all()

    renewal = Renewal.query.filter_by(
        user_id=user.id
    ).order_by(Renewal.id.desc()).first()

    # ==========================
    # ADMIN DASHBOARD METRICS
    # ==========================

    total_members = User.query.count()

    active_members = User.query.filter(
        User.membership_end >= date.today()
    ).count()

    expired_members = total_members - active_members

    total_committees = Committee.query.count()

    total_events = Event.query.count()

    # ==========================
    # ✅ NEW MEDICAL LOGIC
    # ==========================

    update_overdue_items()

    total_medical_items = EquipmentItem.query.count()

    available_medical = EquipmentItem.query.filter_by(
        status="AVAILABLE"
    ).count()

    issued_medical = EquipmentItem.query.filter_by(
        status="ISSUED"
    ).count()

    overdue_medical = EquipmentMovement.query.filter_by(
        status="OVERDUE"
    ).count()

    # ==========================
    # RENEWAL METRICS
    # ==========================

    total_pending_renewals = Renewal.query.filter_by(
        status="PENDING"
    ).count()

    renewal_success_rate = 0
    total_renewals = Renewal.query.count()
    approved_renewals = Renewal.query.filter_by(
        status="APPROVED"
    ).count()

    if total_renewals > 0:
        renewal_success_rate = round(
            (approved_renewals / total_renewals) * 100, 2
        )

    return render_template(
        "dashboard.html",
        user=user,
        expired=is_expired(user),
        announcements=announcements,
        is_admin=is_admin(),
        is_super_admin=is_super_admin(),
        is_section_admin=is_section_admin(),
        renewal_enabled=is_renewal_enabled(),
        renewal_status=renewal.status if renewal else None,
        calculate_age=calculate_age,

        # Admin Metrics
        total_members=total_members,
        active_members=active_members,
        expired_members=expired_members,
        total_committees=total_committees,
        total_events=total_events,

        # ✅ NEW Medical Metrics
        total_medical_items=total_medical_items,
        available_medical=available_medical,
        issued_medical=issued_medical,
        overdue_medical=overdue_medical,

        # Renewal
        total_pending_renewals=total_pending_renewals,
        renewal_success_rate=renewal_success_rate
    )


@portal_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@portal_bp.route("/events")
def portal_events():

    if "user_id" not in session:
        return redirect("/")

    events = PortalEvent.query.order_by(
        PortalEvent.event_date.desc()
    ).all()

    # Get events user already registered for
    registered = PortalEventParticipant.query.filter_by(
        user_id=session["user_id"]
    ).all()

    registered_ids = [r.portal_event_id for r in registered]

    return render_template(
        "event.html",
        events=events,
        registered_ids=registered_ids
    )


@portal_bp.route("/events/participate/<int:event_id>")
def participate_portal_event(event_id):

    if "user_id" not in session:
        return redirect("/")

    existing = PortalEventParticipant.query.filter_by(
        portal_event_id=event_id,
        user_id=session["user_id"]
    ).first()

    if not existing:
        p = PortalEventParticipant(
            portal_event_id=event_id,
            user_id=session["user_id"]
        )
        db.session.add(p)
        db.session.commit()

    return redirect(url_for("portal.portal_events"))

@portal_bp.route("/membership-card")
def membership_card():
    if "user_id" not in session:
        return redirect("/")

    user = current_user()

    return render_template(
        "membership_card.html",
        user=user,
        expired=is_expired(user)
    )


@portal_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/")

    user = current_user()

    if request.method == "POST":
        user.password = generate_password_hash(request.form["password"])
        db.session.commit()
        return redirect(url_for("portal.dashboard"))

    return render_template("change_password.html")


@portal_bp.route("/complete-profile", methods=["GET", "POST"])
def complete_profile():

    if "user_id" not in session:
        return redirect("/")

    user = current_user()

    if request.method == "POST":

        user.address = request.form.get("address")
        user.email = request.form.get("email")
        user.whatsapp = request.form.get("whatsapp")

        dob = request.form.get("dob")
        if dob:
            user.dob = datetime.strptime(dob, "%Y-%m-%d").date()

        user.blood_group = request.form.get("blood_group")
        user.interests = ",".join(request.form.getlist("interests"))

        # ✅ PHOTO HANDLING
        photo = request.files.get("photo")

        if photo and photo.filename:
            os.makedirs("static/uploads", exist_ok=True)

            filename = f"user_{user.id}.jpg"

            # Save file physically
            photo.save(f"static/uploads/{filename}")

            # Save path in DB (WITHOUT static/)
            user.photo = f"uploads/{filename}"

        # ✅ Single commit
        db.session.commit()

        return redirect(url_for("portal.dashboard"))

    return render_template("complete_profile.html", user=user)


@portal_bp.route("/committee/<int:cid>")
def committee_dashboard(cid):
    if not is_committee_member(cid):
        return "Access Denied", 403

    meetings = CommitteeMeeting.query.filter_by(
        committee_id=cid
    ).order_by(CommitteeMeeting.meeting_date.desc()).all()

    return render_template(
        "committee_dashboard.html",
        cid=cid,
        meetings=meetings,
        is_admin=is_committee_admin(cid)
    )


@portal_bp.route("/committees")
def my_committees():

    if "user_id" not in session:
        return redirect("/")

    committees = Committee.query.join(
        CommitteeMember,
        CommitteeMember.committee_id == Committee.id
    ).filter(
        CommitteeMember.user_id == session["user_id"]
    ).all()

    return render_template(
        "my_committees.html",
        committees=committees
    )


@portal_bp.route("/committee/<int:cid>/add-member", methods=["GET", "POST"])
def add_committee_member(cid):
    if not is_committee_admin(cid):
        return "Access Denied", 403

    if request.method == "POST":
        user_id = request.form["user_id"]
        role = request.form["role"]

        existing = CommitteeMember.query.filter_by(
            committee_id=cid,
            user_id=user_id
        ).first()

        if not existing:
            cm = CommitteeMember(
                committee_id=cid,
                user_id=user_id,
                role=role
            )
            db.session.add(cm)
            db.session.commit()

        return redirect(url_for("portal.committee_members_page", cid=cid))

    subquery = db.session.query(
        CommitteeMember.user_id
    ).filter_by(committee_id=cid)

    users = User.query.filter(~User.id.in_(subquery)).all()

    return render_template(
        "committee_add_member.html",
        cid=cid,
        users=users
    )


import uuid
import qrcode
import os

@portal_bp.route("/admin/meeting/start/<int:meeting_id>")
def start_meeting(meeting_id):

    if not is_admin():
        return "Access Denied", 403

    meeting = db.session.get(CommitteeMeeting, meeting_id)

    if not meeting:
        return "Meeting not found"

    if meeting.status != "SCHEDULED":
        return redirect(url_for("portal.committee_dashboard", cid=meeting.committee_id))

    meeting.actual_start = datetime.utcnow()
    meeting.status = "ONGOING"

    db.session.commit()

    return redirect(url_for("portal.committee_dashboard", cid=meeting.committee_id))





@portal_bp.route("/committee/<int:cid>/create-meeting", methods=["GET", "POST"])
def create_meeting(cid):
    if not is_committee_admin(cid):
        return "Access Denied", 403

    if request.method == "POST":
        token = str(uuid.uuid4())

        meeting = CommitteeMeeting(
            committee_id=cid,
            title=request.form["title"],
            meeting_date=request.form["meeting_date"],
            start_time=request.form["start_time"],
            end_time=request.form["end_time"],
            token=token
        )

        db.session.add(meeting)
        db.session.commit()

        qr_url = url_for("portal.scan_attendance", token=token, _external=True)
        img = qrcode.make(qr_url)

        os.makedirs("static/qrcodes", exist_ok=True)
        img.save(f"static/qrcodes/meeting_{meeting.id}.png")

        return redirect(url_for("portal.committee_dashboard", cid=cid))

    return render_template("create_meeting.html", cid=cid)



@portal_bp.route("/attendance/scan/<token>")
def scan_attendance(token):

    if "user_id" not in session:
        return redirect("/")

    meeting = CommitteeMeeting.query.filter_by(token=token).first()

    if not meeting:
        return render_template(
            "attendance_result.html",
            message="Invalid QR Code",
            time="—",
            minutes=0,
            total_time=0,
            attended_time=0
        )

    now = datetime.now()

    # 🔹 Validate date
    if now.date() != meeting.meeting_date:
        return render_template(
            "attendance_result.html",
            message="Meeting is not scheduled for today",
            time=now.strftime("%H:%M"),
            minutes=0,
            total_time=0,
            attended_time=0
        )

    # 🔹 Validate time
    meeting_start = datetime.combine(
        meeting.meeting_date,
        datetime.strptime(meeting.start_time, "%H:%M").time()
    )

    meeting_end = datetime.combine(
        meeting.meeting_date,
        datetime.strptime(meeting.end_time, "%H:%M").time()
    )

    if now < meeting_start or now > meeting_end:
        return render_template(
            "attendance_result.html",
            message="Meeting is not active",
            time=now.strftime("%H:%M"),
            minutes=0,
            total_time=0,
            attended_time=0
        )

    # 🔹 Prevent duplicate
    existing = CommitteeMeetingAttendance.query.filter_by(
        meeting_id=meeting.id,
        user_id=session["user_id"]
    ).first()

    if existing:
        return render_template(
            "attendance_result.html",
            message="Attendance already marked",
            time=existing.scan_time.strftime("%H:%M"),
            minutes=existing.attended_minutes,
            total_time=0,
            attended_time=existing.attended_minutes
        )

    # 🔹 Calculate remaining minutes
    attended_minutes = int((meeting_end - now).total_seconds() / 60)
    attended_minutes = max(attended_minutes, 0)

    attendance = CommitteeMeetingAttendance(
        meeting_id=meeting.id,
        user_id=session["user_id"],
        scan_time=now,
        attended_minutes=attended_minutes
    )

    db.session.add(attendance)
    db.session.commit()

    # 🔹 Total meeting duration
    total_time = int((meeting_end - meeting_start).total_seconds() / 60)

    return render_template(
        "attendance_result.html",
        message="Attendance marked successfully ✅",
        time=now.strftime("%H:%M"),
        minutes=attended_minutes,
        total_time=total_time,
        attended_time=attended_minutes
    )
    
@portal_bp.route("/admin/meeting/end/<int:meeting_id>")
def end_meeting(meeting_id):

    if not is_admin():
        return "Access Denied", 403

    meeting = db.session.get(CommitteeMeeting, meeting_id)

    if not meeting:
        return "Meeting not found"

    if meeting.status != "ONGOING":
        return redirect(url_for("portal.committee_dashboard", cid=meeting.committee_id))

    # 🔹 Update meeting status
    meeting.actual_end = datetime.utcnow()
    meeting.status = "COMPLETED"
    meeting.token = None  # Disable QR scanning

    # 🔹 Delete QR image file
    qr_path = f"static/qrcodes/meeting_{meeting.id}.png"

    if os.path.exists(qr_path):
        os.remove(qr_path)

    db.session.commit()

    return redirect(url_for("portal.committee_dashboard", cid=meeting.committee_id))


@portal_bp.route("/committee/meeting/<int:mid>/report")
def meeting_report(mid):

    meeting = CommitteeMeeting.query.get_or_404(mid)

    # 🔐 Check admin access
    member = CommitteeMember.query.filter_by(
        committee_id=meeting.committee_id,
        user_id=session.get("user_id")
    ).first()

    if not member or member.role != "admin":
        return "Access Denied", 403

    # 🔹 Attendance records
    records = db.session.query(
        User.name,
        CommitteeMeetingAttendance.scan_time,
        CommitteeMeetingAttendance.attended_minutes
    ).join(
        CommitteeMeetingAttendance,
        CommitteeMeetingAttendance.user_id == User.id
    ).filter(
        CommitteeMeetingAttendance.meeting_id == mid
    ).all()

    # 🔹 Calculate total meeting time (scheduled duration)
    total_time = 0

    if meeting.start_time and meeting.end_time:
        try:
            start = datetime.strptime(meeting.start_time, "%H:%M")
            end = datetime.strptime(meeting.end_time, "%H:%M")
            total_time = int((end - start).total_seconds() / 60)
        except:
            total_time = 0

    return render_template(
        "meeting_report.html",
        meeting=meeting,
        records=records,
        total_time=total_time
    )



@portal_bp.route("/committee/<int:cid>/monthly-report")
def monthly_report(cid):

    month = request.args.get("month")  # format YYYY-MM

    # 🔐 Authorization
    member = CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session.get("user_id")
    ).first()

    if not member or member.role != "admin":
        return "Access Denied", 403

    data = []
    processed_data = []
    total_meeting_time = 0
    total_attended_time = 0

    if month:

        # 🔹 Get all meetings for that month
        meetings = CommitteeMeeting.query.filter(
            CommitteeMeeting.committee_id == cid,
            db.func.to_char(CommitteeMeeting.meeting_date, 'YYYY-MM') == month
        ).all()

        # 🔹 Calculate total scheduled meeting time (in minutes)
        for m in meetings:
            if m.start_time and m.end_time:
                try:
                    start = datetime.strptime(m.start_time, "%H:%M")
                    end = datetime.strptime(m.end_time, "%H:%M")
                    diff = (end - start).total_seconds() / 60
                    total_meeting_time += max(diff, 0)
                except:
                    pass

        # 🔹 Total attended minutes per user
        data = db.session.query(
            User.name,
            db.func.coalesce(
                db.func.sum(CommitteeMeetingAttendance.attended_minutes), 0
            )
        ).join(
            CommitteeMeetingAttendance,
            CommitteeMeetingAttendance.user_id == User.id
        ).join(
            CommitteeMeeting,
            CommitteeMeeting.id == CommitteeMeetingAttendance.meeting_id
        ).filter(
            CommitteeMeeting.committee_id == cid,
            db.func.to_char(CommitteeMeeting.meeting_date, 'YYYY-MM') == month
        ).group_by(User.id).all()

        # 🔹 Calculate total attended minutes (all users combined)
        total_attended_time = sum([d[1] for d in data]) if data else 0

        # 🔹 Calculate attendance percentage per user
        for name, attended in data:
            if total_meeting_time > 0:
                percentage = round((attended / total_meeting_time) * 100, 2)
            else:
                percentage = 0

            processed_data.append((name, attended, percentage))

    return render_template(
        "monthly_report.html",
        cid=cid,
        data=processed_data,
        month=month,
        total_meeting_time=int(total_meeting_time),
        total_attended_time=int(total_attended_time)
    )


@portal_bp.route("/committee/<int:cid>/yearly-report")
def yearly_report(cid):

    year = request.args.get("year")

    if not year:
        return "Year required", 400

    member = CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session.get("user_id")
    ).first()

    if not member or member.role != "admin":
        return "Access Denied", 403

    # 🔹 Total meetings in that year
    meetings = CommitteeMeeting.query.filter(
        CommitteeMeeting.committee_id == cid,
        db.func.to_char(CommitteeMeeting.meeting_date, 'YYYY') == year
    ).all()

    total_meetings_count = len(meetings)

    # 🔹 Calculate total scheduled meeting minutes
    total_meeting_time = 0

    for m in meetings:
        if m.start_time and m.end_time:
            try:
                start = datetime.strptime(m.start_time, "%H:%M")
                end = datetime.strptime(m.end_time, "%H:%M")
                diff = (end - start).total_seconds() / 60
                total_meeting_time += max(diff, 0)
            except:
                pass

    # 🔹 Total attended minutes per user
    data = db.session.query(
        User.name,
        db.func.coalesce(
            db.func.sum(CommitteeMeetingAttendance.attended_minutes), 0
        )
    ).join(
        CommitteeMeetingAttendance,
        CommitteeMeetingAttendance.user_id == User.id
    ).join(
        CommitteeMeeting,
        CommitteeMeeting.id == CommitteeMeetingAttendance.meeting_id
    ).filter(
        CommitteeMeeting.committee_id == cid,
        db.func.to_char(CommitteeMeeting.meeting_date, 'YYYY') == year
    ).group_by(User.id).all()

    # 🔹 Calculate attendance percentage
    processed_data = []

    for name, attended in data:
        if total_meeting_time > 0:
            percentage = round((attended / total_meeting_time) * 100, 2)
        else:
            percentage = 0

        processed_data.append((name, attended, percentage))

    return render_template(
        "yearly_report.html",
        cid=cid,
        year=year,
        data=processed_data,
        total_meeting_time=int(total_meeting_time),
        total_meetings_count=total_meetings_count
    )


@portal_bp.route("/committee/<int:cid>/attendance-summary")
def committee_attendance_summary(cid):

    member = CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session.get("user_id")
    ).first()

    if not member or member.role != "admin":
        return "Access Denied", 403

    data = db.session.query(
        User.name,
        db.func.coalesce(
            db.func.sum(CommitteeMeetingAttendance.attended_minutes), 0
        )
    ).join(
        CommitteeMeetingAttendance,
        CommitteeMeetingAttendance.user_id == User.id
    ).join(
        CommitteeMeeting,
        CommitteeMeeting.id == CommitteeMeetingAttendance.meeting_id
    ).filter(
        CommitteeMeeting.committee_id == cid
    ).group_by(User.id).all()

    return render_template(
        "attendance_result.html",
        data=data,
        cid=cid
    )


@portal_bp.route("/committee/<int:cid>/members")
def committee_members_page(cid):

    member = CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=session.get("user_id")
    ).first()

    if not member or member.role != "admin":
        return "Access Denied", 403

    members = db.session.query(
        User.id,
        User.name,
        User.phone,
        CommitteeMember.role
    ).join(
        CommitteeMember,
        CommitteeMember.user_id == User.id
    ).filter(
        CommitteeMember.committee_id == cid
    ).order_by(User.name).all()

    return render_template(
        "committee_members.html",
        cid=cid,
        members=members
    )


# ---------------- REMOVE COMMITTEE MEMBER ----------------

@portal_bp.route("/committee/<int:cid>/remove-member/<int:uid>")
def remove_committee_member(cid, uid):
    if not is_admin():
        return "Access Denied", 403

    member = CommitteeMember.query.filter_by(
        committee_id=cid,
        user_id=uid
    ).first()

    if member:
        db.session.delete(member)
        db.session.commit()

    return redirect(url_for("portal.committee_dashboard", cid=cid))


# ---------------- DELETE COMMITTEE ----------------

@portal_bp.route("/committee/<int:cid>/delete")
def delete_committee(cid):
    if not is_super_admin():
        return "Access Denied", 403

    meetings = CommitteeMeeting.query.filter_by(
        committee_id=cid
    ).all()

    for m in meetings:
        CommitteeMeetingAttendance.query.filter_by(
            meeting_id=m.id
        ).delete()

    CommitteeMeeting.query.filter_by(
        committee_id=cid
    ).delete()

    CommitteeMember.query.filter_by(
        committee_id=cid
    ).delete()

    Committee.query.filter_by(
        id=cid
    ).delete()

    db.session.commit()

    return redirect(url_for("portal.dashboard"))




@portal_bp.route("/renew", methods=["GET", "POST"])
def renew():
    if "user_id" not in session:
        return redirect("/")

    if not is_renewal_enabled():
        return "Renewal Disabled", 403

    user = current_user()

    if request.method == "POST":

        screenshot = request.files.get("screenshot")
        amount = int(request.form.get("amount"))

        path = None
        if screenshot:
            os.makedirs("static/renewals", exist_ok=True)
            path = f"static/renewals/{user.id}_{screenshot.filename}"
            screenshot.save(path)

        renewal = Renewal(
            user_id=user.id,
            amount=amount,
            screenshot=path,
            requested_at=date.today()
        )

        db.session.add(renewal)
        db.session.commit()

        return redirect(url_for("portal.dashboard"))

    return render_template("renew.html")


@portal_bp.route("/receipt")
def view_receipt():
    if "user_id" not in session:
        return redirect("/")

    user = current_user()
    print("LOGGED USER ID:", user.id)

    receipt = Receipt.query.filter_by(
        user_id=user.id
    ).order_by(Receipt.id.desc()).first()

    print("FOUND RECEIPT:", receipt)

    if receipt:
        print("Receipt No:", receipt.receipt_no)
        print("Amount:", receipt.amount)
        print("Issued:", receipt.issued_date)

    if not receipt:
        return "No receipt available"

    return render_template("receipt.html", receipt=receipt)


@portal_bp.route("/admin/members")
def admin_members():
    if not is_admin():
        return "Access Denied", 403

    search = request.args.get("search")

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
                User.membership_id.ilike(f"%{search}%"),
                User.nativity.ilike(f"%{search}%")
            )
        )

    members = query.order_by(User.membership_id).all()

    return render_template(
        "admin_members.html",
        members=members,
        view="all",
        is_super_admin=is_super_admin(),
        SUPER_ADMIN_PHONE=SUPER_ADMIN_PHONE
    )

@portal_bp.route("/admin/members/renewed")
def admin_members_renewed():
    if not is_admin():
        return "Access Denied", 403

    members = User.query.filter(
        User.membership_end >= date.today()
    ).order_by(User.membership_id).all()

    return render_template(
        "admin_members.html",
        members=members,
        view="renewed"
    )

@portal_bp.route("/admin/members/pending")
def admin_members_pending():
    if not is_admin():
        return "Access Denied", 403

    members = db.session.query(User).join(
        Renewal
    ).filter(
        Renewal.status == "PENDING"
    ).all()

    return render_template(
        "admin_members.html",
        members=members,
        view="pending"
    )


@portal_bp.route("/admin/members/not-renewed")
def admin_members_not_renewed():
    if not is_admin():
        return "Access Denied", 403

    members = User.query.filter(
        User.membership_end < date.today()
    ).order_by(User.membership_id).all()

    return render_template(
        "admin_members.html",
        members=members,
        view="not_renewed"
    )



@portal_bp.route("/admin/edit-member/<int:user_id>", methods=["GET", "POST"])
def admin_edit_member(user_id):
    if not is_admin():
        return "Access Denied", 403

    member = User.query.get_or_404(user_id)

    if request.method == "POST":
        member.name = request.form["name"]
        member.phone = request.form["phone"]
        member.nativity = request.form["nativity"]
        db.session.commit()
        return redirect(url_for("portal.admin_members"))

    return render_template("admin_edit_member.html", member=member)



@portal_bp.route("/admin/reset-password/<int:user_id>")
def admin_reset_password(user_id):
    if not is_admin():
        return "Access Denied", 403

    member = User.query.get(user_id)

    if member:
        member.password = generate_password_hash(member.phone)
        db.session.commit()

    return redirect(url_for("portal.admin_members"))

@portal_bp.route("/admin/toggle-admin/<int:user_id>")
def toggle_admin(user_id):
    if not is_super_admin():
        return "Access Denied", 403

    member = User.query.get(user_id)

    if member and member.phone != SUPER_ADMIN_PHONE:
        member.is_admin = not member.is_admin
        db.session.commit()

    return redirect(url_for("portal.admin_members"))


@portal_bp.route("/admin/toggle-section-admin/<int:user_id>")
def toggle_section_admin(user_id):
    if not is_super_admin():
        return "Access Denied", 403

    member = User.query.get(user_id)

    if member:
        member.section_admin = not member.section_admin
        db.session.commit()

    return redirect(url_for("portal.admin_members"))



@portal_bp.route("/admin/add-member", methods=["GET", "POST"])
def admin_add_member():
    if not is_admin():
        return "Access Denied", 403

    if request.method == "POST":

        last = User.query.order_by(User.id.desc()).first()
        num = int(last.membership_id[4:]) + 1 if last else 1

        new_user = User(
            name=request.form["name"],
            phone=request.form["phone"],
            nativity=request.form["nativity"],
            membership_id=generate_membership_id(num),
            password=generate_password_hash(request.form["phone"]),
            membership_start=MEMBERSHIP_START,
            membership_end=MEMBERSHIP_END
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("portal.admin_members"))

    return render_template("admin_add_member.html")



@portal_bp.route("/admin/announcements", methods=["GET", "POST"])
def admin_announcements():
    if not is_admin():
        return "Access Denied", 403

    if request.method == "POST":

        img = request.files.get("image")
        path = None

        if img and img.filename:
            os.makedirs("static/announcements", exist_ok=True)
            path = f"static/announcements/{img.filename}"
            img.save(path)

        ann = Announcement(
            title=request.form["title"],
            message=request.form["message"],
            image=path,
            created_at=date.today()
        )

        db.session.add(ann)
        db.session.commit()

        return redirect(url_for("portal.admin_announcements"))

    announcements = Announcement.query.order_by(
        Announcement.id.desc()
    ).all()

    return render_template(
        "admin_announcements.html",
        announcements=announcements
    )



@portal_bp.route("/admin/renewals")
def admin_renewals():
    if not is_admin():
        return "Access Denied", 403

    renewals = Renewal.query.order_by(Renewal.id.desc()).all()

    return render_template(
        "admin_renewals.html",
        renewals=renewals
    )


# ---------------- APPROVE RENEWAL ----------------

@portal_bp.route("/admin/approve-renewal/<int:rid>/<int:uid>")
def approve_renewal(rid, uid):
    if not is_admin():
        return "Access Denied", 403

    renewal = Renewal.query.get(rid)

    if not renewal or renewal.status == "APPROVED":
        return redirect(url_for("portal.admin_renewals"))

    start_date = date.today()
    end_date = date(2027, 3, 31)

    user = User.query.get(uid)
    user.membership_start = start_date
    user.membership_end = end_date

    renewal.status = "APPROVED"

    receipt_no = f"AASC/{start_date.year}/{rid:05d}"

    receipt = Receipt(
        receipt_no=receipt_no,
        user_id=uid,
        amount=renewal.amount,
        issued_date=start_date,
        membership_start=start_date,
        membership_end=end_date
    )

    db.session.add(receipt)
    db.session.commit()

    return redirect(url_for("portal.admin_renewals"))


# ---------------- REJECT RENEWAL ----------------

@portal_bp.route("/admin/reject-renewal/<int:rid>")
def reject_renewal(rid):
    if not is_admin():
        return "Access Denied", 403

    renewal = Renewal.query.get(rid)

    if renewal:
        renewal.status = "REJECTED"
        db.session.commit()

    return redirect(url_for("portal.admin_renewals"))



@portal_bp.route("/admin/receipts")
def admin_receipts():
    if not is_admin():
        return "Access Denied", 403

    receipts = db.session.query(
        Receipt,
        User
    ).join(
        User, Receipt.user_id == User.id
    ).order_by(
        Receipt.issued_date.desc()
    ).all()

    print("Receipts:", receipts)

    return render_template(
        "admin_receipts.html",
        receipts=receipts
    )



@portal_bp.route("/admin/events", methods=["GET", "POST"])
def admin_events():

    if not is_admin():
        return "Access Denied", 403

    if request.method == "POST":

        event = PortalEvent(
            title=request.form["title"],
            description=request.form["description"],
            event_date=request.form["event_date"],
            created_at=datetime.utcnow()
        )

        db.session.add(event)
        db.session.commit()

        return redirect(url_for("portal.admin_events"))

    events = PortalEvent.query.order_by(
        PortalEvent.created_at.desc()
    ).all()

    return render_template(
        "admin_events.html",
        events=events
    )

@portal_bp.route("/admin/events/<int:event_id>/participants")
def event_participants(event_id):

    if not is_admin():
        return "Access Denied", 403

    event = PortalEvent.query.get_or_404(event_id)

    participants = db.session.query(
        User.name,
        User.phone,
        User.membership_id
    ).join(
        PortalEventParticipant,
        PortalEventParticipant.user_id == User.id
    ).filter(
        PortalEventParticipant.portal_event_id == event_id
    ).all()

    return render_template(
        "admin_event_participants.html",
        participants=participants,
        event=event
    )


@portal_bp.route("/admin/analytics")
def admin_analytics():
    if not is_admin():
        return "Access Denied", 403

    total = User.query.count()

    active = User.query.filter(
        User.membership_end >= date.today()
    ).count()

    expired = total - active

    blood_groups = db.session.query(
        User.blood_group,
        db.func.count(User.id)
    ).filter(
        User.blood_group.isnot(None)
    ).group_by(
        User.blood_group
    ).all()

    interests = db.session.query(
        User.interests,
        db.func.count(User.id)
    ).filter(
        User.interests.isnot(None)
    ).group_by(
        User.interests
    ).all()

    return render_template(
        "admin_analytics.html",
        total=total,
        active=active,
        expired=expired,
        blood_groups=blood_groups,
        interests=interests
    )



@portal_bp.route("/admin/blood-donors")
def blood_donors():
    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    bg = request.args.get("bg")
    donors = []

    if bg:
        donors = User.query.filter_by(blood_group=bg).all()

    return render_template(
        "admin_blood_donors.html",
        donors=donors,
        bg=bg
    )

@portal_bp.route("/admin/blood-summary")
def blood_summary():
    if not is_admin():
        return "Access Denied", 403

    data = db.session.query(
        User.blood_group,
        db.func.count(User.id)
    ).filter(
        User.blood_group.isnot(None)
    ).group_by(User.blood_group).all()

    return render_template(
        "blood_summary.html",
        data=data
    )


@portal_bp.route("/admin/medical/dashboard")
def medical_dashboard():
    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    update_overdue_items()

    # =============================
    # GLOBAL METRICS
    # =============================

    total_categories = EquipmentCategory.query.count()
    total_items = EquipmentItem.query.count()

    available = EquipmentItem.query.filter_by(status="AVAILABLE").count()
    issued = EquipmentItem.query.filter_by(status="ISSUED").count()
    overdue = EquipmentMovement.query.filter_by(status="OVERDUE").count()

    # =============================
    # CATEGORY + ITEMS DATA
    # =============================

    categories = EquipmentCategory.query.order_by(
        EquipmentCategory.name
    ).all()

    category_data = []

    for category in categories:

        items = EquipmentItem.query.filter_by(
            category_id=category.id
        ).order_by(EquipmentItem.item_code).all()

        total_cat = len(items)

        available_cat = sum(1 for i in items if i.status == "AVAILABLE")
        issued_cat = sum(1 for i in items if i.status == "ISSUED")

        category_data.append({
            "category": category,
            "items": items,   # ✅ Needed for template
            "total": total_cat,
            "available": available_cat,
            "issued": issued_cat
        })

    # =============================
    # RENDER TEMPLATE
    # =============================

    return render_template(
        "medical_dashboard.html",

        # Global metrics
        total_categories=total_categories,
        total_items=total_items,
        available=available,
        issued=issued,
        overdue=overdue,

        # Category data
        category_data=category_data
    )



@portal_bp.route("/admin/medical/add-category", methods=["GET", "POST"])
def add_category():
    if not is_admin():
        return "Access Denied", 403

    if request.method == "POST":
        category = EquipmentCategory(
            name=request.form["name"],
            prefix=request.form["prefix"],
            description=request.form["description"]
        )

        db.session.add(category)
        db.session.commit()
        return redirect(url_for("portal.medical_dashboard"))
    return render_template("add_category.html")



@portal_bp.route("/admin/medical/add-items/<int:category_id>", methods=["GET", "POST"])
def add_items(category_id):
    if not is_admin():
        return "Access Denied", 403

    category = EquipmentCategory.query.get_or_404(category_id)

    if request.method == "POST":

        quantity = int(request.form["quantity"])

        for _ in range(quantity):

            last_item = EquipmentItem.query.filter_by(
                category_id=category.id
            ).order_by(EquipmentItem.id.desc()).first()

            next_number = 1
            if last_item:
                last_code = last_item.item_code
                next_number = int(last_code.replace(category.prefix, "")) + 1

            new_code = f"{category.prefix}{str(next_number).zfill(3)}"

            item = EquipmentItem(
                category_id=category.id,
                item_code=new_code
            )

            db.session.add(item)

        db.session.commit()
        return redirect(url_for("portal.medical_dashboard"))

    return render_template("add_items.html", category=category)



@portal_bp.route("/admin/medical/issue/<int:item_id>", methods=["POST"])
def issue_item(item_id):

    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    item = db.session.get(EquipmentItem, item_id)

    if not item:
        flash("Item not found.")
        return redirect(url_for("medical_dashboard"))

    # ===============================
    # BUSINESS RULE VALIDATION
    # ===============================

    # 1️⃣ Check condition first
    if item.condition not in ["GOOD", "FAIR"]:
        session("Item cannot be issued due to poor condition.")
        return redirect(url_for("portal.medical_dashboard"))

    # 2️⃣ Check status
    if item.status != "AVAILABLE":
        session("Item is not available for issuing.")
        return redirect(url_for("portal.medical_dashboard"))

    # ===============================
    # CREATE MOVEMENT RECORD
    # ===============================

    try:
        return_date = datetime.strptime(
            request.form["return_date"], "%Y-%m-%d"
        ).date()
    except:
        session("Invalid return date.")
        return redirect(url_for("portal.medical_dashboard"))

    movement = EquipmentMovement(
        item_id=item.id,
        taker_name=request.form["name"],
        taker_phone=request.form["phone"],
        issue_date=date.today(),
        expected_return_date=return_date,
        status="ISSUED"
    )

    # Update equipment status
    item.status = "ISSUED"

    db.session.add(movement)
    db.session.commit()

    session("Equipment issued successfully.")
    return redirect(url_for("portal.medical_dashboard"))



@portal_bp.route("/admin/medical/movements")
def view_movements():
    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    update_overdue_items()

    movements = EquipmentMovement.query.order_by(
        EquipmentMovement.issue_date.desc()
    ).all()

    return render_template("medical_movements.html", movements=movements)



@portal_bp.route("/admin/medical/return/<int:movement_id>")
def return_item(movement_id):
    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    movement = EquipmentMovement.query.get_or_404(movement_id)

    movement.status = "RETURNED"
    movement.actual_return_date = date.today()

    movement.item.status = "AVAILABLE"

    db.session.commit()

    return redirect(url_for("portal.medical_dashboard"))



@portal_bp.route("/admin/medical/update-condition/<int:item_id>", methods=["POST"])
def update_condition(item_id):

    if not (is_admin() or is_section_admin()):
        return "Access Denied", 403

    item = db.session.get(EquipmentItem, item_id)

    new_condition = request.form.get("condition")
    item.condition = new_condition

    # 🔥 CORE BUSINESS LOGIC
    if new_condition in ["DAMAGED", "BROKEN"]:
        item.status = "UNDER_MAINTENANCE"

    elif new_condition in ["GOOD", "FAIR"]:
        # Only make available if not currently issued
        if item.status != "ISSUED":
            item.status = "AVAILABLE"

    db.session.commit()

    return redirect(url_for("portal.medical_dashboard"))



@portal_bp.route("/admin/medical/analytics")
def medical_analytics():
    if not is_admin():
        return "Access Denied", 403

    category_usage = db.session.query(
        EquipmentCategory.name,
        db.func.count(EquipmentMovement.id)
    ).join(
        EquipmentItem,
        EquipmentItem.category_id == EquipmentCategory.id
    ).join(
        EquipmentMovement,
        EquipmentMovement.item_id == EquipmentItem.id
    ).group_by(EquipmentCategory.name).all()

    monthly_usage = db.session.query(
        db.func.to_char(EquipmentMovement.issue_date, 'YYYY-MM'),
        db.func.count(EquipmentMovement.id)
    ).group_by(
        db.func.to_char(EquipmentMovement.issue_date, 'YYYY-MM')
    ).all()

    return render_template(
        "medical_analytics.html",
        category_usage=category_usage,
        monthly_usage=monthly_usage
    )



@portal_bp.route("/admin/dashboard")
def admin_dashboard():
    if not is_super_admin():
        return "Access Denied", 403

    total_committees = Committee.query.count()
    total_members = User.query.count()
    current_year = datetime.now().year

    return render_template(
        "admin_dashboard.html",
        total_committees=total_committees,
        total_members=total_members,
        current_year=current_year
    )


@portal_bp.route("/admin/committees")
def admin_committees():
    if not is_super_admin():
        return "Access Denied", 403

    committees = Committee.query.order_by(Committee.id.desc()).all()

    return render_template(
        "admin_committees.html",
        committees=committees
    )


@portal_bp.route("/admin/create-committee", methods=["GET", "POST"])
def create_committee():
    if not is_super_admin():
        return "Access Denied", 403

    if request.method == "POST":
        committee = Committee(
            name=request.form["name"],
            created_by=session["user_id"]
        )
        db.session.add(committee)
        db.session.flush()

        cm = CommitteeMember(
            committee_id=committee.id,
            user_id=session["user_id"],
            role="admin"
        )
        db.session.add(cm)
        db.session.commit()

        return redirect(url_for("portal.dashboard"))

    return render_template("create_committee.html")




@portal_bp.route("/admin/manage-admins", methods=["GET", "POST"])
def manage_admins():
    if not is_super_admin():
        return "Access Denied", 403

    if request.method == "POST":

        phone = request.form["phone"]
        action = request.form["action"]

        user = User.query.filter_by(phone=phone).first()

        if user:
            if action == "add":
                user.is_admin = True
            elif action == "remove" and user.phone != SUPER_ADMIN_PHONE:
                user.is_admin = False

            db.session.commit()

        return redirect(url_for("portal.manage_admins"))

    admins = User.query.filter_by(is_admin=True).all()
    members = User.query.filter_by(is_admin=False).all()

    return render_template(
        "admin_manage_admins.html",
        admins=admins,
        members=members
    )



@portal_bp.route("/admin/renewal-toggle", methods=["POST"])
def toggle_renewal():
    if not is_admin():
        return "Access Denied", 403

    setting = Setting.query.filter_by(
        key="renewal_enabled"
    ).first()

    if setting:
        setting.value = request.form["value"]
        db.session.commit()

    return redirect(url_for("portal.dashboard"))


    # Ensure super admin exists
    admin = User.query.filter_by(phone=SUPER_ADMIN_PHONE).first()

    if not admin:
        super_admin = User(
            name="Super Admin",
            phone=SUPER_ADMIN_PHONE,
            nativity="Admin",
            membership_id="AASC001",
            password=generate_password_hash(SUPER_ADMIN_PHONE),
            membership_start=MEMBERSHIP_START,
            membership_end=MEMBERSHIP_END,
            is_admin=True
        )

        db.session.add(super_admin)
        db.session.commit()

    # Import Excel
    if User.query.count() <= 1:
     import_members_from_excel()

