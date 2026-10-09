from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class HostelGroupCommunication(models.Model):
    _name = 'hostel.group.communication'
    _description = 'Group Communication'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Subject", required=True)
    message = fields.Html(required=True)
    
    # Target selection
    target_type = fields.Selection([
        ('building', 'Building'),
        ('unit', 'Unit/Apartment'),
        ('room', 'Room'),
        ('bed', 'Bed'),
        ('custom', 'Custom Selection')
    ], required=True, default='building')
    
    building_ids = fields.Many2many(
        'hostel.building',
        string="Buildings"
    )
    
    unit_ids = fields.Many2many(
        'hostel.unit',
        string="Units/Apartments"
    )
    
    room_ids = fields.Many2many(
        'hostel.room',
        string="Rooms"
    )
    
    bed_ids = fields.Many2many(
        'hostel.bed',
        string="Beds"
    )
    
    student_ids = fields.Many2many(
        'res.partner',
        string="Selected Students",
        domain=[('is_student', '=', True)],
        help="Manually select students for custom communication"
    )
    
    # Communication channels
    send_email = fields.Boolean(default=True)
    send_sms = fields.Boolean(default=False)
    send_notification = fields.Boolean(default=True)
    
    # Template
    template_id = fields.Many2one(
        'mail.template',
        string="Email Template"
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent')
    ], default='draft', tracking=True)
    
    sent_date = fields.Datetime(readonly=True)
    sent_by = fields.Many2one('res.users', readonly=True)
    
    # Log
    communication_log_ids = fields.One2many(
        'hostel.communication.log',
        'communication_id',
        string="Communication Log"
    )
    
    total_recipients = fields.Integer(compute='_compute_recipients', store=True)
    sent_count = fields.Integer(compute='_compute_sent_count')
    failed_count = fields.Integer(compute='_compute_failed_count')

    @api.depends('target_type', 'building_ids', 'unit_ids', 'room_ids', 'bed_ids', 'student_ids')
    def _compute_recipients(self):
        for rec in self:
            rec.total_recipients = len(rec._get_target_students())

    def _compute_sent_count(self):
        for rec in self:
            rec.sent_count = len(rec.communication_log_ids.filtered(lambda l: l.status == 'sent'))

    def _compute_failed_count(self):
        for rec in self:
            rec.failed_count = len(rec.communication_log_ids.filtered(lambda l: l.status == 'failed'))

    def _get_target_students(self):
        """Get list of target students based on selection"""
        students = self.env['res.partner']
        
        if self.target_type == 'building' and self.building_ids:
            contracts = self.env['hostel.contract'].search([
                ('building_id', 'in', self.building_ids.ids),
                ('state', '=', 'active')
            ])
            students = contracts.mapped('student_id')
        
        elif self.target_type == 'unit' and self.unit_ids:
            contracts = self.env['hostel.contract'].search([
                ('unit_id', 'in', self.unit_ids.ids),
                ('state', '=', 'active')
            ])
            students = contracts.mapped('student_id')
        
        elif self.target_type == 'room' and self.room_ids:
            contracts = self.env['hostel.contract'].search([
                ('room_id', 'in', self.room_ids.ids),
                ('state', '=', 'active')
            ])
            students = contracts.mapped('student_id')
        
        elif self.target_type == 'bed' and self.bed_ids:
            contracts = self.env['hostel.contract'].search([
                ('bed_id', 'in', self.bed_ids.ids),
                ('state', '=', 'active')
            ])
            students = contracts.mapped('student_id')
        
        elif self.target_type == 'custom' and self.student_ids:
            students = self.student_ids
        
        return students

    def action_send(self):
        """Send communication to all target students"""
        if not self.message:
            raise UserError("Message content is required")
        
        students = self._get_target_students()
        if not students:
            raise UserError("No students found for the selected criteria")
        
        sent = 0
        failed = 0
        
        for student in students:
            try:
                # Send email
                if self.send_email and student.email:
                    if self.template_id:
                        self.template_id.send_mail(student.id, force_send=True)
                    else:
                        # Send direct email
                        mail_values = {
                            'subject': self.name,
                            'body_html': self.message,
                            'email_to': student.email,
                            'email_from': self.env.user.email,
                        }
                        self.env['mail.mail'].create(mail_values).send()
                
                # Send notification
                if self.send_notification:
                    self.env['mail.message'].create({
                        'model': 'res.partner',
                        'res_id': student.id,
                        'subject': self.name,
                        'body': self.message,
                        'message_type': 'notification',
                    })
                
                # Log success
                self.env['hostel.communication.log'].create({
                    'communication_id': self.id,
                    'student_id': student.id,
                    'status': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'channel': 'email' if self.send_email else 'notification'
                })
                sent += 1
                
            except Exception as e:
                # Log failure
                self.env['hostel.communication.log'].create({
                    'communication_id': self.id,
                    'student_id': student.id,
                    'status': 'failed',
                    'error_message': str(e),
                    'sent_date': fields.Datetime.now(),
                })
                failed += 1
        
        self.state = 'sent'
        self.sent_date = fields.Datetime.now()
        self.sent_by = self.env.user.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Communication Sent',
                'message': f'Sent to {sent} students. {failed} failed.',
                'type': 'success',
            }
        }


class HostelCommunicationLog(models.Model):
    _name = 'hostel.communication.log'
    _description = 'Communication Log'
    _order = 'sent_date desc'

    communication_id = fields.Many2one(
        'hostel.group.communication',
        required=True,
        ondelete='cascade'
    )
    student_id = fields.Many2one('res.partner', required=True)
    sent_date = fields.Datetime(required=True)
    status = fields.Selection([
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], required=True)
    channel = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('notification', 'Notification')
    ])
    error_message = fields.Text()
