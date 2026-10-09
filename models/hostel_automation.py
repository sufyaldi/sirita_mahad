import logging

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HostelBirthdayGreeting(models.Model):
    _name = 'hostel.birthday.greeting'
    _description = 'Birthday Greeting Configuration'

    name = fields.Char(string="Template Name", required=True)
    email_template_id = fields.Many2one(
        'mail.template',
        string="Email Template",
        required=True
    )
    active = fields.Boolean(default=True)
    last_run_date = fields.Date()

    def send_birthday_greetings(self):
        """Send birthday greetings to students whose birthday is today"""
        today = fields.Date.today()
        
        # Find students whose birthday is today
        students = self.env['res.partner'].search([
            ('is_student', '=', True),
            ('date_of_birth', '!=', False),
            ('email', '!=', False),
        ])
        
        birthday_students = []
        for student in students:
            if student.date_of_birth:
                if student.date_of_birth.month == today.month and student.date_of_birth.day == today.day:
                    birthday_students.append(student)
        
        sent_count = 0
        for student in birthday_students:
            try:
                if self.email_template_id:
                    self.email_template_id.send_mail(student.id, force_send=True)
                    # Log the greeting
                    self.env['hostel.birthday.greeting.log'].create({
                        'student_id': student.id,
                        'greeting_id': self.id,
                        'sent_date': fields.Datetime.now(),
                        'status': 'sent'
                    })
                    sent_count += 1
            except Exception as e:
                # Log error
                self.env['hostel.birthday.greeting.log'].create({
                    'student_id': student.id,
                    'greeting_id': self.id,
                    'sent_date': fields.Datetime.now(),
                    'status': 'failed',
                    'error_message': str(e)
                })
        
        self.last_run_date = today
        return sent_count

    @api.model
    def send_birthday_greetings_all(self):
        """Send birthday greetings for all active configurations"""
        greetings = self.search([('active', '=', True)])
        total_sent = 0
        for greeting in greetings:
            total_sent += greeting.send_birthday_greetings()
        return total_sent


class HostelBirthdayGreetingLog(models.Model):
    _name = 'hostel.birthday.greeting.log'
    _description = 'Birthday Greeting Log'
    _order = 'sent_date desc'

    student_id = fields.Many2one('res.partner', required=True)
    greeting_id = fields.Many2one('hostel.birthday.greeting', required=True)
    sent_date = fields.Datetime(required=True)
    status = fields.Selection([
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], required=True)
    error_message = fields.Text()


class HostelRenewalReminder(models.Model):
    _name = 'hostel.renewal.reminder'
    _description = 'Contract Renewal Reminder Configuration'

    name = fields.Char(string="Reminder Name", required=True)
    days_before_expiry = fields.Integer(
        required=True,
        string="Days Before Expiry",
        help="Number of days before contract expiry to send reminder"
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string="Email Template",
        domain=[('model', '=', 'hostel.contract')],
        required=True
    )
    active = fields.Boolean(default=True)
    last_run_date = fields.Datetime()

    def send_renewal_reminders(self):
        """Send renewal reminders to students whose contracts are expiring"""
        today = fields.Date.today()
        reminder_date = today + timedelta(days=self.days_before_expiry)
        
        # Find contracts expiring on reminder_date
        contracts = self.env['hostel.contract'].search([
            ('state', '=', 'active'),
            ('contract_end', '=', reminder_date),
        ])
        
        sent_count = 0
        for contract in contracts:
            if contract.student_id.email:
                try:
                    self.email_template_id.send_mail(contract.id, force_send=True)
                    # Log the reminder
                    self.env['hostel.renewal.reminder.log'].create({
                        'contract_id': contract.id,
                        'reminder_id': self.id,
                        'sent_date': fields.Datetime.now(),
                        'status': 'sent',
                        'days_before_expiry': self.days_before_expiry
                    })
                    sent_count += 1
                except Exception as e:
                    # Log error
                    self.env['hostel.renewal.reminder.log'].create({
                        'contract_id': contract.id,
                        'reminder_id': self.id,
                        'sent_date': fields.Datetime.now(),
                        'status': 'failed',
                        'error_message': str(e),
                        'days_before_expiry': self.days_before_expiry
                    })
        
        self.last_run_date = fields.Datetime.now()
        return sent_count


class HostelRenewalReminderLog(models.Model):
    _name = 'hostel.renewal.reminder.log'
    _description = 'Renewal Reminder Log'
    _order = 'sent_date desc'

    contract_id = fields.Many2one('hostel.contract', required=True)
    reminder_id = fields.Many2one('hostel.renewal.reminder', required=True)
    sent_date = fields.Datetime(required=True)
    days_before_expiry = fields.Integer()
    status = fields.Selection([
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], required=True)
    error_message = fields.Text()
