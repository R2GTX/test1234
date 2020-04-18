# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp


class ResCountryMidav(models.Model):
    _inherit = "res.country"

    show_sid = fields.Boolean(string=_('Show SID Number for Product'))
    fce_fcd = fields.Char('FCE-FDA N°')