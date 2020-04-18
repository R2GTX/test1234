# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import api, fields, models, _

class SaleLayoutCategoryMidav(models.Model):
    _inherit = "sale.layout_category"

    count_qty = fields.Boolean(string=_('Count Quantity'))

    sh_code_pro_format = fields.Boolean(string=_('Pro Format'), default=True)
    sh_code_pro_format_usa = fields.Boolean(string=_('Pro Format USA'), default=True)
    sh_code_healt_certificate = fields.Boolean(string=_('Healt Certificate'), default=True)
    sh_code_r3 = fields.Boolean(string=_('R3'))
    sh_code_r4 = fields.Boolean(string=_('R4'))

    ligne_pro_format = fields.Boolean(string=_('Pro Format'), default=True)
    ligne_r2 = fields.Boolean(string=_('R2'))
    ligne_r3 = fields.Boolean(string=_('R3'))
    ligne_r4 = fields.Boolean(string=_('R4'))

    sid_pro_format_usa = fields.Boolean(string=_('SID USA'), default=True)
    dimension_pro_format_usa = fields.Boolean(string=_('Dimensions USA'), default=True)
    code_barre_pro_format_usa = fields.Boolean(string=_('Code Barre USA'), default=True)
