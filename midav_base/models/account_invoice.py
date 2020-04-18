# -*- coding: utf-8 -*-
from .amount_to_text_fr import amount_to_text_fr
from datetime import datetime, date, timedelta
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp
from functools import partial
from odoo.tools.misc import formatLang


class AccountInvoiceMidav(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('amount_total')
    def _amount_in_words(self):
        self.to_text = amount_to_text_fr(self.amount_total,self.currency_id.currency_unit_label)

    to_text = fields.Text(string='Montant total en lettre',
                                 store=True, readonly=True, compute='_amount_in_words')

    @api.multi
    @api.depends("amount_total")
    def _compute_amount_letter(self):
        """"""

        for invoice in self:

            invoice.total_amount_letter = invoice.currency_id.amount_to_text(invoice.amount_total)

    @api.multi
    def amount_letter(self, price):
        for invoice in self:
            return invoice.currency_id.amount_to_text(price)

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        fmt = partial(formatLang, self.with_context(lang=self.partner_id.lang).env)
        res = {}
        for line in self.tax_line_ids:
            res.setdefault(line.tax_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
            res[line.tax_id.tax_group_id]['amount'] += line.amount
            res[line.tax_id.tax_group_id]['base'] += line.base
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(
            r[0].name, r[1]['amount'], r[1]['base'],
            fmt(r[1]['amount']), fmt(r[1]['base']),
        ) for r in res]
        return res




    @api.depends('origin')
    def _compute_midav_order(self):
        for o in self:
            o.midav_order_id = False
            if o.origin:
                sos = self.env["sale.order"].search([('name', '=', o.origin)])
                if sos:
                    o.midav_order_id = sos[0]

    ref_fda = fields.Char(string=_("Ref FDA"))
    show_in_report = fields.Boolean(string=_("Show in invoice"), default=False)
    sale_picking_id = fields.Many2one("midav.sale.picking", string=_("Sale Picking"))
    total_amount_letter = fields.Char(string=_("Total amount letter"), compute=_compute_amount_letter)
    order_id = fields.Many2one('sale.order', string=_('Order N'), related='sale_picking_id.sale_order_id')
    midav_order_id = fields.Many2one('sale.order', string=_('Order M'), compute=_compute_midav_order)

    @api.multi
    def get_product_suggested_op(self):
        or_public = \
        self.env['midav.sale.picking'].search([('sale_order_id', '=', self.order_id.id), ('public_op', '=', True)])[0]
        return or_public

    @api.multi
    def sum_qty(self):
        """"""
        total_qty = 0.0
        for line in self.invoice_line_ids:
            #if line.layout_category_id.ligne_pro_format:
            #    if not line.layout_category_id.count_qty:
            total_qty += line.quantity
        return total_qty
