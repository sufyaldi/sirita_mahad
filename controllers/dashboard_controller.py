# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class HostelDashboardController(http.Controller):
    """Controller for Hostel Dashboard - same pattern as helpdesk (form view + JSON routes)."""

    @http.route('/hostel/dashboard/statistics', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_statistics(self, date_from=None, date_to=None, **kwargs):
        """Get dashboard statistics (KPIs). Calls hostel.dashboard get_statistics."""
        try:
            Dashboard = request.env['hostel.dashboard']
            result = Dashboard.get_statistics(date_from=date_from, date_to=date_to)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/hostel/dashboard/chart-data', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_chart_data(self, date_from=None, date_to=None, **kwargs):
        """Get chart data. Calls hostel.dashboard get_chart_data."""
        try:
            Dashboard = request.env['hostel.dashboard']
            result = Dashboard.get_chart_data(date_from=date_from, date_to=date_to)
            return {'success': True, 'data': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
