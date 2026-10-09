from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HostelComplaint(models.Model):
    _name = "hostel.complaint"
    _description = "Hostel Complaint & Grievance"
    _order = "priority desc, create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Reference",
        required=True,
        default="/",
        copy=False,
        readonly=True,
        tracking=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        string="Complainant (Student)",
        required=True,
        domain=[("is_student", "=", True)],
        tracking=True,
    )
    category = fields.Selection(
        [
            ("noise", "Noise / Disturbance"),
            ("cleanliness", "Cleanliness / Hygiene"),
            ("facilities", "Facilities / Amenities"),
            ("staff_behavior", "Staff Behavior"),
            ("safety", "Safety / Security"),
            ("room_issue", "Room / Bed Issue"),
            ("other", "Other"),
        ],
        string="Category",
        required=True,
        default="other",
        tracking=True,
    )
    subject = fields.Char(
        string="Subject",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Description",
        required=True,
        tracking=True,
    )
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="medium",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
            ("escalated", "Escalated"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    building_id = fields.Many2one(
        "hostel.building",
        string="Building",
        ondelete="set null",
        tracking=True,
    )
    room_id = fields.Many2one(
        "hostel.room",
        string="Room",
        ondelete="set null",
        tracking=True,
    )
    assigned_to_id = fields.Many2one(
        "hr.employee",
        string="Assigned To",
        ondelete="set null",
        tracking=True,
    )
    resolution_notes = fields.Text(
        string="Resolution Notes",
        tracking=True,
    )
    resolved_date = fields.Datetime(
        string="Resolved Date",
        readonly=True,
        tracking=True,
    )
    resolved_by_id = fields.Many2one(
        "res.users",
        string="Resolved By",
        readonly=True,
        tracking=True,
    )
    escalation_notes = fields.Text(
        string="Escalation Notes",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Settings-driven helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_settings(self):
        ICP = self.env["ir.config_parameter"].sudo()
        allow_anonymous = (
            ICP.get_str("sirita_mahad.complaint_allow_anonymous", "False")
            != "False"
        )
        escalation_days_str = ICP.get_str(
            "sirita_mahad.complaint_escalation_days", "0"
        ) or "0"
        try:
            escalation_days = int(escalation_days_str)
        except ValueError:
            escalation_days = 0
        notify_student = (
            ICP.get_str("sirita_mahad.complaint_notify_student", "False")
            != "False"
        )
        notify_manager = (
            ICP.get_str("sirita_mahad.complaint_notify_manager", "False")
            != "False"
        )
        return {
            "allow_anonymous": allow_anonymous,
            "escalation_days": escalation_days,
            "notify_student": notify_student,
            "notify_manager": notify_manager,
        }

    @api.constrains("student_id")
    def _check_student_required_unless_allowed(self):
        """Enforce student requirement based on settings."""
        settings = self._get_settings()
        if settings["allow_anonymous"]:
            return
        for rec in self:
            if not rec.student_id:
                raise ValidationError(
                    "Complainant (Student) is required. Anonymous complaints are disabled in settings."
                )

    @api.model_create_multi
    def create(self, vals_list):
        settings = self._get_settings()
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hostel.complaint") or "/"
                )
            if not settings["allow_anonymous"] and not vals.get("student_id"):
                raise ValidationError(
                    "Complainant (Student) is required. Anonymous complaints are disabled in settings."
                )
        return super().create(vals_list)

    def _notify_parties(self, message):
        """Notify student and/or manager based on settings."""
        settings = self._get_settings()
        for rec in self:
            # notify student
            if settings["notify_student"] and rec.student_id:
                try:
                    rec.student_id.message_post(body=message)
                except Exception:
                    rec.message_post(body=message)
            # notify manager: simple implementation → log on complaint itself
            if settings["notify_manager"]:
                rec.message_post(body="[Manager Notification] %s" % message)

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Only draft complaints can be submitted.")
            rec.state = "submitted"
            rec._notify_parties("Complaint %s has been submitted." % rec.name)

    def action_assign_review(self):
        for rec in self:
            if rec.state not in ("submitted", "under_review"):
                raise UserError(
                    "Only submitted or under-review complaints can be (re)assigned."
                )
            rec.state = "under_review"
            rec._notify_parties("Complaint %s is now under review." % rec.name)

    def action_resolve(self):
        for rec in self:
            if rec.state != "under_review":
                raise UserError(
                    "Only complaints under review can be marked as resolved."
                )
            rec.state = "resolved"
            rec.resolved_date = fields.Datetime.now()
            rec.resolved_by_id = self.env.user.id
            rec._notify_parties("Complaint %s has been resolved." % rec.name)

    def action_close(self):
        for rec in self:
            if rec.state not in ("resolved", "submitted", "under_review"):
                raise UserError(
                    "Only resolved, submitted, or under-review complaints can be closed."
                )
            if not rec.resolved_date:
                rec.resolved_date = fields.Datetime.now()
                rec.resolved_by_id = self.env.user.id
            rec.state = "closed"
            rec._notify_parties("Complaint %s has been closed." % rec.name)

    def action_escalate(self):
        for rec in self:
            if rec.state in ("resolved", "closed", "cancelled"):
                raise UserError(
                    "Resolved, closed, or cancelled complaints cannot be escalated."
                )
            rec.state = "escalated"
            rec._notify_parties("Complaint %s has been escalated." % rec.name)

    def action_cancel(self):
        for rec in self:
            if rec.state in ("resolved", "closed"):
                raise UserError(
                    "Resolved or closed complaints cannot be cancelled."
                )
            rec.state = "cancelled"
            rec._notify_parties("Complaint %s has been cancelled." % rec.name)

    def action_reset_draft(self):
        for rec in self:
            if rec.state != "cancelled":
                raise UserError("Only cancelled complaints can be reset to draft.")
            rec.state = "draft"
            rec.resolved_date = False
            rec.resolved_by_id = False
