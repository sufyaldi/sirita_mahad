from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta


class HostelRoomInspection(models.Model):
    _name = "hostel.room.inspection"
    _description = "Hostel Room Inspection"
    _order = "inspection_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        default="/",
        copy=False,
        readonly=True,
    )
    inspection_date = fields.Date(
        string="Inspection Date",
        required=True,
        default=fields.Date.context_today,
    )
    scheduled_date = fields.Date(string="Scheduled Date")
    building_id = fields.Many2one(
        "hostel.building",
        string="Building",
        ondelete="set null",
    )
    room_id = fields.Many2one(
        "hostel.room",
        string="Room",
        ondelete="set null",
        help="Leave empty for building-wide inspection",
    )
    inspected_by_id = fields.Many2one(
        "hr.employee",
        string="Inspected By",
        ondelete="set null",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
    )
    checklist_note = fields.Text(string="Checklist Notes")
    findings = fields.Text(string="Findings / Remarks")
    line_ids = fields.One2many(
        "hostel.room.inspection.line",
        "inspection_id",
        string="Checklist",
        copy=True,
    )

    # ---------------------------------------------------------------------
    # Helpers reading configuration
    # ---------------------------------------------------------------------

    def _get_default_frequency_days(self):
        """Return configured default inspection frequency (days)."""
        ICP = self.env["ir.config_parameter"].sudo()
        days_str = ICP.get_str(
            "sirita_mahad.inspection_default_frequency", "0"
        ) or "0"
        try:
            return int(days_str)
        except ValueError:
            return 0

    def _is_auto_schedule_enabled(self):
        """Return whether auto-scheduling of inspections is enabled."""
        ICP = self.env["ir.config_parameter"].sudo()
        return (
            ICP.get_str("sirita_mahad.inspection_auto_schedule", "False")
            != "False"
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hostel.room.inspection")
                    or "/"
                )
            if not vals.get("inspection_date") and vals.get("scheduled_date"):
                freq_days = self._get_default_frequency_days()
                if freq_days > 0 and self._is_auto_schedule_enabled():
                    try:
                        scheduled = fields.Date.from_string(vals["scheduled_date"])
                    except Exception:
                        scheduled = None
                    if scheduled:
                        vals["inspection_date"] = scheduled

        return super().create(vals_list)

    def action_schedule(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Only draft inspections can be scheduled.")
            rec.state = "scheduled"
            if not rec.scheduled_date:
                rec.scheduled_date = rec.inspection_date

    def action_start(self):
        for rec in self:
            if rec.state not in ("draft", "scheduled"):
                raise UserError(
                    "Only draft or scheduled inspections can be started."
                )
            rec.state = "in_progress"

    def action_complete(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(
                    "Only in-progress inspections can be completed."
                )
            rec.state = "completed"

    def action_cancel(self):
        for rec in self:
            if rec.state == "completed":
                raise UserError("Completed inspections cannot be cancelled.")
            rec.state = "cancelled"

    def action_reset_draft(self):
        for rec in self:
            if rec.state != "cancelled":
                raise UserError(
                    "Only cancelled inspections can be reset to draft."
                )
            rec.state = "draft"

    # ---------------------------------------------------------------------
    # Cron helper for auto-scheduling based on settings
    # ---------------------------------------------------------------------

    @api.model
    def _cron_auto_schedule_inspections(self):
        """Placeholder for future: create upcoming inspections when enabled."""
        if not self._is_auto_schedule_enabled():
            return
        freq_days = self._get_default_frequency_days()
        if freq_days <= 0:
            return
        # Future enhancement: generate inspections per building/room here.
        return


class HostelRoomInspectionLine(models.Model):
    _name = "hostel.room.inspection.line"
    _description = "Room Inspection Checklist Line"

    inspection_id = fields.Many2one(
        "hostel.room.inspection",
        string="Inspection",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Check Item", required=True)
    result = fields.Selection(
        [
            ("ok", "OK"),
            ("not_ok", "Not OK"),
            ("na", "N/A"),
        ],
        string="Result",
        default="ok",
    )
    remarks = fields.Char(string="Remarks")
