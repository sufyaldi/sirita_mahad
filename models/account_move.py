from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_category = fields.Selection([
        ('rent', 'Rent'),
        ('security_deposit', 'Security Deposit'),
        ('violation_fees', 'Violation Fees'),
        ('damage_charges', 'Damage Charges'),
        ('other', 'Other')
    ], string="Invoice Category", default='rent')
    
    hostel_contract_id = fields.Many2one(
        'hostel.contract',
        string="Hostel Contract"
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_category = fields.Selection(
        related='move_id.invoice_category',
        string="Invoice Category",
        store=True
    )
