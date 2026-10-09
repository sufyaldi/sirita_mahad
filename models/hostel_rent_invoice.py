from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class HostelRentInvoice(models.Model):
    _name = "hostel.rent.invoice"
    _description = "Hostel Rent Invoice"
    _order = "period_start desc, id desc"

    contract_id = fields.Many2one(
        "hostel.contract",
        string="Contract",
        required=True,
        ondelete="cascade",
    )
    student_id = fields.Many2one(
        "res.partner",
        related="contract_id.student_id",
        store=True,
        string="Student",
    )
    name = fields.Char(
        string="Description",
        required=True,
        default="/",
    )
    period_start = fields.Date(string="Period From", required=True)
    period_end = fields.Date(string="Period To", required=True)
    amount = fields.Monetary(
        string="Amount",
        required=True,
        currency_field="currency_id",
    )
    due_date = fields.Date(string="Due Date", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="contract_id.currency_id",
        store=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("invoiced", "Invoiced"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        compute="_compute_state",
        store=True,
        readonly=False,
    )

    penalty_amount = fields.Monetary(
        string="Late Payment Penalty",
        currency_field="currency_id",
        compute="_compute_penalty_amount",
        store=True,
        readonly=False,
        help="Penalty computed when the invoice becomes overdue, based on settings.",
    )
    total_with_penalty = fields.Monetary(
        string="Total with Penalty",
        currency_field="currency_id",
        help="Original amount plus any computed late payment penalty.",
        compute="_compute_total_with_penalty",
        store=True,
    )

    # Convenience flag reflecting payment gateway setting
    payment_gateway_enabled = fields.Boolean(
        string="Payment gateway enabled",
        compute="_compute_payment_gateway_enabled",
        help="Reflects the 'Enable payment gateway integration' setting.",
    )

    @api.depends("invoice_id", "invoice_id.payment_state", "due_date")
    def _compute_state(self):
        for rec in self:
            if rec.state == "cancelled":
                continue
            if not rec.invoice_id:
                today = fields.Date.context_today(rec)
                if rec.due_date and rec.due_date < today:
                    rec.state = "overdue"
                else:
                    rec.state = "draft"
            else:
                if rec.invoice_id.payment_state == "paid":
                    rec.state = "paid"
                elif rec.invoice_id.state == "posted":
                    if rec.due_date and rec.due_date < fields.Date.context_today(rec):
                        rec.state = "overdue"
                    else:
                        rec.state = "invoiced"
                else:
                    rec.state = "draft"

    @api.depends("state", "amount")
    def _compute_penalty_amount(self):
        ICP = self.env["ir.config_parameter"].sudo()
        penalty_type = ICP.get_str(
            "sirita_mahad.late_penalty_type", "none"
        ) or "none"
        penalty_value_str = ICP.get_str(
            "sirita_mahad.late_penalty_value", "0"
        ) or "0"
        try:
            penalty_value = float(penalty_value_str)
        except ValueError:
            penalty_value = 0.0

        for rec in self:
            if rec.state == "overdue" and penalty_type != "none" and penalty_value > 0:
                if penalty_type == "fixed":
                    rec.penalty_amount = penalty_value
                elif penalty_type == "percent":
                    rec.penalty_amount = (rec.amount or 0.0) * (penalty_value / 100.0)
                else:
                    rec.penalty_amount = 0.0
            else:
                rec.penalty_amount = 0.0

    @api.depends("amount", "penalty_amount")
    def _compute_total_with_penalty(self):
        for rec in self:
            rec.total_with_penalty = (rec.amount or 0.0) + (rec.penalty_amount or 0.0)

    def _compute_payment_gateway_enabled(self):
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = (
            ICP.get_str("sirita_mahad.enable_payment_gateway", "False")
            != "False"
        )
        for rec in self:
            rec.payment_gateway_enabled = enabled

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                contract = self.env["hostel.contract"].browse(vals.get("contract_id"))
                if contract and vals.get("period_start"):
                    start = vals["period_start"]
                    if isinstance(start, str):
                        start = fields.Date.from_string(start)
                    if hasattr(start, "strftime"):
                        vals["name"] = "Rent %s" % start.strftime("%b %Y")
        return super().create(vals_list)

    def action_create_invoice(self):
        """Create account.move (customer invoice) for this rent invoice."""
        self.ensure_one()
        if self.invoice_id:
            raise UserError("An invoice already exists for this rent period.")
        if self.contract_id.state != "active":
            raise UserError("Rent invoices can only be created for active contracts.")
        invoice = self._create_invoice()
        self.invoice_id = invoice.id
        self.state = "invoiced"
        return self._action_view_invoice(invoice)

    def _create_invoice(self):
        """Create the account.move for rent."""
        self.ensure_one()
        contract = self.contract_id
        # Income account: use company's default or first income account
        account = self.env["account.account"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
        if not account:
            account = self.env["account.account"].search(
                [
                    ("company_id", "=", self.env.company.id),
                    ("account_type", "in", ["income", "income_other"]),
                ],
                limit=1,
            )
        invoice_lines = [
            (
                0,
                0,
                {
                    "name": self.name,
                    "quantity": 1,
                    "price_unit": self.amount,
                    "account_id": account.id if account else False,
                },
            )
        ]
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": contract.student_id.id,
            "invoice_date": fields.Date.context_today(self),
            "invoice_line_ids": invoice_lines,
            "ref": "%s - %s" % (self.name, contract.bed_id.name or ""),
            "invoice_category": "rent",
            "hostel_contract_id": contract.id,
        }
        return self.env["account.move"].create(invoice_vals)

    def _action_view_invoice(self, invoice):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_invoice(self):
        """Open the linked invoice."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("No invoice has been created yet.")
        return self._action_view_invoice(self.invoice_id)

    def action_cancel(self):
        for rec in self:
            if rec.invoice_id and rec.invoice_id.state not in ("draft", "cancel"):
                raise UserError(
                    "Cannot cancel a rent invoice that has been posted. Cancel or reset the linked invoice first."
                )
            rec.state = "cancelled"

    def action_set_draft(self):
        self.write({"state": "draft"})

    @api.model
    def _cron_generate_rent_invoices(self):
        """Generate draft rent invoices for the current month for active contracts that don't have one."""
        today = fields.Date.context_today(self)
        ICP = self.env['ir.config_parameter'].sudo()
        day_str = ICP.get_str('sirita_mahad.rent_invoice_day', '1') or '1'
        try:
            gen_day = max(1, min(28, int(day_str)))
        except ValueError:
            gen_day = 1
        period_start = today.replace(day=1)
        # period_end = last day of month
        next_month = period_start + relativedelta(months=1)
        period_end = next_month - timedelta(days=1)
        # Due date: configurable days after period_start (fallback 7)
        reminder_str = ICP.get_str('sirita_mahad.payment_reminder_days_before_due', '7') or '7'
        try:
            offset_days = int(reminder_str)
        except ValueError:
            offset_days = 7
        due_date = period_start + timedelta(days=offset_days)
        active_contracts = self.env["hostel.contract"].search(
            [
                ("state", "=", "active"),
                ("monthly_rent", ">", 0),
                ("contract_start", "<=", period_end),
                ("contract_end", ">=", period_start),
            ]
        )
        created = self.browse()
        for contract in active_contracts:
            existing = self.search(
                [
                    ("contract_id", "=", contract.id),
                    ("period_start", "=", period_start),
                ],
                limit=1,
            )
            if existing:
                continue
            # Prorate if contract starts or ends in the middle of the month
            days_in_period = (period_end - period_start).days + 1
            start = max(contract.contract_start, period_start)
            end = min(contract.contract_end, period_end)
            days_occupied = (end - start).days + 1
            amount = contract.monthly_rent * (days_occupied / days_in_period) if days_in_period else 0
            created += self.create(
                {
                    "contract_id": contract.id,
                    "name": "Rent %s" % period_start.strftime("%b %Y"),
                    "period_start": period_start,
                    "period_end": period_end,
                    "amount": round(amount, 2),
                    "due_date": due_date,
                }
            )
        return created
