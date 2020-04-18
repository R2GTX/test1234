# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import api, fields, models, _

class TaxMidav(models.Model):
    _inherit = "account.tax"

    tax_code = fields.Integer(string=_('Tax Code'))