# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HostelHelpController(http.Controller):

    @http.route('/hostel/help', type='http', auth='user', website=False)
    def help_page(self, **kwargs):
        return request.render('sirita_mahad.hostel_help_page', {})
