# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp

class ResCompanyMidav(models.Model):
    _inherit = "res.company"

    approval = fields.Char(string=_("N° Approval"))
    fda = fields.Char(string=_('N° FCE FDA'))
    show_in_report = fields.Boolean(string=_("Show in report"), default=False)