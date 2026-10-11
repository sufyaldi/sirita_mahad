from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(default=False)
    nim = fields.Char(string="NIM / Login Mahasantri", index=True)
    prodi = fields.Char(string="Program Studi")
    date_of_birth = fields.Date()
    university_id = fields.Many2one(
        'res.partner',
        domain=[('is_company', '=', True)]
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ])

    age_category = fields.Selection(
        [('underage', 'Underage'), ('overage', 'Overage')],
        compute="_compute_age_category",
        store=True
    )

    # Explicit One2many for hostel contracts (avoids conflict with account.analytic.account's contract_ids)
    hostel_contract_ids = fields.One2many(
        'hostel.contract',
        'student_id',
        string="Hostel Contracts",
    )

    def action_create_portal_user(self):
        for rec in self:
            if not rec.nim:
                continue
            user = self.env['res.users'].search([('login', '=', rec.nim)], limit=1)
            group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
            if not user:
                self.env['res.users'].create({
                    'name': rec.name,
                    'login': rec.nim,
                    'password': "M4hasantri@mahad",
                    'partner_id': rec.id,
                    'group_ids': [(4, group_portal.id)] if group_portal else [],
                })
            else:
                user.sudo().write({
                    'name': rec.name,
                    'password': "M4hasantri@mahad",
                })
        return True

    @api.depends('date_of_birth')
    def _compute_age_category(self):
        for rec in self:
            rec.age_category = False
            if rec.date_of_birth:
                age = (fields.Date.today() - rec.date_of_birth).days // 365
                rec.age_category = 'underage' if age < 18 else 'overage'
