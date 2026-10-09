from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HostelCheckIn(models.Model):
    _name = "hostel.checkin"
    _description = "Check-In / Check-Out"

    contract_id = fields.Many2one(
        'hostel.contract',
        required=True
    )

    student_id = fields.Many2one(
        related='contract_id.student_id',
        store=True
    )

    bed_id = fields.Many2one(
        related='contract_id.bed_id',
        store=True
    )

    room_id = fields.Many2one(
        related='contract_id.room_id',
        store=True,
        string="Room"
    )

    building_id = fields.Many2one(
        related='contract_id.building_id',
        store=True,
        string="Building"
    )

    checkin_datetime = fields.Datetime()
    checkout_datetime = fields.Datetime()

    inventory_notes = fields.Text()
    damage_notes = fields.Text()

    checkin_signature = fields.Binary()
    checkout_signature = fields.Binary()

    photo_ids = fields.Many2many(
        'ir.attachment',
        string="Inspection Photos"
    )

    penalty_ids = fields.One2many(
        'hostel.checkin.penalty',
        'checkin_id',
        string="Penalties"
    )

    total_penalty_amount = fields.Monetary(
        compute='_compute_total_penalty',
        store=True,
        string="Total Penalty Amount"
    )

    invoice_id = fields.Many2one(
        'account.move',
        string="Penalty Invoice"
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='contract_id.currency_id'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out')
    ], default='draft')

    @api.depends('penalty_ids.amount')
    def _compute_total_penalty(self):
        for rec in self:
            rec.total_penalty_amount = sum(rec.penalty_ids.mapped('amount'))

    def action_checkin(self):
        """Perform check-in and optionally enforce mandatory student documents."""
        ICP = self.env["ir.config_parameter"].sudo()
        require_docs = (
            ICP.get_str("sirita_mahad.require_documents_on_checkin", "False")
            != "False"
        )

        for rec in self:
            if require_docs:
                # Require at least one non-expired ID/passport/visa document
                student = rec.student_id
                if not student:
                    raise ValidationError(
                        "Cannot check in without a linked student on the contract."
                    )
                docs = student.student_document_ids.filtered(
                    lambda d: d.document_type in ("id_card", "passport", "visa")
                )
                if not docs:
                    raise ValidationError(
                        "Check-in blocked: no ID/Passport/Visa documents are uploaded "
                        "for student %s." % (student.display_name,)
                    )
                # Treat documents with no expiry date as invalid for this rule
                valid_docs = docs.filtered(
                    lambda d: d.expiry_date and not d.is_expired
                )
                if not valid_docs:
                    raise ValidationError(
                        "Check-in blocked: all key documents for student %s are "
                        "missing expiry dates or already expired."
                        % (student.display_name,)
                    )

            rec.checkin_datetime = fields.Datetime.now()
            rec.state = "checked_in"
            rec.contract_id.state = "active"

            self.env["hostel.occupancy.history"].create(
                {
                    "student_id": rec.student_id.id,
                    "bed_id": rec.bed_id.id,
                    "contract_id": rec.contract_id.id,
                    "check_in": rec.checkin_datetime,
                }
            )

    def action_checkout(self):
        for rec in self:
            rec.checkout_datetime = fields.Datetime.now()
            rec.state = 'checked_out'
            rec.contract_id.state = 'closed'

            history = self.env['hostel.occupancy.history'].search([
                ('contract_id', '=', rec.contract_id.id)
            ], limit=1)
            if history:
                history.check_out = rec.checkout_datetime

            if rec.penalty_ids and rec.total_penalty_amount > 0:
                rec._create_penalty_invoice()

    def _create_penalty_invoice(self):
        """Create invoice for penalties."""
        self.ensure_one()
        if not self.student_id:
            raise UserError("Student is required to create penalty invoice.")

        account = self.env['account.account'].search([
            ('company_id', '=', self.env.company.id),
            ('account_type', '=', 'income'),
        ], limit=1)
        if not account:
            account = self.env['account.account'].search([
                ('company_id', '=', self.env.company.id),
                ('account_type', 'in', ['income', 'income_other']),
            ], limit=1)

        invoice_lines = []
        for penalty in self.penalty_ids:
            invoice_lines.append((0, 0, {
                'name': penalty.description or penalty.penalty_type_id.name,
                'quantity': 1,
                'price_unit': penalty.amount,
                'account_id': account.id if account else False,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.student_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'ref': 'Check-out Penalties - %s' % (self.bed_id.name or ''),
        })
        self.invoice_id = invoice.id
        return invoice


class HostelCheckInPenalty(models.Model):
    _name = 'hostel.checkin.penalty'
    _description = 'Check-In/Check-Out Penalty'

    checkin_id = fields.Many2one(
        'hostel.checkin',
        required=True,
        ondelete='cascade'
    )

    penalty_type_id = fields.Many2one(
        'hostel.penalty.type',
        string="Penalty Type"
    )

    description = fields.Text(
        required=True,
        string="Description/Justification"
    )

    amount = fields.Monetary(
        required=True,
        string="Penalty Amount"
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='checkin_id.currency_id'
    )

    penalty_category = fields.Selection([
        ('damage', 'Damage Charges'),
        ('violation', 'Violation Fees'),
        ('other', 'Other')
    ], default='damage', required=True)


class HostelPenaltyType(models.Model):
    _name = 'hostel.penalty.type'
    _description = 'Penalty Type'

    name = fields.Char(required=True)
    default_amount = fields.Monetary()
    penalty_category = fields.Selection([
        ('damage', 'Damage Charges'),
        ('violation', 'Violation Fees'),
        ('other', 'Other')
    ], default='damage')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    active = fields.Boolean(default=True)
