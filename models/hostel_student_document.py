from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    student_document_ids = fields.One2many(
        "hostel.student.document",
        "student_id",
        string="Student Documents",
    )
    document_expiring_count = fields.Integer(
        string="Documents Expiring Soon",
        compute="_compute_document_expiring_count",
    )
    document_expired_count = fields.Integer(
        string="Expired Documents",
        compute="_compute_document_expiring_count",
    )

    @api.depends("student_document_ids", "student_document_ids.expiry_date")
    def _compute_document_expiring_count(self):
        today = fields.Date.today()
        for rec in self:
            docs = rec.student_document_ids or self.env["hostel.student.document"]
            rec.document_expiring_count = len(
                docs.filtered(
                    lambda d: d.expiry_date
                    and 0 <= (d.expiry_date - today).days <= 30
                )
            )
            rec.document_expired_count = len(
                docs.filtered(
                    lambda d: d.expiry_date and (d.expiry_date - today).days < 0
                )
            )


class HostelStudentDocument(models.Model):
    _name = "hostel.student.document"
    _description = "Student Document"
    _order = "expiry_date asc nulls last, create_date desc"

    student_id = fields.Many2one(
        "res.partner",
        string="Student",
        required=True,
        ondelete="cascade",
        domain=[("is_student", "=", True)],
    )
    name = fields.Char(string="Document Name", required=True)
    document_type = fields.Selection(
        [
            ("id_card", "ID Card"),
            ("passport", "Passport"),
            ("visa", "Visa"),
            ("photo", "Photo"),
            ("certificate", "Certificate"),
            ("other", "Other"),
        ],
        string="Document Type",
        required=True,
        default="other",
    )
    document_number = fields.Char(string="Document Number")
    issue_date = fields.Date(string="Issue Date")
    expiry_date = fields.Date(string="Expiry Date")
    document_file = fields.Binary(string="Document File", attachment=True)
    filename = fields.Char(string="Filename")
    notes = fields.Text(string="Notes")

    days_to_expiry = fields.Integer(
        string="Days to Expiry",
        compute="_compute_expiry_status",
        store=True,
    )
    is_expired = fields.Boolean(
        string="Expired",
        compute="_compute_expiry_status",
        store=True,
    )
    is_expiring_soon = fields.Boolean(
        string="Expiring Soon",
        compute="_compute_expiry_status",
        store=True,
    )

    @api.depends("expiry_date")
    def _compute_expiry_status(self):
        today = fields.Date.today()
        ICP = self.env["ir.config_parameter"].sudo()
        warning_days = int(ICP.get_str("sirita_mahad.document_expiry_warning_days", "30") or 30)
        for rec in self:
            if rec.expiry_date:
                days = (rec.expiry_date - today).days
                rec.days_to_expiry = days
                rec.is_expired = days < 0
                rec.is_expiring_soon = 0 <= days <= warning_days
            else:
                rec.days_to_expiry = 0
                rec.is_expired = False
                rec.is_expiring_soon = False
