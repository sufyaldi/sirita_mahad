from odoo import models, fields

class HostelBed(models.Model):
    _name = "hostel.bed"
    _description = "Hostel Bed"

    name = fields.Char(required=True)
    room_id = fields.Many2one(
        'hostel.room',
        required=True,
        ondelete='restrict'
    )
    is_active = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    occupancy_status = fields.Selection(
        [('vacant', 'Vacant'), ('occupied', 'Occupied')],
        compute="_compute_occupancy",
    )

    def _compute_occupancy(self):
        Contract = self.env['hostel.contract']
        for bed in self:
            active_contract = Contract.search([
                ('bed_id', '=', bed.id),
                ('state', '=', 'active')
            ], limit=1)
            bed.occupancy_status = 'occupied' if active_contract else 'vacant'
