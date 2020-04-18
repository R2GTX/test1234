# -*- coding: utf-8 -*-

import itertools
import psycopg2

from odoo.addons import decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from odoo.tools import pycompat


class ProductTemplateMidav(models.Model):
    _inherit = "product.template"

    net_weight = fields.Float(string=_("Net weight"), required=False,digits=(20, 3))
    pne_weight  = fields.Float(string=_("PNE"), required=False,digits=(20, 3))
    gross_weight = fields.Float(string=_("Gross weight"), required=False,digits=(20, 3))
    gross_weight_nu = fields.Float(string=_("Gross Weight E"), required=False,digits=(20, 3))
    code_sh = fields.Many2one('sh.code', string=_("Code SH"))
    sid = fields.Char(string=_("SID"))
    dimensions = fields.Char(string=_('Dimensions'))
    cans = fields.Many2one('midav.cans', string=_('Cans'))
    midav_empty_cans_id = fields.Many2one('midav.empty.cans', string=_('Reference UVC (box)'))
    midav_fish_id = fields.Many2one('midav.fish', string=_('Fish'))
    midav_preparation_id = fields.Many2one('midav.preparation', string=_('Preparation')) # rverse maybe
    midav_jutage_id = fields.Many2one('midav.jutage', string=_('Jutage'))
    #midav_cases_id = fields.Many2one('midav.cases', string=_('Cases'))
    midav_cartons_id = fields.Many2one('midav.cartons', string=_('Cartons'))
    midav_tag_id = fields.Many2one('midav.tag', string=_('Tag'))
    #midav_stickers_btes_id = fields.Many2one('midav.stickers.btes', string=_("References Stickers/Btes"))
    #midav_stickers_barq_id = fields.Many2one('midav.stickers.barq', string=_("References Stickers/Barq"))
    brand = fields.Many2one('midav.brand', string=_('Brand'))
    is_codif = fields.Boolean(string = _("Use codification"), default=True)
    name_sci = fields.Many2one('scientific.name',string=_('Scientific Name'))
    description_commodity_id = fields.Many2one("midav.description.commodity", string=_("Description of commodity"))
    company_id = fields.Many2one(
        'res.company', 'Company')

    @api.onchange('midav_empty_cans_id',
                  'midav_fish_id',
                  'midav_preparation_id',
                  'midav_jutage_id',
                  'is_codif')
    def change_properties(self):
        for res in self:
            if res.is_codif:
                code, designation = "", ""
                if res.midav_empty_cans_id:
                    code += " " + (res.midav_empty_cans_id.code or "")
                    designation += " " + (res.midav_empty_cans_id.name or "")
                if res.midav_fish_id:
                    code += " " + (res.midav_fish_id.code or "")
                    designation += " " + (res.midav_fish_id.name or "")
                if res.midav_preparation_id:
                    code += " " + (res.midav_preparation_id.code or "")
                    designation += " " + (res.midav_preparation_id.name or "")
                if res.midav_jutage_id:
                    code += " " + (res.midav_jutage_id.code or "")
                    designation += " " + (res.midav_jutage_id.name or "")

                res.default_code = code
                res.name = designation

    def del_company(self):
        rec_ids = self.env['product.template'].search([])
        for r in rec_ids:
            r.company_id = False


class ProductProductMidav(models.Model):
    _inherit = "product.product"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        context = self._context or {}
        sale_order_id = context.get('search_product_sale_order', False)
        get_options_op = context.get('get_options_op', False)

        if sale_order_id:
            sale_order_id = self.env['sale.order'].search([('id','=',sale_order_id)])[0]
            products = []
            if get_options_op:
                for sl in sale_order_id.options:
                    products.append(sl.product_id.id)
            else:
                for sl in sale_order_id.order_line:
                    products.append(sl.product_id.id)
            new_args = [l for l in args if l[0]!='id']
            args = new_args + [('id', 'in', products)]
        return super(ProductProductMidav, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                    access_rights_uid=access_rights_uid)

    @api.model
    def create(self, vals):
        res = super(ProductProductMidav, self).create(vals)
        if res.is_codif:
            code, designation = "", ""
            if res.midav_empty_cans_id:
                code += " " + (res.midav_empty_cans_id.code or "")
                designation += " " + (res.midav_empty_cans_id.name or "")
            if res.midav_fish_id:
                code += " " + (res.midav_fish_id.code or "")
                designation += " " + (res.midav_fish_id.name or "")
            if res.midav_preparation_id:
                code += " " + (res.midav_preparation_id.code or "")
                designation += " " + (res.midav_preparation_id.name or "")
            if res.midav_jutage_id:
                code += " " + (res.midav_jutage_id.code or "")
                designation += " " + (res.midav_jutage_id.name or "")

            res.write({'default_code': code,
                       'name': designation,
                       })
        return res



class ProductUomMidav(models.Model):
    _inherit = "product.uom"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        context = self._context or {}
        new_args = [l for l in args if l[0] != 'category_id']
        product_id = context.get('search_uom_product', False)
        if product_id:
            product_id = self.env['product.product'].search([('id','=', product_id)])[0]

            args = new_args + [('category_id','=', product_id.uom_id and product_id.uom_id.category_id.id)]
        return super(ProductUomMidav, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                    access_rights_uid=access_rights_uid)

    pne_uom_weight = fields.Float(string=_('Dry weight'))
    pn_uom_weight = fields.Float(string=_('Net Weight'))


class MidavCans(models.Model):
    _name="midav.cans"

    name = fields.Char(string=_('Name'), required=True)

class MidavDescriptionCommodity(models.Model):
    _name='midav.description.commodity'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")