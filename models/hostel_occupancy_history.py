from odoo import models, fields

class HostelOccupancyHistory(models.Model):
    _name = "hostel.occupancy.history"
    _description = "Hostel Occupancy History"
    _order = "check_in desc"

    student_id = fields.Many2one('res.partner', required=True)
    bed_id = fields.Many2one('hostel.bed', required=True)
    contract_id = fields.Many2one('hostel.contract')
    check_in = fields.Datetime(required=True)
    check_out = fields.Datetime()
    remarks = fields.Text()
