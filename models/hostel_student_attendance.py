from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HostelStudentAttendance(models.Model):
    _name = "hostel.student.attendance"
    _description = "Hostel Student Attendance"
    _order = "date desc, checkin_datetime desc"

    student_id = fields.Many2one(
        "res.partner",
        string="Student",
        required=True,
        domain=[("is_student", "=", True)],
        ondelete="cascade",
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today,
    )
    checkin_datetime = fields.Datetime(string="Check-In Time")
    checkout_datetime = fields.Datetime(string="Check-Out Time")
    status = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late Entry"),
            ("early_departure", "Early Departure"),
        ],
        string="Status",
        default="present",
        compute="_compute_status",
        store=True,
        readonly=False,
    )
    building_id = fields.Many2one(
        "hostel.building",
        string="Building / Entry Point",
        ondelete="set null",
    )
    remarks = fields.Text(string="Remarks")
    verified_by_id = fields.Many2one(
        "hr.employee",
        string="Verified By",
        ondelete="set null",
    )

    @api.depends("checkin_datetime", "checkout_datetime")
    def _compute_status(self):
        ICP = self.env["ir.config_parameter"].sudo()
        source = ICP.get_str("sirita_mahad.attendance_source", "manual") or "manual"
        late_grace_str = ICP.get_str("sirita_mahad.attendance_late_grace", "0") or "0"
        try:
            late_grace = int(late_grace_str)
        except ValueError:
            late_grace = 0

        for rec in self:
            # Manual -> admin decides status, do not override
            if source == "manual":
                continue

            if not rec.checkin_datetime and not rec.checkout_datetime:
                rec.status = "absent"
                continue

            # Default present when any time is set
            new_status = "present"

            # If we use check-in source and late_grace > 0, compute late based on a simple 09:00 baseline
            if source in ("checkin", "mixed") and late_grace and rec.checkin_datetime and rec.date:
                try:
                    # Build a naive datetime at 09:00 local for the attendance date
                    base_dt = fields.Datetime.to_datetime(f"{rec.date} 09:00:00")
                    delta = rec.checkin_datetime - base_dt
                    minutes = delta.total_seconds() / 60.0
                    if minutes > late_grace:
                        new_status = "late"
                except Exception:
                    # Fallback to present if any parsing fails
                    new_status = "present"

            # Only override when previous status was absent or empty
            if not rec.status or rec.status == "absent":
                rec.status = new_status

    @api.constrains("checkin_datetime", "checkout_datetime")
    def _check_checkout_after_checkin(self):
        for rec in self:
            if rec.checkin_datetime and rec.checkout_datetime:
                if rec.checkout_datetime < rec.checkin_datetime:
                    raise ValidationError(
                        "Check-out time cannot be before check-in time."
                    )

    @api.constrains("student_id", "date")
    def _check_unique_attendance_per_day(self):
        for rec in self:
            if not rec.student_id or not rec.date:
                continue
            existing = self.search(
                [
                    ("student_id", "=", rec.student_id.id),
                    ("date", "=", rec.date),
                    ("id", "!=", rec.id),
                ],
                limit=1,
            )
            if existing:
                raise ValidationError(
                    "Attendance for %s on %s already exists."
                    % (rec.student_id.name, rec.date)
                )

    # ---------------------------------------------------------------------
    # Notifications based on settings
    # ---------------------------------------------------------------------

    def _notify_guardian_absent(self):
        """Post a simple message on student when absent, if enabled."""
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = ICP.get_str(
            "sirita_mahad.attendance_absent_notify_guardian", "False"
        ) != "False"
        if not enabled:
            return
        for rec in self:
            if rec.status == "absent" and rec.student_id:
                body = (
                    "Hostel attendance: student marked as ABSENT on %s."
                    % (rec.date or "")
                )
                try:
                    rec.student_id.message_post(body=body)
                except Exception:
                    # If partner doesn't support chatter, ignore silently
                    continue

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._notify_guardian_absent()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._notify_guardian_absent()
        return res

    @api.depends('student_id', 'date', 'status')
    def _compute_display_name(self):
        for rec in self:
            label = "%s - %s" % (
                rec.student_id.name or "",
                rec.date.strftime("%Y-%m-%d") if rec.date else "",
            )
            if rec.status:
                status_label = dict(rec._fields["status"].selection).get(
                    rec.status, rec.status
                )
                label += " [%s]" % status_label
            rec.display_name = label
