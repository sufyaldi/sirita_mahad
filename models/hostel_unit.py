from odoo import models, fields

class HostelUnit(models.Model):
    _name = "hostel.unit"
    _description = "Hostel Unit"

    name = fields.Char(required=True)
    building_id = fields.Many2one(
        'hostel.building',
        required=True,
        ondelete='restrict'
    )
    floor = fields.Char()
    unit_type = fields.Char()
    active = fields.Boolean(default=True)
