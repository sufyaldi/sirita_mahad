from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HostelVisitor(models.Model):
    _name = "hostel.visitor"
    _description = "Hostel Visitor"
    _order = "visit_datetime desc, create_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Visitor Name",
        required=True,
        tracking=True
    )

    visitor_id_number = fields.Char(
        string="ID Number",
        tracking=True,
        help="Government ID, Passport, or other identification number"
    )

    phone = fields.Char(
        string="Phone",
        tracking=True
    )

    email = fields.Char(
        string="Email"
    )

    student_id = fields.Many2one(
        'res.partner',
        string="Student Being Visited",
        required=True,
        domain=[('is_student', '=', True)],
        tracking=True
    )

    building_id = fields.Many2one(
        'hostel.building',
        string="Building",
        compute='_compute_building_id',
        store=True,
        readonly=True
    )

    @api.depends('student_id', 'student_id.hostel_contract_ids', 'student_id.hostel_contract_ids.building_id', 'student_id.hostel_contract_ids.state')
    def _compute_building_id(self):
        for rec in self:
            if rec.student_id:
                active_contract = rec.student_id.hostel_contract_ids.filtered(lambda c: c.state == 'active')
                if active_contract:
                    rec.building_id = active_contract[0].building_id
                else:
                    rec.building_id = False
            else:
                rec.building_id = False

    visit_datetime = fields.Datetime(
        string="Visit Date & Time",
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )

    expected_duration = fields.Float(
        string="Expected Duration (Hours)",
        default=1.0,
        help="Expected duration of visit in hours"
    )

    purpose = fields.Text(
        string="Purpose of Visit",
        required=True,
        help="Reason for the visit"
    )

    status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('checked_in', 'Checked In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='pending', tracking=True, required=True)

    approved_by_id = fields.Many2one(
        'hr.employee',
        string="Approved By",
        tracking=True,
        help="Staff member who approved the visit"
    )

    approval_datetime = fields.Datetime(
        string="Approval Date & Time",
        tracking=True
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        help="Reason for rejection if visit was rejected"
    )

    checkin_datetime = fields.Datetime(
        string="Check-In Time",
        tracking=True
    )

    checkout_datetime = fields.Datetime(
        string="Check-Out Time",
        tracking=True
    )

    actual_duration = fields.Float(
        string="Actual Duration (Hours)",
        compute='_compute_actual_duration',
        store=True,
        help="Actual duration of visit in hours"
    )

    visitor_photo = fields.Binary(
        string="Visitor Photo",
        help="Photo of the visitor"
    )

    visitor_id_document = fields.Binary(
        string="ID Document",
        help="Copy of visitor's ID document"
    )

    notes = fields.Text(
        string="Notes/Remarks",
        help="Additional notes or remarks about the visit"
    )

    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the visitor record without removing it."
    )

    # Computed fields
    is_overdue = fields.Boolean(
        string="Overdue",
        compute='_compute_is_overdue',
        help="Check if visitor has exceeded expected duration"
    )

    @api.depends('checkin_datetime', 'checkout_datetime', 'expected_duration')
    def _compute_actual_duration(self):
        for rec in self:
            if rec.checkin_datetime and rec.checkout_datetime:
                delta = rec.checkout_datetime - rec.checkin_datetime
                rec.actual_duration = delta.total_seconds() / 3600.0
            elif rec.checkin_datetime and not rec.checkout_datetime:
                # Still checked in, calculate duration from check-in to now
                delta = fields.Datetime.now() - rec.checkin_datetime
                rec.actual_duration = delta.total_seconds() / 3600.0
            else:
                rec.actual_duration = 0.0

    @api.depends('checkin_datetime', 'expected_duration', 'status')
    def _compute_is_overdue(self):
        ICP = self.env['ir.config_parameter'].sudo()
        overstay_minutes_cfg = int(ICP.get_str('sirita_mahad.visitor_overstay_minutes', '0') or 0)
        for rec in self:
            if rec.checkin_datetime and rec.status == 'checked_in':
                delta = fields.Datetime.now() - rec.checkin_datetime
                minutes = delta.total_seconds() / 60.0
                allowed_minutes = (rec.expected_duration or 0.0) * 60.0
                if overstay_minutes_cfg > 0:
                    allowed_minutes += overstay_minutes_cfg
                rec.is_overdue = minutes > allowed_minutes if allowed_minutes >= 0 else False
            else:
                rec.is_overdue = False

    @api.constrains('visit_datetime', 'status')
    def _check_visit_datetime(self):
        for rec in self:
            if rec.visit_datetime and rec.visit_datetime < fields.Datetime.now():
                # Allow past dates for completed, checked-in, or cancelled (historical/demo data)
                if rec.status not in ('completed', 'checked_in', 'cancelled'):
                    raise ValidationError("Visit date/time cannot be in the past.")

    @api.constrains('student_id', 'visit_datetime')
    def _check_max_visitors_per_day(self):
        """Enforce optional soft limit for visitors per student per day."""
        ICP = self.env['ir.config_parameter'].sudo()
        max_per_day = int(ICP.get_str('sirita_mahad.visitor_max_per_day', '0') or 0)
        if not max_per_day:
            return
        for rec in self:
            if not rec.student_id or not rec.visit_datetime:
                continue
            day_start = fields.Datetime.to_datetime(rec.visit_datetime).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start.replace(hour=23, minute=59, second=59)
            count = self.search_count([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('visit_datetime', '>=', day_start),
                ('visit_datetime', '<=', day_end),
            ])
            if count >= max_per_day:
                raise ValidationError(
                    "Maximum visitors per day for %s is %s." % (rec.student_id.display_name, max_per_day)
                )

    @api.constrains('checkin_datetime', 'checkout_datetime')
    def _check_checkout_after_checkin(self):
        for rec in self:
            if rec.checkin_datetime and rec.checkout_datetime:
                if rec.checkout_datetime < rec.checkin_datetime:
                    raise ValidationError("Check-out time cannot be before check-in time.")

    @api.model_create_multi
    def create(self, vals_list):
        """Optionally auto-approve visitors based on settings."""
        records = super().create(vals_list)
        ICP = self.env['ir.config_parameter'].sudo()
        require_approval = ICP.get_str('sirita_mahad.visitor_require_approval', 'True') != 'False'
        if not require_approval:
            for rec in records:
                if rec.status == 'pending':
                    rec._do_approve(from_auto=True)
        return records

    def _do_approve(self, from_auto=False):
        """Internal helper to approve a visitor (used by button + auto-approval)."""
        for rec in self:
            if rec.status != 'pending':
                if from_auto:
                    continue
                raise UserError("Only pending visits can be approved.")
            rec.status = 'approved'
            rec.approved_by_id = self.env.user.employee_ids[:1] if self.env.user.employee_ids else False
            rec.approval_datetime = fields.Datetime.now()
            rec._send_approval_notification()

    def action_approve(self):
        """Approve the visitor request (button)."""
        self._do_approve(from_auto=False)

    def action_reject(self):
        """Reject the visitor request"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError("Only pending visits can be rejected.")
        
        return {
            'name': 'Reject Visit Request',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.visitor.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_visitor_id': self.id}
        }

    def action_checkin(self):
        """Check-in the visitor"""
        for rec in self:
            if rec.status not in ['approved', 'checked_in']:
                raise UserError("Only approved visits can be checked in.")
            if rec.status == 'checked_in':
                raise UserError("Visitor is already checked in.")
            rec.status = 'checked_in'
            rec.checkin_datetime = fields.Datetime.now()
            rec._send_checkin_notification()

    def action_checkout(self):
        """Check-out the visitor"""
        for rec in self:
            if rec.status != 'checked_in':
                raise UserError("Only checked-in visitors can be checked out.")
            rec.status = 'completed'
            rec.checkout_datetime = fields.Datetime.now()
            rec._send_checkout_notification()

    def action_cancel(self):
        """Cancel the visitor request"""
        for rec in self:
            if rec.status in ['completed', 'cancelled']:
                raise UserError("Cannot cancel a completed or already cancelled visit.")
            rec.status = 'cancelled'

    def action_reset_to_pending(self):
        """Reset status to pending"""
        for rec in self:
            rec.status = 'pending'
            rec.approved_by_id = False
            rec.approval_datetime = False
            rec.rejection_reason = False
            rec.checkin_datetime = False
            rec.checkout_datetime = False

    def _send_approval_notification(self):
        """Send approval notification (email/SMS) based on settings."""
        ICP = self.env['ir.config_parameter'].sudo()
        email_enabled = ICP.get_str('sirita_mahad.visitor_notify_email', 'False') != 'False'
        sms_enabled = ICP.get_str('sirita_mahad.visitor_notify_sms', 'False') != 'False'
        template_id = ICP.get_str('sirita_mahad.email_template_visitor')
        for rec in self:
            if email_enabled:
                if template_id:
                    try:
                        tmpl = self.env['mail.template'].browse(int(template_id))
                        if tmpl.exists():
                            tmpl.send_mail(rec.id, force_send=True)
                        else:
                            rec.message_post(body="Visitor request approved.")
                    except Exception:
                        rec.message_post(body="Visitor request approved.")
                else:
                    rec.message_post(body="Visitor request approved.")
            if sms_enabled and ICP.get_str('sirita_mahad.enable_sms', 'False') != 'False':
                rec.message_post(body="[SMS] Visitor request approved.")

    def _send_checkin_notification(self):
        ICP = self.env['ir.config_parameter'].sudo()
        email_enabled = ICP.get_str('sirita_mahad.visitor_notify_email', 'False') != 'False'
        sms_enabled = ICP.get_str('sirita_mahad.visitor_notify_sms', 'False') != 'False'
        template_id = ICP.get_str('sirita_mahad.email_template_visitor')
        for rec in self:
            if email_enabled:
                if template_id:
                    try:
                        tmpl = self.env['mail.template'].browse(int(template_id))
                        if tmpl.exists():
                            tmpl.send_mail(rec.id, force_send=True)
                        else:
                            rec.message_post(body="Visitor checked in.")
                    except Exception:
                        rec.message_post(body="Visitor checked in.")
                else:
                    rec.message_post(body="Visitor checked in.")
            if sms_enabled and ICP.get_str('sirita_mahad.enable_sms', 'False') != 'False':
                rec.message_post(body="[SMS] Visitor checked in.")

    def _send_checkout_notification(self):
        ICP = self.env['ir.config_parameter'].sudo()
        email_enabled = ICP.get_str('sirita_mahad.visitor_notify_email', 'False') != 'False'
        sms_enabled = ICP.get_str('sirita_mahad.visitor_notify_sms', 'False') != 'False'
        template_id = ICP.get_str('sirita_mahad.email_template_visitor')
        for rec in self:
            if email_enabled:
                if template_id:
                    try:
                        tmpl = self.env['mail.template'].browse(int(template_id))
                        if tmpl.exists():
                            tmpl.send_mail(rec.id, force_send=True)
                        else:
                            rec.message_post(body="Visitor checked out.")
                    except Exception:
                        rec.message_post(body="Visitor checked out.")
                else:
                    rec.message_post(body="Visitor checked out.")
            if sms_enabled and ICP.get_str('sirita_mahad.enable_sms', 'False') != 'False':
                rec.message_post(body="[SMS] Visitor checked out.")

    def _send_rejection_notification(self):
        ICP = self.env['ir.config_parameter'].sudo()
        email_enabled = ICP.get_str('sirita_mahad.visitor_notify_email', 'False') != 'False'
        sms_enabled = ICP.get_str('sirita_mahad.visitor_notify_sms', 'False') != 'False'
        template_id = ICP.get_str('sirita_mahad.email_template_visitor')
        for rec in self:
            if email_enabled:
                if template_id:
                    try:
                        tmpl = self.env['mail.template'].browse(int(template_id))
                        if tmpl.exists():
                            tmpl.send_mail(rec.id, force_send=True)
                        else:
                            rec.message_post(body="Visitor request rejected.")
                    except Exception:
                        rec.message_post(body="Visitor request rejected.")
                else:
                    rec.message_post(body="Visitor request rejected.")
            if sms_enabled and ICP.get_str('sirita_mahad.enable_sms', 'False') != 'False':
                rec.message_post(body="[SMS] Visitor request rejected.")

    @api.depends('name', 'student_id', 'visit_datetime')
    def _compute_display_name(self):
        for rec in self:
            label = "%s - %s" % (rec.name or '', rec.student_id.name or '')
            if rec.visit_datetime:
                label += " (%s)" % fields.Datetime.to_string(rec.visit_datetime)
            rec.display_name = label


class HostelVisitorRejectWizard(models.TransientModel):
    _name = "hostel.visitor.reject.wizard"
    _description = "Visitor Rejection Wizard"

    visitor_id = fields.Many2one(
        'hostel.visitor',
        string="Visitor",
        required=True
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        required=True
    )

    def action_reject(self):
        """Confirm rejection"""
        self.visitor_id.rejection_reason = self.rejection_reason
        self.visitor_id.status = 'rejected'
        self.visitor_id.approved_by_id = self.env.user.employee_ids[:1] if self.env.user.employee_ids else False
        
        # Send notification
        self.visitor_id._send_rejection_notification()
        
        return {'type': 'ir.actions.act_window_close'}
