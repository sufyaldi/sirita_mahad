from odoo import models, fields

class HostelBuilding(models.Model):
    _name = "hostel.building"
    _description = "Hostel Building"

    name = fields.Char(required=True)
    code = fields.Char()
    gender_allowed = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('mixed', 'Mixed')
    ], default='mixed')
    address = fields.Text()
    active = fields.Boolean(default=True)
