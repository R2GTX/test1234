# -*- coding: utf-8 -*-
from .amount_to_text_fr import amount_to_text_fr

from datetime import datetime, date, timedelta
from itertools import groupby
from pprint import pprint
import math

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp


class SaleOrderMidav(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if line.layout_category_id.ligne_pro_format:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    to_text = fields.Text(string='Montant total en lettre',
                                 store=True, readonly=True, compute='_amount_in_words')
    @api.one
    @api.depends('amount_total')
    def _amount_in_words(self):
        self.to_text = amount_to_text_fr(self.amount_total, self.currency_id.currency_unit_label)

    @api.multi
    def _compute_nb_sale_pickings(self):
        """"""
        for so in self:
            so.nb_sale_pickings = len(so.sale_picking_ids or "")

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_letter(self):
        """"""
        for so in self:
            if so.currency_id:
                so.total_amount_letter = so.currency_id.amount_to_text(so.amount_total)

    def amount_letter(self, price):
        """"""
        for so in self:
            frac, whole = math.modf(price)
            print("========================")
            print("fraq = ", round(frac,2))
            print("whole = ",whole)
            print("========================")
            price = whole+round(frac,2)
            print("price = ",price)
            print (so.currency_id.amount_to_text(price))
            print("========================")
            return so.currency_id.amount_to_text(price)
    def _default_country(self):
        return self.env["res.country"].search([("id", "=",136)])
    bank_id = fields.Many2one("res.partner.bank", string=_("Customer Bank"))
    commodity_destination = fields.Char(string=_('Commodity Destination'))
    nb_port = fields.Char(string=_('Port Number'))
    ref_po = fields.Char(string=_("Ref. order"))
    nb_sale_pickings = fields.Integer(string=_("Nb sale pickings"), default=0, compute=_compute_nb_sale_pickings)
    payment_mode_id = fields.Many2one("account.journal", string=_("Payment mode"))
    total_amount_letter = fields.Char(string=_("Total amount letter"), compute=_compute_amount_letter)
    special_mark = fields.Char(string=_("Special Marking"))
    incoterm_id = fields.Many2one('stock.incoterms', string=_('Incoterm'))
    sale_picking_ids = fields.One2many("midav.sale.picking", "sale_order_id", string=_("Sale pickings"))
    origin_product = fields.Many2one("res.country", default=_default_country)

    @api.multi
    def sum_qty(self):
        """"""
        total_qty = 0.0
        for line in self.order_line:
            if line.layout_category_id.ligne_pro_format:
                if not line.layout_category_id.count_qty:
                    total_qty += line.product_uom_qty
        return total_qty
        """ Add 15 days to date order to compute validity date"""
        for order in self:
            if order.date_order:
                d_order = str(order.date_order).split(" ")[0]
                new_date = (datetime.strptime(d_order, '%Y-%m-%d') + timedelta(days=15))
                order.validity_date = new_date

    @api.multi
    def action_view_sale_pickings(self):
        """"""
        action = self.env.ref("midav_base.action_sale_picking").read()[0]
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {'default_sale_order_id': self.id}
        return action

    @api.multi
    def action_confirm(self):
        """"""
        res = super(SaleOrderMidav, self).action_confirm()
        msp = self.env['midav.sale.picking'].create({
            'sale_order_id': self.id,
        })
        mss = self.env['midav.sale.picking'].create({
            'sale_order_id': self.id,
            'public_op': True,
        })
        return res

    @api.onchange('partner_id', 'company_id')
    def _on_change_bank_id(self):
        """"""
        banks = self.env['res.partner.bank'].search([('company_id', '=', self.company_id.id)])
        dbanks = [b.id for b in banks]
        res = {
            'domain': {
                'bank_id': [('id', 'in', dbanks)],
            },
        }
        return res

    @api.multi
    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
            # If last added category induced a pagebreak, this one will be on a new page

            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])
            # Append category to current report page
            if category.ligne_pro_format:
                report_pages[-1].append({
                    'name': category and category.name or _('Uncategorized'),
                    'subtotal': category and category.subtotal,
                    'pagebreak': category and category.pagebreak,
                    'lines': list(lines)
                })
        return report_pages

    def get_subtotal(self):
        subtotal = amount_tax = 0.0
        for i in self.order_lines_layouted()[0]:
            for l in i["lines"]:
                subtotal += l.price_subtotal
                amount_tax += l.price_tax
        total = subtotal+amount_tax
        return subtotal, total


    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            if line.layout_category_id.ligne_pro_format:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=self.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]
        return res

    def date_emission(self):
        now = datetime.now().strftime("%d/%m/%Y")
        return now

class SaleOrderLineMidav(models.Model):
    _inherit = "sale.order.line"

    # _sql_constraints = [
    #     ('orderLine_product_uniq', 'unique (product_id,order_id)', _('The product of the sale order must be unique !'))
    # ]

    attachment_ids = fields.Many2many("ir.attachment", string="Attachment")
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal',digits=0, readonly=True, store=True)

    def update_name(self):
        for o in self:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
            )
            name = product.name_get()[0][1]
            if product.description_sale:
                name += '\n' + product.description_sale
            o.name = name
            if o.name and ']' in o.name:
                o.name = o.name.split("]")[1]
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLineMidav, self).product_id_change()
        for o in self:
            if o.name and ']' in o.name:
                o.name = o.name.split("]")[1]
        return res

