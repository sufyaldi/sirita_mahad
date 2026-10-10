from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date


class HostelAnnouncementCategory(models.Model):
    _name = "hostel.announcement.category"
    _description = "Announcement Category"
    _order = "sequence, name"

    name = fields.Char(string="Category", required=True)
    sequence = fields.Integer(string="Sequence", default=10)


class HostelAnnouncement(models.Model):
    _name = "hostel.announcement"
    _description = "Notice Board / Announcement"
    _order = "priority desc, date_start desc, create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
    )
    reference = fields.Char(
        string="Reference",
        required=True,
        default="/",
        copy=False,
        readonly=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        "hostel.announcement.category",
        string="Category",
        ondelete="set null",
        tracking=True,
    )
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        required=True,
        tracking=True,
    )
    content = fields.Html(
        string="Content",
        required=True,
    )
    target_type = fields.Selection(
        [
            ("all", "All Students"),
            ("building", "Specific Building(s)"),
        ],
        string="Target",
        default="all",
        required=True,
        tracking=True,
    )
    building_ids = fields.Many2many(
        "hostel.building",
        "hostel_announcement_building_rel",
        "announcement_id",
        "building_id",
        string="Buildings",
        help="Leave empty when target is All. Used when target is Specific Building(s).",
    )
    date_start = fields.Date(
        string="Start Date",
        default=fields.Date.context_today,
        tracking=True,
        help="Date from which the announcement is visible.",
    )
    date_end = fields.Date(
        string="Expiry Date",
        tracking=True,
        help="Date after which the announcement expires. Leave empty for no expiry.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("expired", "Expired"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    published_date = fields.Datetime(string="Published On", readonly=True)
    published_by = fields.Many2one("res.users", string="Published By", readonly=True)
    created_by = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    is_active = fields.Boolean(
        string="Currently Active",
        compute="_compute_is_active",
        store=True,
        help="True when published, within date range, and not expired.",
    )

    @api.depends("state", "date_start", "date_end")
    def _compute_is_active(self):
        today = date.today()
        for rec in self:
            if rec.state != "published":
                rec.is_active = False
                continue
            if rec.date_start and rec.date_start > today:
                rec.is_active = False
                continue
            if rec.date_end and rec.date_end < today:
                rec.is_active = False
                continue
            rec.is_active = True
    
    # -------------------------------------------------------------------------
    # Helpers reading configuration
    # -------------------------------------------------------------------------

    def _get_default_target_type(self):
        """Return default target type from settings."""
        ICP = self.env["ir.config_parameter"].sudo()
        target = ICP.get_str(
            "sirita_mahad.announcement_default_target", "all"
        ) or "all"
        if target not in ("all", "building"):
            target = "all"
        return target

    def _is_email_broadcast_enabled(self):
        """Return whether email broadcast is enabled for announcements."""
        ICP = self.env["ir.config_parameter"].sudo()
        return (
            ICP.get_str(
                "sirita_mahad.announcement_email_broadcast", "False"
            )
            != "False"
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "/") == "/":
                vals["reference"] = (
                    self.env["ir.sequence"].next_by_code("hostel.announcement") or "/"
                )
            if not vals.get("target_type"):
                vals["target_type"] = self._get_default_target_type()

        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default["reference"] = "/"
        default["state"] = "draft"
        default["published_date"] = False
        default["published_by"] = False
        return super().copy(default)

    def action_publish(self):
        draft = self.filtered(lambda r: r.state == "draft")
        if len(self) != len(draft):
            raise UserError("Only draft announcements can be published.")
        draft.write(
            {
                "state": "published",
                "published_date": fields.Datetime.now(),
                "published_by": self.env.user.id,
            }
        )
        # Optionally broadcast via email based on settings
        if self._is_email_broadcast_enabled():
            self._broadcast_via_email()

    def action_archive(self):
        self.write({"state": "archived"})

    def action_expire(self):
        self.write({"state": "expired"})

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("published", "expired", "archived"):
                raise UserError("Only published, expired, or archived announcements can be reset.")
        self.write({
            "state": "draft",
            "published_date": False,
            "published_by": False,
        })

    # -------------------------------------------------------------------------
    # Communication helpers
    # -------------------------------------------------------------------------

    def _broadcast_via_email(self):
        """Post a message to related students when email broadcast is enabled.

        For now this simply logs a message in the chatter; integration with
        mass mailing / specific student followers can be added later.
        """
        for rec in self:
            rec.message_post(
                body="Announcement published and email broadcast is enabled in settings."
            )

    @api.model
    def _cron_expire_announcements(self):
        """Mark announcements as expired when date_end is past."""
        today = date.today()
        expired = self.search([
            ("state", "=", "published"),
            ("date_end", "!=", False),
            ("date_end", "<", today),
        ])
        if expired:
            expired.write({"state": "expired"})
