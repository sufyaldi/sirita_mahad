from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_code = fields.Char(string="Employee Code")
    employment_type = fields.Selection([
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('probation', 'Probation')
    ], default='full_time')

    document_ids = fields.One2many(
        'hr.employee.document',
        'employee_id',
        string="Documents"
    )


class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'Employee Document'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    name = fields.Char(required=True, string="Document Name")
    document_type = fields.Selection([
        ('id', 'ID Card'),
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('license', 'License'),
        ('certificate', 'Certificate'),
        ('contract', 'Employment Contract'),
        ('other', 'Other')
    ], required=True)
    document_number = fields.Char()
    issue_date = fields.Date()
    expiry_date = fields.Date(tracking=True)
    document_file = fields.Binary(string="Document File")
    filename = fields.Char()
    notes = fields.Text()
    
    # Alerts
    days_to_expiry = fields.Integer(compute='_compute_days_to_expiry')
    is_expired = fields.Boolean(compute='_compute_days_to_expiry')
    is_expiring_soon = fields.Boolean(compute='_compute_days_to_expiry')

    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                days = (rec.expiry_date - today).days
                rec.days_to_expiry = days
                rec.is_expired = days < 0
                rec.is_expiring_soon = 0 <= days <= 30
            else:
                rec.days_to_expiry = 0
                rec.is_expired = False
                rec.is_expiring_soon = False


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Additional fields
    late_arrival = fields.Boolean(default=False)
    early_departure = fields.Boolean(default=False)
    regularization_requested = fields.Boolean(default=False)
    regularization_approved = fields.Boolean(default=False)
    notes = fields.Text()


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # Additional tracking
    leave_balance_before = fields.Float(string="Balance Before")
    leave_balance_after = fields.Float(string="Balance After")
