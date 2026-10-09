from odoo import models, fields, api
from odoo.exceptions import UserError


class HostelMaintenanceRequest(models.Model):
    _name = "hostel.maintenance.request"
    _description = "Hostel Maintenance Request"
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
    request_type = fields.Selection(
        [
            ("plumbing", "Plumbing"),
            ("electrical", "Electrical"),
            ("cleaning", "Cleaning"),
            ("carpentry", "Carpentry"),
            ("painting", "Painting"),
            ("hvac", "HVAC / AC"),
            ("pest_control", "Pest Control"),
            ("other", "Other"),
        ],
        string="Request Type",
        required=True,
        default="other",
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
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Description",
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
    bed_id = fields.Many2one(
        "hostel.bed",
        string="Bed",
        ondelete="set null",
        tracking=True,
    )
    requested_by_id = fields.Many2one(
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    assigned_to_id = fields.Many2one(
        "hr.employee",
        string="Assigned To",
        ondelete="set null",
        tracking=True,
    )
    cost = fields.Monetary(
        string="Cost",
        currency_field="currency_id",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        tracking=True,
    )
    notes = fields.Text(string="Internal Notes")

    @api.model_create_multi
    def create(self, vals_list):
        """Apply sequence and default priority from settings."""
        ICP = self.env["ir.config_parameter"].sudo()
        default_prio = (
            ICP.get_str("sirita_mahad.maintenance_default_priority", "medium")
            or "medium"
        )
        for vals in vals_list:
            if not vals.get("priority"):
                if default_prio in ("low", "medium", "high", "urgent"):
                    vals["priority"] = default_prio

            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hostel.maintenance.request")
                    or "/"
                )
        records = super().create(vals_list)
        for rec in records:
            rec._auto_assign_if_enabled(on_create=True)
        return records

    # ------------------------------------------------------------------
    # Settings-driven helpers
    # ------------------------------------------------------------------

    def _auto_assign_if_enabled(self, on_create=False):
        """Auto-assign maintenance requests based on settings."""
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = (
            ICP.get_str("sirita_mahad.maintenance_auto_assign", "False")
            != "False"
        )
        if not enabled:
            return
        for rec in self:
            if rec.assigned_to_id:
                continue
            # Simple strategy: first active employee in current company
            employee = (
                self.env["hr.employee"]
                .search([("company_id", "=", rec.env.company.id)], limit=1)
            )
            if not employee:
                continue
            rec.assigned_to_id = employee
            # If submitting or just created, move to assigned state directly
            if rec.state in ("draft", "submitted") or (on_create and rec.state == "draft"):
                rec.state = "assigned"

    def _notify_requester(self, message):
        """Notify requester via chatter when setting is enabled."""
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = (
            ICP.get_str("sirita_mahad.maintenance_notify_requester", "False")
            != "False"
        )
        if not enabled:
            return
        for rec in self:
            if rec.requested_by_id:
                try:
                    rec.requested_by_id.partner_id.message_post(body=message)
                except Exception:
                    # Fallback: log on the request itself
                    rec.message_post(body=message)

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Only draft requests can be submitted.")
            rec.state = "submitted"
            rec._auto_assign_if_enabled()
            rec._notify_requester("Your maintenance request %s has been submitted." % rec.name)

    def action_assign(self):
        for rec in self:
            if rec.state not in ("submitted", "assigned"):
                raise UserError(
                    "Only submitted or assigned requests can be (re)assigned."
                )
            rec.state = "assigned"
            rec._auto_assign_if_enabled()
            rec._notify_requester("Your maintenance request %s has been assigned." % rec.name)

    def action_start(self):
        for rec in self:
            if rec.state not in ("submitted", "assigned"):
                raise UserError(
                    "Only submitted or assigned requests can be started."
                )
            rec.state = "in_progress"
            rec._notify_requester("Work has started on maintenance request %s." % rec.name)

    def action_complete(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError("Only in-progress requests can be completed.")
            rec.state = "completed"
            rec.completed_date = fields.Datetime.now()
            rec._notify_requester("Maintenance request %s has been completed." % rec.name)

    def action_cancel(self):
        for rec in self:
            if rec.state in ("completed", "cancelled"):
                raise UserError(
                    "Completed or already cancelled requests cannot be cancelled."
                )
            rec.state = "cancelled"
            rec._notify_requester("Maintenance request %s has been cancelled." % rec.name)

    def action_reset_draft(self):
        for rec in self:
            rec.state = "draft"
            rec.completed_date = False
