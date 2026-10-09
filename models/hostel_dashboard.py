from odoo import models, fields, api
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


def _parse_date(value):
    """Convert string from JSON/RPC to date. Returns None if value is None or empty."""
    if value is None:
        return None
    if isinstance(value, str):
        value = (value or "").strip()
        if not value:
            return None
        return date.fromisoformat(value[:10])
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return value


class HostelDashboard(models.TransientModel):
    _name = 'hostel.dashboard'
    _description = 'Hostel Dashboard'

    @api.model
    def action_visitors_today(self):
        today = fields.Date.today()
        return {
            'name': "Today's Visitors",
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.visitor',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('visit_datetime', '>=', datetime.combine(today, datetime.min.time())),
                ('visit_datetime', '<', datetime.combine(today + timedelta(days=1), datetime.min.time())),
            ],
        }

    @api.model
    def action_pending_visitors(self):
        return {
            'name': 'Pending Visitors',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.visitor',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('status', '=', 'pending')],
        }

    @api.model
    def action_maintenance_open(self):
        return {
            'name': 'Open Maintenance',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.maintenance.request',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('state', 'not in', ['completed', 'cancelled'])],
        }

    @api.model
    def action_rent_invoices(self):
        return {
            'name': 'Rent Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.rent.invoice',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
        }

    @api.model
    def action_student_attendance(self):
        return {
            'name': 'Student Attendance',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.student.attendance',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
        }

    @api.model
    def action_complaints_open(self):
        return {
            'name': 'Open Complaints',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.complaint',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('state', 'not in', ['resolved', 'closed', 'cancelled'])],
        }

    @api.model
    def action_laundry_open(self):
        return {
            'name': 'Laundry Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.laundry.request',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('state', 'not in', ['completed', 'cancelled'])],
        }

    @api.model
    def action_room_inspections(self):
        return {
            'name': 'Room Inspections',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.room.inspection',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
        }

    @api.model
    def action_announcements(self):
        return {
            'name': 'Notice Board',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.announcement',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'context': {'search_default_active': 1},
        }

    @api.model
    def action_daily_checkin(self):
        today = fields.Date.today()
        return {
            'name': 'Daily Check-In Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.checkin',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('checkin_datetime', '>=', datetime.combine(today, datetime.min.time())),
                ('checkin_datetime', '<', datetime.combine(today + timedelta(days=1), datetime.min.time())),
                ('state', '=', 'checked_in')
            ],
            'context': {'search_default_today': 1}
        }

    @api.model
    def action_daily_contract_ending(self):
        today = fields.Date.today()
        return {
            'name': 'Daily Contract Ending Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.contract',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('contract_end', '=', today),
                ('state', 'in', ['active', 'draft'])
            ],
        }

    @api.model
    def action_active_students(self):
        return {
            'name': 'Active Students Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.contract',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('state', '=', 'active')],
            'context': {'group_by': 'building_id'}
        }

    @api.model
    def action_vacant_spaces(self):
        occupied_bed_ids = self.env['hostel.contract'].search([
            ('state', '=', 'active')
        ]).mapped('bed_id').ids
        return {
            'name': 'Vacant Spaces Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.bed',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('id', 'not in', occupied_bed_ids),
                ('is_active', '=', True),
                ('active', '=', True)
            ],
            'context': {'group_by': ['room_id', 'room_id.room_type']}
        }

    @api.model
    def action_upcoming_30_days(self):
        today = fields.Date.today()
        next_30_days = today + timedelta(days=30)
        return {
            'name': 'Contracts Expiring in Next 30 Days',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.contract',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('contract_end', '>=', today),
                ('contract_end', '<=', next_30_days),
                ('state', '=', 'active')
            ],
        }

    @api.model
    def action_upcoming_10_days(self):
        today = fields.Date.today()
        next_10_days = today + timedelta(days=10)
        return {
            'name': 'Contracts Expiring in Next 10 Days',
            'type': 'ir.actions.act_window',
            'res_model': 'hostel.contract',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [
                ('contract_end', '>=', today),
                ('contract_end', '<=', next_10_days),
                ('state', '=', 'active')
            ],
        }

    # -------------------------------------------------------------------------
    # All statistics use date_from and date_to where applicable.
    # Default: date_to = today, date_from = today - 30.
    # -------------------------------------------------------------------------

    @api.model
    def get_statistics(self, date_from=None, date_to=None):
        """Get dashboard statistics for JavaScript component. All data filtered by date_from/date_to where applicable."""
        today = fields.Date.today()
        ICP = self.env['ir.config_parameter'].sudo()
        default_days = int(ICP.get_str('sirita_mahad.default_dashboard_range_days', '30') or 30)
        date_from = _parse_date(date_from) or (today - timedelta(days=default_days))
        date_to = _parse_date(date_to) or today
        range_end_30 = date_to + timedelta(days=30)
        range_end_10 = date_to + timedelta(days=10)

        # Check-ins in range [date_from, date_to]
        checkins = self.env['hostel.checkin'].search_count([
            ('checkin_datetime', '>=', datetime.combine(date_from, datetime.min.time())),
            ('checkin_datetime', '<=', datetime.combine(date_to, datetime.max.time())),
            ('state', '=', 'checked_in')
        ])

        # Contracts ending in range [date_from, date_to]
        contracts_ending = self.env['hostel.contract'].search_count([
            ('contract_end', '>=', date_from),
            ('contract_end', '<=', date_to),
            ('state', 'in', ['active', 'draft'])
        ])

        # Active students as of date_to (contract active on date_to)
        contracts_on_date = self.env['hostel.contract'].search([
            ('state', '=', 'active'),
            ('contract_start', '<=', date_to),
            ('contract_end', '>=', date_to),
        ])
        active_students = len(set(contracts_on_date.mapped('student_id').ids))

        # Vacant spaces as of date_to (beds not occupied on date_to)
        occupied_bed_ids = set(contracts_on_date.mapped('bed_id').ids)
        all_beds = self.env['hostel.bed'].search([
            ('is_active', '=', True),
            ('active', '=', True)
        ])
        vacant_beds = len([b for b in all_beds if b.id not in occupied_bed_ids])

        # Upcoming: contracts ending between date_to and date_to+30/10
        upcoming_30 = self.env['hostel.contract'].search_count([
            ('contract_end', '>=', date_to),
            ('contract_end', '<=', range_end_30),
            ('state', '=', 'active')
        ])
        upcoming_10 = self.env['hostel.contract'].search_count([
            ('contract_end', '>=', date_to),
            ('contract_end', '<=', range_end_10),
            ('state', '=', 'active')
        ])

        # Total counts (infrastructure; not date-filtered)
        total_buildings = self.env['hostel.building'].search_count([('active', '=', True)])
        total_rooms = self.env['hostel.room'].search_count([('active', '=', True)])
        total_beds = self.env['hostel.bed'].search_count([('active', '=', True), ('is_active', '=', True)])

        # Occupancy rate as of date_to
        total_active_beds = len(all_beds)
        occupied_beds = len(occupied_bed_ids)
        occupancy_rate = (occupied_beds / total_active_beds * 100) if total_active_beds else 0.0

        # Visitors on date_to (single day)
        visitor_today = self.env['hostel.visitor'].search_count([
            ('visit_datetime', '>=', datetime.combine(date_to, datetime.min.time())),
            ('visit_datetime', '<=', datetime.combine(date_to, datetime.max.time())),
        ])
        visitor_pending = self.env['hostel.visitor'].search_count([
            ('status', '=', 'pending')
        ])
        visitor_in_range = self.env['hostel.visitor'].search_count([
            ('visit_datetime', '>=', datetime.combine(date_from, datetime.min.time())),
            ('visit_datetime', '<=', datetime.combine(date_to, datetime.max.time())),
        ])

        # Maintenance: created in [date_from, date_to]
        maintenance_open = self.env['hostel.maintenance.request'].search_count([
            ('create_date', '>=', datetime.combine(date_from, datetime.min.time())),
            ('create_date', '<=', datetime.combine(date_to, datetime.max.time())),
            ('state', 'not in', ['completed', 'cancelled'])
        ])
        maintenance_in_progress = self.env['hostel.maintenance.request'].search_count([
            ('create_date', '>=', datetime.combine(date_from, datetime.min.time())),
            ('create_date', '<=', datetime.combine(date_to, datetime.max.time())),
            ('state', '=', 'in_progress')
        ])
        maintenance_total = self.env['hostel.maintenance.request'].search_count([
            ('create_date', '>=', datetime.combine(date_from, datetime.min.time())),
            ('create_date', '<=', datetime.combine(date_to, datetime.max.time())),
        ])

        # Attendance on date_to (present) and in range
        attendance_today = self.env['hostel.student.attendance'].search_count([
            ('date', '=', date_to),
            ('status', '=', 'present')
        ])
        attendance_in_range = self.env['hostel.student.attendance'].search_count([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])

        # Revenue: paid = period overlapping [date_from, date_to]; outstanding = due by date_to
        invoices_paid = self.env['hostel.rent.invoice'].search([
            ('state', '=', 'paid'),
            ('period_start', '<=', date_to),
            ('period_end', '>=', date_from),
        ])
        revenue_paid = sum(invoices_paid.mapped('amount'))
        invoices_outstanding = self.env['hostel.rent.invoice'].search([
            ('state', 'in', ['invoiced', 'overdue']),
            ('due_date', '<=', date_to),
        ])
        revenue_outstanding = sum(invoices_outstanding.mapped('amount'))

        # Complaints: open, created in [date_from, date_to]
        complaints_open = self.env['hostel.complaint'].search_count([
            ('create_date', '>=', datetime.combine(date_from, datetime.min.time())),
            ('create_date', '<=', datetime.combine(date_to, datetime.max.time())),
            ('state', 'not in', ['resolved', 'closed', 'cancelled'])
        ])
        # Laundry: open, created in [date_from, date_to]
        laundry_open = self.env['hostel.laundry.request'].search_count([
            ('create_date', '>=', datetime.combine(date_from, datetime.min.time())),
            ('create_date', '<=', datetime.combine(date_to, datetime.max.time())),
            ('state', 'not in', ['completed', 'cancelled'])
        ])
        # Inspections: scheduled/in_progress with scheduled_date in [date_from, date_to]
        inspections_open = self.env['hostel.room.inspection'].search_count([
            ('state', 'in', ['scheduled', 'in_progress']),
            ('scheduled_date', '>=', date_from),
            ('scheduled_date', '<=', date_to),
        ])

        # Active announcements whose validity period overlaps [date_from, date_to]
        announcements_active = self.env['hostel.announcement'].search_count([
            ('is_active', '=', True),
            ('date_start', '<=', date_to),
            ('date_end', '>=', date_from),
        ])

        total_revenue = revenue_paid + revenue_outstanding
        collection_rate = (revenue_paid / total_revenue * 100) if total_revenue else 0.0

        # Optionally hide expiry highlights on dashboard
        show_expiry = ICP.get_str('sirita_mahad.dashboard_show_expiry_highlights', 'True') != 'False'
        if not show_expiry:
            upcoming_10 = 0
            upcoming_30 = 0

        return {
            'daily_checkin_count': checkins,
            'daily_contract_ending_count': contracts_ending,
            'active_students_count': active_students,
            'vacant_spaces_count': vacant_beds,
            'upcoming_30_days_count': upcoming_30,
            'upcoming_10_days_count': upcoming_10,
            'total_buildings': total_buildings,
            'total_rooms': total_rooms,
            'total_beds': total_beds,
            'occupancy_rate': round(occupancy_rate, 2),
            'visitor_today_count': visitor_today,
            'visitor_pending_count': visitor_pending,
            'visitor_in_range_count': visitor_in_range,
            'maintenance_open_count': maintenance_open,
            'maintenance_in_progress_count': maintenance_in_progress,
            'maintenance_total_count': maintenance_total,
            'attendance_today_count': attendance_today,
            'attendance_in_range_count': attendance_in_range,
            'revenue_paid': round(revenue_paid, 2),
            'revenue_outstanding': round(revenue_outstanding, 2),
            'collection_rate': round(collection_rate, 1),
            'complaints_open_count': complaints_open,
            'laundry_open_count': laundry_open,
            'inspections_open_count': inspections_open,
            'announcements_active_count': announcements_active,
            'date_from': date_from.isoformat() if date_from else None,
            'date_to': date_to.isoformat() if date_to else None,
        }

    def _get_empty_chart_data(self):
        """Return empty chart structure for frontend."""
        return {
            'occupancy_by_building': [],
            'revenue_monthly': [],
            'attendance_daily': [],
            'visitors_daily': [],
            'maintenance_by_state': [],
        }

    @api.model
    def get_chart_data(self, date_from=None, date_to=None):
        """Return chart data for occupancy, revenue, attendance, visitors, maintenance."""
        try:
            return self._get_chart_data_impl(date_from, date_to)
        except Exception:
            return self._get_empty_chart_data()

    @api.model
    def _get_chart_data_impl(self, date_from=None, date_to=None):
        today = fields.Date.today()
        date_from = _parse_date(date_from) or (today - timedelta(days=30))
        date_to = _parse_date(date_to) or today

        # Occupancy by building as of date_to (respects date filter; no filter = last 30 days → date_to = today)
        contracts_on_date = self.env['hostel.contract'].search([
            ('state', '=', 'active'),
            ('contract_start', '<=', date_to),
            ('contract_end', '>=', date_to),
        ])
        occupied_bed_ids = set(contracts_on_date.mapped('bed_id').ids)
        buildings = self.env['hostel.building'].search([('active', '=', True)], order='name')
        occupancy_by_building = []
        for b in buildings:
            beds = self.env['hostel.bed'].search([
                ('room_id.unit_id.building_id', '=', b.id),
                ('is_active', '=', True),
                ('active', '=', True)
            ])
            total = len(beds)
            occupied = len([bid for bid in beds.ids if bid in occupied_bed_ids])
            pct = (occupied / total * 100) if total else 0
            occupancy_by_building.append({
                'name': b.name,
                'value': occupied,
                'total': total,
                'percentage': round(pct, 1),
            })

        # Revenue: 6 months ending on date_to (respects date filter)
        revenue_monthly = []
        for i in range(5, -1, -1):
            month_start = (date_to + relativedelta(months=-i)).replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
            invs = self.env['hostel.rent.invoice'].search([
                ('state', '=', 'paid'),
                ('period_start', '>=', month_start),
                ('period_start', '<=', month_end),
            ])
            revenue_monthly.append({
                'label': month_start.strftime('%b %Y'),
                'value': round(sum(invs.mapped('amount')), 2),
            })
        max_rev = max((x['value'] for x in revenue_monthly), default=1) or 1
        for x in revenue_monthly:
            x['percentage'] = round(100.0 * x['value'] / max_rev, 1)

        # Attendance (7d): 7 days ending on date_to (respects date filter "To")
        attendance_daily = []
        for i in range(6, -1, -1):
            d = date_to - timedelta(days=i)
            cnt = self.env['hostel.student.attendance'].search_count([
                ('date', '=', d),
                ('status', '=', 'present')
            ])
            attendance_daily.append({'label': d.strftime('%a %d'), 'value': cnt})
        max_att = max((x['value'] for x in attendance_daily), default=1) or 1
        for x in attendance_daily:
            x['percentage'] = round(100.0 * x['value'] / max_att, 1)

        # Visitors (7d): 7 days ending on date_to (respects date filter "To")
        visitors_daily = []
        for i in range(6, -1, -1):
            d = date_to - timedelta(days=i)
            cnt = self.env['hostel.visitor'].search_count([
                ('visit_datetime', '>=', datetime.combine(d, datetime.min.time())),
                ('visit_datetime', '<=', datetime.combine(d, datetime.max.time())),
            ])
            visitors_daily.append({'label': d.strftime('%a %d'), 'value': cnt})
        max_vis = max((x['value'] for x in visitors_daily), default=1) or 1
        for x in visitors_daily:
            x['percentage'] = round(100.0 * x['value'] / max_vis, 1)

        # Maintenance by state
        Maintenance = self.env['hostel.maintenance.request']
        maintenance_by_state = [
            {'label': 'Open', 'value': Maintenance.search_count([('state', 'not in', ['completed', 'cancelled'])])},
            {'label': 'In Progress', 'value': Maintenance.search_count([('state', '=', 'in_progress')])},
            {'label': 'Completed', 'value': Maintenance.search_count([('state', '=', 'completed')])},
        ]

        return {
            'occupancy_by_building': occupancy_by_building,
            'revenue_monthly': revenue_monthly,
            'attendance_daily': attendance_daily,
            'visitors_daily': visitors_daily,
            'maintenance_by_state': maintenance_by_state,
        }
