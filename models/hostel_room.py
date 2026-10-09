from odoo import models, fields

class HostelRoom(models.Model):
    _name = "hostel.room"
    _description = "Hostel Room"

    name = fields.Char(required=True)
    unit_id = fields.Many2one(
        'hostel.unit',
        required=True,
        ondelete='restrict'
    )
    room_type = fields.Selection([
        ('single', 'Single'),
        ('twin', 'Twin'),
        ('studio', 'Studio')
    ], required=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('mixed', 'Mixed')
    ], default='mixed')

    room_status = fields.Selection([
        ('dirty', 'Dirty'),
        ('ready', 'Ready for Arrival'),
        ('buffer', 'Buffer Room'),
        ('out', 'Out of Order')
    ], default='ready')

    active = fields.Boolean(default=True)
