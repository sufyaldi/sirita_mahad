from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HostelAsset(models.Model):
    _name = 'hostel.asset'
    _description = 'Hostel Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    asset_code = fields.Char(string="Asset Code", tracking=True)
    asset_category_id = fields.Many2one(
        'hostel.asset.category',
        string="Category",
        required=True
    )
    
    # Location mapping
    building_id = fields.Many2one('hostel.building')
    unit_id = fields.Many2one('hostel.unit')
    room_id = fields.Many2one('hostel.room')
    bed_id = fields.Many2one('hostel.bed')
    
    # Asset details
    purchase_date = fields.Date(tracking=True)
    purchase_cost = fields.Monetary(tracking=True)
    warranty_expiry = fields.Date(tracking=True)
    current_value = fields.Monetary(compute='_compute_current_value', store=True)
    
    # Lifecycle
    state = fields.Selection([
        ('procured', 'Procured'),
        ('allocated', 'Allocated'),
        ('maintenance', 'Under Maintenance'),
        ('replaced', 'Replaced'),
        ('disposed', 'Disposed')
    ], default='procured', tracking=True)
    
    # Condition and maintenance
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], default='good', tracking=True)
    
    maintenance_history_ids = fields.One2many(
        'hostel.asset.maintenance',
        'asset_id',
        string="Maintenance History"
    )
    
    service_history_ids = fields.One2many(
        'hostel.asset.service',
        'asset_id',
        string="Service History"
    )
    
    # Financial
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    depreciation_rate = fields.Float(string="Depreciation Rate (%)", default=10.0)
    
    # Supplier/Vendor
    supplier_id = fields.Many2one('res.partner', string="Supplier/Vendor")
    
    # Description
    description = fields.Text()
    notes = fields.Text()
    
    active = fields.Boolean(default=True)

    @api.depends('purchase_cost', 'purchase_date', 'depreciation_rate')
    def _compute_current_value(self):
        for rec in self:
            if rec.purchase_cost and rec.purchase_date:
                years = (fields.Date.today() - rec.purchase_date).days / 365.0
                depreciation = rec.purchase_cost * (rec.depreciation_rate / 100) * years
                rec.current_value = max(0, rec.purchase_cost - depreciation)
            else:
                rec.current_value = 0.0

    def action_allocate(self):
        self.state = 'allocated'

    def action_maintenance(self):
        self.state = 'maintenance'

    def action_replace(self):
        self.state = 'replaced'

    def action_dispose(self):
        self.state = 'disposed'


class HostelAssetCategory(models.Model):
    _name = 'hostel.asset.category'
    _description = 'Asset Category'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)


class HostelAssetMaintenance(models.Model):
    _name = 'hostel.asset.maintenance'
    _description = 'Asset Maintenance Record'
    _order = 'maintenance_date desc'

    asset_id = fields.Many2one('hostel.asset', required=True, ondelete='cascade')
    maintenance_date = fields.Date(required=True, default=fields.Date.today)
    maintenance_type = fields.Selection([
        ('repair', 'Repair'),
        ('service', 'Service'),
        ('inspection', 'Inspection'),
        ('replacement', 'Replacement')
    ], required=True)
    description = fields.Text(required=True)
    cost = fields.Monetary()
    vendor_id = fields.Many2one('res.partner', string="Service Provider")
    currency_id = fields.Many2one(
        'res.currency',
        related='asset_id.currency_id'
    )
    notes = fields.Text()


class HostelAssetService(models.Model):
    _name = 'hostel.asset.service'
    _description = 'Asset Service Record'
    _order = 'service_date desc'

    asset_id = fields.Many2one('hostel.asset', required=True, ondelete='cascade')
    service_date = fields.Date(required=True, default=fields.Date.today)
    service_type = fields.Char(required=True)
    description = fields.Text()
    cost = fields.Monetary()
    service_provider_id = fields.Many2one('res.partner', string="Service Provider")
    currency_id = fields.Many2one(
        'res.currency',
        related='asset_id.currency_id'
    )
    warranty_until = fields.Date()
    notes = fields.Text()
