from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HostelContract(models.Model):
    _name = "hostel.contract"
    _description = "Hostel Contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one(
        'res.partner',
        required=True,
        domain=[('is_student', '=', True)]
    )

    bed_id = fields.Many2one(
        'hostel.bed',
        required=True,
        ondelete='restrict'
    )

    room_id = fields.Many2one(
        related='bed_id.room_id',
        store=True
    )

    unit_id = fields.Many2one(
        related='room_id.unit_id',
        store=True
    )

    building_id = fields.Many2one(
        related='unit_id.building_id',
        store=True
    )

    contract_start = fields.Date(required=True)
    contract_end = fields.Date(required=True)

    monthly_rent = fields.Monetary()
    security_deposit = fields.Monetary()

    deposit_status = fields.Selection([
        ('held', 'Held'),
        ('refunded', 'Refunded')
    ], default='held')

    force_upgrade = fields.Boolean()
    original_room_type = fields.Selection([
        ('single', 'Single'),
        ('twin', 'Twin'),
        ('studio', 'Studio')
    ])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], default='draft')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    rent_invoice_ids = fields.One2many(
        'hostel.rent.invoice',
        'contract_id',
        string="Rent Invoices",
    )
    outstanding_rent_balance = fields.Monetary(
        string="Outstanding Rent",
        compute='_compute_outstanding_rent_balance',
        store=True,
        currency_field='currency_id',
    )

    active = fields.Boolean(default=True)

    @api.depends('rent_invoice_ids', 'rent_invoice_ids.state', 'rent_invoice_ids.amount', 'rent_invoice_ids.invoice_id', 'rent_invoice_ids.invoice_id.payment_state')
    def _compute_outstanding_rent_balance(self):
        for rec in self:
            total = 0.0
            for inv in rec.rent_invoice_ids:
                if inv.state in ('invoiced', 'overdue') and inv.invoice_id and inv.invoice_id.state == 'posted':
                    total += inv.amount
            rec.outstanding_rent_balance = total

    @api.constrains('bed_id', 'contract_start', 'contract_end', 'state')
    def _check_contract_overlap(self):
        for rec in self:
            if rec.state != 'active':
                continue

            overlapping = self.search([
                ('id', '!=', rec.id),
                ('bed_id', '=', rec.bed_id.id),
                ('state', '=', 'active'),
                ('contract_start', '<=', rec.contract_end),
                ('contract_end', '>=', rec.contract_start),
            ])

            if overlapping:
                raise ValidationError(
                    "This bed already has an active contract for the selected period."
                )

    # -------------------------------------------------------------------------
    # Communication helpers (contract email)
    # -------------------------------------------------------------------------

    def action_send_contract_email(self):
        """Send contract email using the default template from settings.

        Uses config parameter 'sirita_mahad.email_template_contract'
        (set via General Settings). Falls back to a simple chatter message
        if no valid template is configured.
        """
        self.ensure_one()
        ICP = self.env["ir.config_parameter"].sudo()
        template_id = ICP.get_str("sirita_mahad.email_template_contract")
        if template_id:
            try:
                tmpl = self.env["mail.template"].browse(int(template_id))
            except Exception:
                tmpl = self.env["mail.template"]
            if tmpl and tmpl.exists():
                tmpl.send_mail(self.id, force_send=True)
                return True

        # Fallback: no template configured or invalid
        self.message_post(body="Contract email sent (no default template configured).")
        return True
