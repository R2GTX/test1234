# -*- coding: utf-8 -*-
# OKzm/@/0815
from datetime import datetime, timedelta
from itertools import groupby
from dateutil import parser
import math

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class MidavPackagingType(models.Model):
    _name = 'midav.packaging.type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    company_id = fields.Many2one('res.company', string=_('Company'))


class SalePickingMidav(models.Model):
    _name = 'midav.sale.picking'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Sale Picking"
    _order = 'date desc, id desc'

    def _count_operations(self):
        """"""
        for sp in self:
            sp.operations_count = len(sp.sale_operation_ids or "")

    def _count_invoices(self):
        """"""
        for sp in self:
            sp.invoice_count = len(sp.account_invoice_id or "")

    @api.depends('sale_picking_line_ids', 'sale_picking_line_ids.pn', 'sale_picking_line_ids.pne',
                 'sale_picking_line_ids.nbr_carton')
    def _compute_weights(self):
        """"""
        for sp in self:
            # sp.gross_weight = 0.0
            for spl in sp.sale_picking_line_ids:
                # sp.gross_weight += (spl.product_id.gross_weight or 0.0) * (spl.qty_done or 0.0)
                # sp.gross_weight_nu += (spl.product_id.gross_weight_nu or 0.0) * (spl.qty_done or 0.0)
                sp.net_weight += (spl.pn or 0.0)
                sp.pne_weight += (spl.pne or 0.0)
                sp.nb_colis += spl.nbr_carton or 0

    name = fields.Char(string="N° Order", readonly=True)
    departure_date = fields.Date(string=_('Date departure'))
    public_op = fields.Boolean(string=_('Public Order Preparation'))
    transit_document = fields.Many2one('midav.document', string=_('Transit Document'))
    commodity_nature = fields.Char(string=_('Commodity Nature'))
    treatement_type = fields.Char(string=_('Treatement Type'))
    process_type = fields.Char(string=_('Process Type'))
    usa_print = fields.Boolean(string=_('USA Version of the Report'))
    # scientific_name = fields.Char(string=_("Species (Scientific Name)"))
    date = fields.Datetime(default=fields.Datetime.now, required=True, string=_("Date"))
    sale_picking_line_ids = fields.One2many('midav.sale.picking.line', 'sale_picking_id', string=_("Sale Picking Line"))
    sale_operation_ids = fields.One2many('midav.sale.operation', 'sale_picking_id', string=_("Sale operations"))
    sale_order_id = fields.Many2one('sale.order', string=_("Sale order"), readonly=True, ondelete='restrict')
    client_id = fields.Many2one('res.partner', related="sale_order_id.partner_id", string=_('Client'))
    company_id = fields.Many2one("res.company", related="sale_order_id.company_id")
    quality_notes = fields.Text(_('Quality Notes'))
    operations_count = fields.Integer(string=_("Operations count"), default=0, compute=_count_operations)
    account_invoice_id = fields.Many2one("account.invoice", string='Invoices')
    invoice_count = fields.Integer(string=_("Invoices count"), default=0, compute=_count_invoices)
    first_notify = fields.Many2one('res.partner', string=_('First Notify'))
    second_notify = fields.Many2one('res.partner', string=_('Second Notify'))
    gross_weight = fields.Float(string=_("Gross weight amount"),digits=(20, 3), store=True)
    gross_weight_nu = fields.Float(string=_("Gross weight nu amount"),digits=(20, 3))
    net_weight = fields.Float(string=_("Net weight amount"),digits=(20, 3), compute=_compute_weights)
    pne_weight = fields.Float(string=_("PNE amount"),digits=(20, 3), compute=_compute_weights)
    booking_nbr = fields.Char(string=_('N° Booking'))
    agreement_nbr = fields.Char(string=_('N° Agreement'))
    escale_nbr = fields.Char(string=_('N° Escale'))
    midav_seq_date = fields.Date(string=_('Sequence Date'))
    nb_colis = fields.Integer(string="NB colis", compute=_compute_weights)
    state = fields.Selection([
        ('draft', _('Draft')),
        ('progress', _('Prepare')),
        ('packing', _('Packing')),
        ('quality_check', _('Quality check')),
        ('done', _('Done')),
        ('improper_quality', _('Improper Quality')),
    ], string=_('State'), readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    # transit order
    charger = fields.Many2one('res.partner', string=_('Charger'))
    consignee = fields.Many2one('res.partner', string=_('Consignee'))
    transporter = fields.Many2one('res.partner', string=_('Transporter'))
    date_transit = fields.Date(string='Date')
    dest_port = fields.Char(string='Destination Port')
    marquage_lc = fields.Char(string=_('Marquage Colisage Liste'))
    marquage_or = fields.Char(string=_('Marquage Preparation Order'))
    board_port = fields.Char(string='Board Port')
    navigation_comp = fields.Char(string="Navigation Company")
    lading = fields.Many2one('midav.lading', string="lading")
    bill_of_lading = fields.Char(string="Bill of Lading")
    forwarding_agent = fields.Char(string='Forwarding agent')
    contact_ids = fields.Many2many("res.partner")

    # health certificate
    num_certificate = fields.Char(string="N°")
    means_of_conveyance = fields.Selection([
        ('aeroplane', 'Aeroplane'),
        ('ship', 'Ship'),
        ('railway_wagon', 'Railway wagon'),
        ('road_vehicle', 'Road vehicle'),
        ('other', 'Other'),
    ], string="Means of conveyance", default='ship')
    brand_certificate = fields.Many2one("midav.brand", string=_("Brand"))
    product_temperature = fields.Selection([('ambient', 'Ambient'),
                                            ('chilled', 'Chilled'),
                                            ('forzen', 'Frozen'), ], string=_("Temperature of product"),
                                           default='ambient')
    human_consumption = fields.Boolean(_("Human consumption"), default=False)
    imp_admission = fields.Boolean(_("For import or admission into EU"), default=False)
    packaging_type_id = fields.Many2one("midav.packaging.type", string=_("Packaging Type"))

    # colisage
    codification_1 = fields.Char(string="Code 1")
    codification_2 = fields.Char(string="Code 2")
    codification_3 = fields.Char(string="Code 3")
    codification_4 = fields.Char(string="Code 4")

    @api.model
    def create(self, values):
        """"""
        if not values.get("sale_order_id", False):
            values['sale_order_id'] = self._context.get("default_sale_order_id", False)
        vals = super(SalePickingMidav, self).create(values)
        vals.name = self.env['ir.sequence'].next_by_code('midav.sale.picking') or _('New')
        return vals

    @api.multi
    def action_draft(self):
        """"""
        self.write({
            'state': 'draft',
        })

    @api.multi
    def action_progress(self):
        """"""
        self.write({
            'state': 'progress',
        })
        self.generate_operation()

    @api.multi
    def generate_operation(self):
        for sp in self:
            operation = self.env['midav.sale.operation'].create({
                'sale_picking_id': sp.id,
            })
            operation.generate_lines_from_sale_picking()

    @api.multi
    def action_in_quality_check(self):
        """"""
        self.write({
            'state': 'quality_check',
        })

    @api.multi
    def action_done(self):
        """"""
        self.write({
            'state': 'done',
        })

    @api.multi
    def action_undone(self):
        """"""
        self.write({
            'state': 'improper_quality',
        })

    @api.multi
    def action_packing(self):
        """"""
        self.write({
            'state': 'packing',
        })

    @api.multi
    def action_view_sale_operations(self):
        """"""
        action = self.env.ref("midav_base.action_sale_operation").read()[0]
        action['domain'] = [('sale_picking_id', '=', self.id)]
        return action

    @api.multi
    def action_view_invoice(self):
        """"""
        action = self.env.ref("midav_base.action_invoice_customer_tree1").read()[0]
        action['domain'] = [('type', '=', 'out_invoice'), ('sale_picking_id', '=', self.id)]
        return action

    @api.multi
    def action_print_packing_list(self):
        """"""
        data = {}
        return self.env.ref('midav_base.action_report_list_colisage').report_action(self,
                                                                                    data=data,
                                                                                    config=False)

    @api.multi
    def action_billing(self):
        for sp in self:
            sp.generate_invoice()

    @api.one
    def generate_invoice(self):
        """Generate invoice from sale picking"""
        if self.state == 'done' and self.sale_picking_line_ids:
            invoice = self.env['account.invoice'].create({
                'partner_id': self.sale_order_id.partner_invoice_id.id,
                'partner_shipping_id': self.sale_order_id.partner_shipping_id.id,
                'sale_picking_id': self.id,
            })
            invoice._onchange_partner_id()
            invoice.write({
                'payment_term_id': self.sale_order_id.payment_term_id.id if self.sale_order_id else False,
                'origin': self.name,
                'currency_id': self.sale_order_id.currency_id.id if self.sale_order_id else False,
            })
            for product_id, lines in groupby(self.sale_picking_line_ids, lambda l: l.product_id):
                lines = list(lines)
                # AMH#-- product uom (traitment) ...
                qty = sum([l.nbr_carton for l in lines])
                result = self.to_create_invoice_line(invoice, product_id)
                if len(result) == 1:
                    result = result[0]
                invoice_line = self.env['account.invoice.line'].create({
                    'invoice_id': invoice.id,
                    'product_id': product_id.id,
                    'quantity': qty,
                    'name': result['name'],
                    'uom_id': result['uom_id'],
                    'account_id': result['account_id'],
                    'price_unit': result['price_unit'],
                    'invoice_line_tax_ids': [(6, 0, result['taxes'])],
                })
                invoice_line._onchange_product_id()
                invoice_line.write({
                    'name': result['name'],
                    'uom_id': result['uom_id'],
                    'price_unit': result['price_unit'],
                    'invoice_line_tax_ids': [(6, 0, result['taxes'])],
                })
            self.account_invoice_id = invoice

    @api.one
    def to_create_invoice_line(self, invoice_id, product_id):
        """ Needed to create an invoice"""
        domain = {
            'price_unit': 0.0,
            'uom_id': False,
        }
        if not invoice_id:
            return

        part = invoice_id.partner_id
        fpos = invoice_id.fiscal_position_id
        company = invoice_id.company_id
        currency = invoice_id.currency_id
        type = invoice_id.type
        uom_id = False

        so_line = [soli for soli in self.sale_order_id.order_line if soli.product_id.id == product_id.id]
        so_line = so_line[0] if len(so_line) else False

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner!'),
            }
            return {'warning': warning}

        if not product_id:
            if type not in ('in_invoice', 'in_refund'):
                domain['price_unit'] = 0.0
            domain['uom_id'] = False

        else:
            # Use the purchase uom by default
            domain['uom_id'] = product_id.uom_po_id.id
            uom_id = product_id.uom_po_id

            if part.lang:
                product = product_id.with_context(lang=part.lang)
            else:
                product = product_id

            domain['name'] = product.partner_ref
            account = self.env['account.invoice.line'].get_invoice_line_account(type, product, fpos, company)
            if account:
                domain['account_id'] = account.id
            # self.env['account.invoice.line']._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    domain['name'] += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    domain['name'] += '\n' + product.description_sale

            if not uom_id or product.uom_id.category_id.id != uom_id.category_id.id:
                uom_id = product.uom_id
                domain['uom_id'] = product.uom_id.id

            if company and currency:
                if company.currency_id != currency:
                    domain['price_unit'] = domain['price_unit'] * currency.with_context(
                        dict(self._context or {}, date=invoice_id.date_invoice)).rate

                if uom_id and uom_id.id != product.uom_id.id:
                    domain['price_unit'] = product.uom_id._compute_price(domain['price_unit'], uom_id)
            if so_line:
                domain['name'] = so_line.name
                domain['price_unit'] = so_line.price_unit
                domain['uom_id'] = so_line.product_uom.id
                domain['taxes'] = [t.id for t in so_line.tax_id]
        return domain

    @api.one
    def get_lines_by_product(self):
        res = []
        if self.sale_picking_line_ids:
            for p, lns in groupby(self.sale_picking_line_ids, lambda r: r.product_id):
                res.append([p, list(lns)])
        return res
    
    @api.multi
    def get_lines_by_product2(self):
        list_lines = []
        product_ids = list(set([line.product_id.id for line in self.sale_picking_line_ids]))
        for l in product_ids:
            list_lines.append(self.sale_picking_line_ids.filtered(lambda x : x.product_id.id == l))

        return list_lines

    @api.one
    def get_merchandise_by_sh(self):
        res = []
        if self.sale_picking_line_ids:
            for p, lns in groupby(self.sale_picking_line_ids, lambda r: r.product_id.code_sh):
                res.append([p, list(lns)])
        return res

    @api.one
    def get_unique_tc_lines(self):
        res = set()
        if self.sale_picking_line_ids:
            for spl in self.sale_picking_line_ids:
                if spl.sead_tc_id:
                    res.add(spl.sead_tc_id)

        return list(res)

    @api.one
    def get_unique_desc_commodity(self):
        res = set()
        if self.sale_picking_line_ids:
            for spl in self.sale_picking_line_ids:
                if spl.product_id.description_commodity_id:
                    res.add(spl.product_id.description_commodity_id.name)

        return list(res)

    @api.one
    def get_unique_sh_codes(self):
        res = set()

        if self.sale_picking_line_ids:
            for spl in self.sale_picking_line_ids:
                if spl.product_id.code_sh and spl.layout_category_id and spl.layout_category_id.sh_code_healt_certificate:
                    res.add(spl.product_id.code_sh.name)

        return list(res)

    @api.one
    def get_unique_number_of_packages(self):
        res = list()
        if self.sale_picking_line_ids:
            for uom_packing_id, lns in groupby(self.sale_picking_line_ids, lambda r: r.uom_packing_id):
                nb_colis = sum([line.nbr_carton for line in list(lns)])
                res.append(str(nb_colis or 0) + ' ' + 'cartons ')
            for sp in self:
                sp.gross_weight = 0.0
                for spl in sp.sale_picking_line_ids:
                    # sp.gross_weight += (spl.product_id.gross_weight or 0.0) * (spl.qty_done or 0.0)
                    # sp.gross_weight_nu += (spl.product_id.gross_weight_nu or 0.0) * (spl.qty_done or 0.0)
                    sp.net_weight += (spl.pn or 0.0)
                    sp.pne_weight += (spl.pne or 0.0)
        return res

    @api.one
    def get_unique_number_of_packages(self):
        qty = 0.0
        if self.sale_picking_line_ids:
            # for uom_packing_id, lns in groupby(self.sale_picking_line_ids, lambda r: r.uom_packing_id):
            #     nb_colis = sum([line.nbr_carton for line in list(lns)])
            #     res.append(str(nb_colis or 0) + ' ' + 'cartons ')
            # for sp in self:
            #     sp.gross_weight = 0.0
            #     for spl in sp.sale_picking_line_ids:
            #         # sp.gross_weight += (spl.product_id.gross_weight or 0.0) * (spl.qty_done or 0.0)
            #         # sp.gross_weight_nu += (spl.product_id.gross_weight_nu or 0.0) * (spl.qty_done or 0.0)
            #         sp.net_weight += (spl.pn or 0.0)
            #         sp.pne_weight += (spl.pne or 0.0)

            qty = sum([line.nbr_carton for line in self.sale_picking_line_ids])
            res = str(int(qty) or 0) + ' ' + 'cartons '
        return res

    @api.multi
    def calcul_gross_weight(self):
        total_gross = 0.0
        total_gross_nu = 0.0
        for line in self.sale_picking_line_ids:
            total_gross += line.qty_done * line.product_id.gross_weight
            total_gross_nu += line.qty_done * line.product_id.gross_weight_nu
        self.gross_weight = total_gross
        self.gross_weight_nu = total_gross_nu

    @api.multi
    def get_seat_tc(self):
        seal_tc_ids = [line.sead_tc_id.id for line in self.sale_picking_line_ids]
        seal_ids = self.env['midav.sead.tc'].search([('id', 'in', list(set(seal_tc_ids)))])
        return seal_ids

    def get_month(self, m):
        months = {
            "January": "Janvier",
            "February": "Février",
            "March": "Mars",
            "April": "Avril",
            "May": "Mai",
            "June": "Juin",
            "July": "Juillet",
            "August": "Aout",
            "September": "Septembre",
            "October": "Octobre",
            "November": "Novembre",
            "December": "Décembre",
        }
        return months[m]



    @api.multi
    def group_by_shcode(self):
        list_lines = []
        seal_tc_ids = list(set([line.product_id.code_sh.id for line in self.sale_picking_line_ids]))
        for l in seal_tc_ids:
            # list_lines.append(self.sale_picking_line_ids.filtered(lambda x : x.sh_code.id == l))

            list_lines.append(sorted(self.sale_picking_line_ids.filtered(lambda x: x.sh_code.id == l),
                                     key=lambda x: (x.product_id.default_code, x.production_date)))

        return list_lines

    @api.multi
    def group_by_shcode2(self):
        list_lines = []
        seal_tc_ids = list(set([line.product_id.code_sh.id for line in self.sale_picking_line_ids]))
        for l in seal_tc_ids:
            # list_lines.append(self.sale_picking_line_ids.filtered(lambda x : x.sh_code.id == l))
            sous_list = sorted(self.sale_picking_line_ids.filtered(lambda x: x.sh_code.id == l),
                                     key=lambda x: (x.product_id.default_code, x.production_date))
            glist = []

            for key, l in groupby(sous_list, lambda l: (l.lot_code_finale[0:6], l.product_id)):

                l = list(l)
                print(key, " : ", [x for x in l])
                # print(len(l[0]))
                slist = []
                slist.append(key[1].brand.name or '')
                slist.append(key[0] or '')
                slist.append(key[1].barcode or '')
                slist.append(l[0].lot_code or '')
                slist.append(key[1].name if self.public_op else key[1].midav_empty_cans_id.code or '')
                slist.append(l[0].mould.name or '')
                slist.append(key[1].description_commodity_id.name or '')
                slist.append(key[1].code_sh.name or '')
                slist.append(sum([z.nbr_carton for z in l]) or 0)
                my_date = parser.parse(l[0].production_date)
                proper_date_string = my_date.strftime('%d-%m-%Y')
                slist.append(proper_date_string or '')
                my_date = parser.parse(l[0].lapsing_date)
                proper_date_string = my_date.strftime('%d-%m-%Y')
                slist.append(proper_date_string or '')

                slist.append(sum([z.gross_wei for z in l]) or 0)
                slist.append(sum([z.pn for z in l]) or 0)
                slist.append(sum([z.pne for z in l]) or 0)
                # slist.append(sum([z.nbr_carton for z in l]))

                # glist.append([key[0],sum([z.nbr_carton for z in l])])
                glist.append(slist)
            list_lines.append(glist)

        return list_lines

    @api.multi
    def group_by_shcode3(self):
        list_lines = []
        seal_tc_ids = list(set([line.product_id.code_sh.id for line in self.sale_picking_line_ids]))
        for l in seal_tc_ids:
            # list_lines.append(self.sale_picking_line_ids.filtered(lambda x : x.sh_code.id == l))
            sous_list = sorted(self.sale_picking_line_ids.filtered(lambda x: x.sh_code.id == l),
                               key=lambda x: (x.product_id.default_code, x.production_date))
            glist = []
            for key, l in groupby(sous_list, lambda l: (l.lot_code_finale[0:6], l.product_id)):
                l = list(l)
                print(key, " : ", [x for x in l])
                # print(len(l[0]))
                slist = []

                slist.append(key[0] or '')
                slist.append(key[1].description_commodity_id.name or '')
                slist.append(key[1].brand.name or '')
                slist.append(key[1].default_code.split()[0] or '')
                slist.append(str(sum([z.nbr_carton for z in l]))+' x '+str(int(l[0].uom_packing_id.factor_inv))+" cans")
                glist.append(slist)
            list_lines.append(glist)

        return list_lines

    @api.multi
    def group_by_shcode4(self):
        list_lines = []
        seal_tc_ids = list(set([line.product_id.code_sh.id for line in self.sale_picking_line_ids]))
        for l in seal_tc_ids:
            # list_lines.append(self.sale_picking_line_ids.filtered(lambda x : x.sh_code.id == l))
            sous_list = sorted(self.sale_picking_line_ids.filtered(lambda x: x.sh_code.id == l),
                               key=lambda x: (x.product_id.default_code, x.production_date))
            glist = []

            for key, l in groupby(sous_list, lambda l: (l.lot_code_finale[0:6], l.product_id)):
                l = list(l)
                print(key, " : ", [x for x in l])
                # print(len(l[0]))
                slist = []

                slist.append(key[0] or '')
                slist.append(key[1].description_commodity_id.name or '')
                slist.append(key[1].name_sci.name or '')
                slist.append(sum([z.nbr_carton for z in l]) or 0)
                slist.append(sum([z.pn for z in l]) or 0)
                slist.append(sum([z.pne for z in l]) or 0)





                glist.append(slist)
            list_lines.append(glist)

        return list_lines

    @api.multi
    def sort_sale_picking_line_ids(self):
        l = self.sale_picking_line_ids.sorted(key=lambda x: x.product_id.default_code)
        return l
        #return sorted(self.sale_picking_line_ids, key=lambda x: (x.product_id.default_code, x.production_date))

    @api.multi
    def total_weights(self):
        pne_tot = sum([l.pne for l in self.sale_picking_line_ids])
        pn_tot = sum([l.pn for l in self.sale_picking_line_ids])
        gross_tot = sum([l.gross_wei for l in self.sale_picking_line_ids])
        return gross_tot, pn_tot, pne_tot

    @api.multi
    def get_all_info_lc(self):
        list_lines = []
        side_a = []
        side_b = []
        uom_packing_ids = list(set([line.uom_packing_id.id for line in self.sale_picking_line_ids]))
        lines_sh = self.group_by_shcode()

        for l in uom_packing_ids:
            info_a = []
            lines = self.sale_picking_line_ids.filtered(lambda x: x.uom_packing_id.id == l)
            qty = sum([l.nbr_carton for l in lines])
            unit_pne = 0.0
            unit_pn = 0.0
            unit_gross = 0.0
            if qty:
                unit_pne = sum([l.pne for l in lines]) / qty
                unit_pn = sum([l.pn for l in lines]) / qty
                unit_gross = sum([l.gross_wei for l in lines]) / qty

            info_a.append(lines[0].uom_packing_id.name)
            info_a.append(unit_gross)
            info_a.append(unit_pn)
            info_a.append(unit_pne)
            side_a.append(info_a)
        lenght_a = len(side_a)

        for lines in lines_sh:
            info_b = []
            qty = sum([l.nbr_carton for l in lines])
            pne_tot = sum([l.pne for l in lines])
            pn_tot = sum([l.pn for l in lines])
            gross_tot = sum([l.gross_wei for l in lines])
            info_b.append(qty)
            info_b.append(lines[0].sh_code.name)
            info_b.append(gross_tot)
            info_b.append(pn_tot)
            info_b.append(pne_tot)
            side_b.append(info_b)
        lenght_b = len(side_b)
        if lenght_a > lenght_b:
            i = lenght_a - lenght_b
            for j in range(0, i):
                side_b.append([0, 0, 0, 0])
        if lenght_b > lenght_a:
            i = lenght_b - lenght_a
            for j in range(0, i):
                side_a.append([0, 0, 0, 0])

        list_lines.append(side_a)
        list_lines.append(side_b)
        for i in range(0, len(side_a)):
            for l in side_b[i]:
                side_a[i].append(l)
        return side_a


class SalePickingLineMidav(models.Model):
    """  """
    _name = "midav.sale.picking.line"

    @api.depends("sale_operation_line_ids.qty_done", "sale_operation_line_ids.state")
    def _compute_qty_done(self):
        """ """
        for spl in self:
            qty = 0.0
            # sum of qty done of operation lines in state done
            sps_done = [sp for sp in spl.sale_operation_line_ids if sp.state == 'done']
            for l in sps_done:
                qty += l.qty_done
            spl.qty_done = qty

    @api.one
    @api.depends("uom_id", "uom_packing_id", "qty_done")
    def _compute_nbr_carton(self):
        if self.uom_id and self.uom_packing_id:
            nbr_carton = ((self.qty_done or 0.0) * \
                          self.uom_id.factor_inv) / float(self.uom_packing_id.factor_inv)
            self.nbr_carton = math.ceil(nbr_carton)

    name = fields.Char(string=_("Name"), readonly=True)
    marquage = fields.Char(string=_('Marquage'))
    lot_code = fields.Char(string=_('LOT CODE'))
    lot_code_finale = fields.Char(string=_('Lot'), compute="get_principal_lot")
    attachements = fields.Many2many('ir.attachment', string=_('Attachments'))
    mould = fields.Many2one('midav.mould', string=_('MOULD'))
    production_date = fields.Date(string=_('Production Date'))
    lapsing_date = fields.Date(string=_('Lapsing Date'))
    sale_picking_id = fields.Many2one("midav.sale.picking", string=_("Sale picking"), required=True,
                                      ondelete='restrict')
    product_id = fields.Many2one("product.product", string=_("Product"), required=True)
    sh_code = fields.Many2one('sh.code', related='product_id.code_sh')
    lot = fields.Char(string=_("N° Lot"))
    qty_todo = fields.Float(string=_("Quantity to do"), default=0.0)
    qty_done = fields.Float(string=_("Quantity done"), default=0.0, compute=_compute_qty_done, store=True)
    qty_remain = fields.Float(string=_("Quantity Remained"), default=0.0, store=True)
    qty_enter = fields.Float(string=_('Quantity Entered'), default=0.0)
    nbr_carton = fields.Integer(string=_("Nbr colis"), default=0, required=True,
                                compute=_compute_nbr_carton, store=True)
    # type_carton = fields.Many2one("midav.cartons", string=_("Type carton"), required=False)#AMH required
    uom_packing_id = fields.Many2one("product.uom", string=_("Conditioning unit"))
    uom_id = fields.Many2one("product.uom", string=_("Unit of measure"))  # , required=True)
    old_uom_id = fields.Many2one("product.uom", string=_("Old Unit of measure"))
    special_mark = fields.Text(string=_("Special Marking"))
    sale_operation_line_ids = fields.One2many("midav.sale.operation.line", "sale_picking_line_id",
                                              string=_("Sale operation lines"))
    # invoice_lines = fields.Many2many('account.invoice.line', 'sale_picking_line_invoice_rel', 'sale_picking_line_id',
    #                                  'invoice_line_id', string='Invoice Lines', copy=False)
    sead_tc_id = fields.Many2one("midav.sead.tc", string=_("SEAL / TC"))
    blanket = fields.Char(string=_("Blanket"))
    production = fields.Date(string=_("Production date"))
    pne = fields.Float(string=_("Drained Weight/Kgs"), )
    pn = fields.Float(string=_("Net Weight/Kgs"), )
    gross_wei = fields.Float(string=_("Gross Weight/Kgs"), )
    expired_date = fields.Date(string=_("Lapsing date"))
    sale_order_id = fields.Many2one("sale.order", related="sale_picking_id.sale_order_id")
    company_id = fields.Many2one('res.company', string=_('Company'))
    layout_category_id = fields.Many2one("sale.layout_category", "Section")

    @api.model
    def create(self, values):
        """"""
        values['name'] = self.env['ir.sequence'].next_by_code('sale.picking.line.name') or _('New')
        return super(SalePickingLineMidav, self).create(values)

    @api.multi
    @api.depends('lot')
    def get_principal_lot(self):
        for r in self:
            if r.lot:
                r.lot_code_finale = r.lot

    @api.multi
    @api.onchange("product_id", "sale_order_id")
    def _onchange_product_id(self):
        products = []
        categ_uom_id = False
        for spl in self:
            for sl in spl.sale_picking_id.sale_order_id.order_line:
                products.append(sl.product_id.id)
                if sl.product_id.id == spl.product_id.id:
                    spl.uom_id = sl.product_uom or spl.product_id.uom_id
                    spl.old_uom_id = spl.uom_id
                    categ_uom_id = sl.product_uom.category_id.id or spl.product_id.uom_id.category_id.id
                    spl.layout_category_id = sl.layout_category_id and sl.layout_category_id.id or False
                    # spl.type_carton = spl.product_id.midav_cartons_id

        return {
            'domain': {
                'product_id': [('id', 'in', products) if products else ('id', '!=', False)],
                'uom_id': [('category_id', '=', categ_uom_id)],
            },
        }

    # @api.multi
    # def get_lapsing_date(self):
    #     date = self.lapsing_date
    #     print("----------",date)
    #     Mois = ['JA', 'FE', 'MA', 'AV', 'MAI', 'JU', 'JUI', 'AO', 'SE', 'OC',
    #             'NO', 'DE']

    @api.multi
    def count_pne(self):
        for spl in self:
            spl.pne = ((self.uom_packing_id.pne_uom_weight or 0.0) * (spl.nbr_carton or 0.0))
            spl.pn = ((self.uom_packing_id.pn_uom_weight or 0.0) * (spl.nbr_carton or 0.0))
            spl.gross_wei = spl.product_id.gross_weight * (spl.qty_done or 0.0)

    @api.onchange("uom_id")
    def on_change_uom(self):
        for spl in self:
            if spl.uom_id and spl.old_uom_id:
                old_factor = spl.old_uom_id.factor_inv
                new_factor = spl.uom_id.factor_inv
                spl.qty_todo = (old_factor / float(new_factor)) * (spl.qty_todo or 0.0)
                spl.old_uom_id = spl.uom_id


class SaleOperationMidav(models.Model):
    """"""
    _name = "midav.sale.operation"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Sale Operation"
    _order = 'date desc, id desc'

    name = fields.Char(string=_("Name"), readonly=True)
    user_id = fields.Many2one("res.users", string=_("Storekeeper"))
    date = fields.Date(string=_("Date preparation"), default=datetime.now(), required=True)
    sale_picking_id = fields.Many2one("midav.sale.picking", string=_("Sale picking"), required=True,
                                      ondelete="restrict")
    back_sale_operation_id = fields.Many2one("midav.sale.operation", string=_("Back sale operation"))
    sale_operation_line_ids = fields.One2many("midav.sale.operation.line", "sale_operation_id",
                                              string=_("Sale operation lines"))
    company_id = fields.Many2one('res.company', string=_('Company'))

    state = fields.Selection([
        ('draft', _('Draft')),
        ('done', _('Done')),
        ('canceled', _('Canceled')),
    ], string=_('State'), readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.model
    def create(self, values):
        """"""
        values['name'] = self.env['ir.sequence'].next_by_code('sale.operation.name') or _('New')
        return super(SaleOperationMidav, self).create(values)

    @api.multi
    def generate_lines_from_sale_picking(self):
        """"""
        for sop in self:
            if sop.sale_picking_id and not len(sop.sale_operation_line_ids or ""):
                for spl in [spli for spli in sop.sale_picking_id.sale_picking_line_ids if
                            spli.qty_done < spli.qty_todo]:
                    vals = {
                        'sale_operation_id': sop.id,
                        'state': 'draft',
                        'sale_picking_line_id': spl.id,
                        'lot': spl.lot,
                        'qty_todo': spl.qty_todo,
                        'qty_export': spl.qty_enter,
                        'uom_packing_id': spl.uom_packing_id.id,
                        'uom_id': spl.uom_id.id,
                        'premption_date': spl.lapsing_date,
                        'production_date': spl.production_date,
                    }
                    self.env['midav.sale.operation.line'].create(vals)

    @api.multi
    def action_done(self):
        """"""
        if self.sale_operation_line_ids:
            for sopl in self.sale_operation_line_ids:
                sopl.action_done()
        self.write({
            'state': 'done',
        })

    @api.multi
    def action_draft(self):
        """"""
        self.write({
            'state': 'draft',
        })

    @api.multi
    def action_canceled(self):
        """"""
        self.write({
            'state': 'canceled',
        })


class SaleOperationLineMidav(models.Model):
    """"""
    _name = "midav.sale.operation.line"

    @api.depends("qty_sample", "qty_done", "qty_export", "qty_todo", "qty_missing", "qty_dented", "qty_leak",
                 "default_polish", "lack_of_weight", "qty_cambered", "qty_seam", "qty_big_dots", "qty_rust",
                 "qty_flush", "qty_small_dots")
    def _compute_qty_remain(self):
        """ """
        for sol in self:
            ecart = 0.0
            ecart = sol.qty_missing + sol.qty_dented + sol.qty_leak + sol.qty_cambered + sol.qty_seam \
                    + sol.qty_big_dots + sol.qty_rust + sol.qty_flush + sol.qty_small_dots + sol.lack_of_weight + sol.default_polish

            sol.qty_remain = (sol.qty_export - sol.qty_done - sol.qty_sample - ecart) \
                if (sol.qty_export is not False and sol.qty_done is not False) else 0.0

    @api.one
    @api.depends("uom_id", "uom_packing_id", "qty_done")
    def _compute_nbr_carton(self):
        if self.uom_id and self.uom_packing_id:
            nbr_carton = ((self.qty_done or 0.0) * \
                          self.uom_id.factor_inv) / float(self.uom_packing_id.factor_inv)
            self.nbr_carton = math.ceil(nbr_carton)

    name = fields.Char(string=_("Name"), readonly=True)
    sale_operation_id = fields.Many2one("midav.sale.operation", string=_("Sale operation"),
                                        required=True, ondelete='restrict')
    sale_picking_line_id = fields.Many2one("midav.sale.picking.line", string=_("Sale picking line"), required=False,
                                           ondelete='restrict')
    sale_picking_id = fields.Many2one("midav.sale.picking", string=_("Sale picking"),
                                      related="sale_picking_line_id.sale_picking_id", readonly=True)
    product_id = fields.Many2one("product.product", related="sale_picking_line_id.product_id", string=_("Product"),
                                 required=True, readonly=True)
    lot = fields.Char(string=_("N° Lot"), default=lambda self: self.sale_picking_line_id.lot)
    qty_todo = fields.Float(string=_("Quantity to do"), default=0.0)
    qty_export = fields.Float(string=_("Quantity export"), default=0.0)
    qty_sample = fields.Float(string=_("Quantity sample"), default=0.0)
    qty_done = fields.Float(string=_("Quantity done"), default=0.0, store=True)
    qty_remain = fields.Float(string=_("Remained quantity"), default=0.0, compute=_compute_qty_remain, store=True)
    qty_missing = fields.Float(string=_("Missing quantity"), default=0.0, required=True)
    qty_dented = fields.Float(string=_("Dented quantity"), default=0.0, required=True)
    qty_leak = fields.Float(string=_("Leak quantity"), default=0.0, required=True)
    qty_seam = fields.Float(string=_("Defect of seam"), default=0.0, required=True)
    qty_cambered = fields.Float(string=_("Cambered quantity"), default=0.0, required=True)
    qty_big_dots = fields.Float(string=_("Big dots"), default=0.0, required=True)
    qty_rust = fields.Float(string=_("Rust"), default=0.0, required=True)
    qty_flush = fields.Float(string=_("Flush"), default=0.0, required=True)
    nbr_carton = fields.Integer(string=_("Nbr colis"), default=0, required=True, compute='_compute_nbr_carton')
    qty_small_dots = fields.Float(string=_("Small dots"), default=0.0, required=True)
    lack_of_weight = fields.Float(string=_("Lack of weight"), default=0.0, required=True)
    default_polish = fields.Float(string=_("Default Polish"), default=0.0, required=True)
    premption_date = fields.Date(string=_('peremption date'))
    production_date = fields.Date(string=_('production date'))
    # type_carton = fields.Char(string=_("Type carton"), default=0, required=False)#AMH required
    company_id = fields.Many2one('res.company', string=_('Company'))
    uom_packing_id = fields.Many2one("product.uom", string=_("Conditioning unit"))
    uom_id = fields.Many2one("product.uom", string=_("Unit of measure"), default=lambda r: r.product_id.uom_id)
    special_mark = fields.Text(string=_("Special Marking"))
    state = fields.Selection([
        ('draft', _('Draft')),
        ('done', _('Done')),
        ('canceled', _('Canceled')),
    ], string=_('State'), readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.model
    def create(self, values):
        """ """
        values['name'] = self.env['ir.sequence'].next_by_code('sale.operation.line.name') or _('New')
        return super(SaleOperationLineMidav, self).create(values)

    @api.multi
    def action_done(self):
        """Verify if the sum of lost quantities is the same of remained quantity"""
        for sopl in self:
            # sum_q = sum([sopl.qty_dented or 0.0,
            #             sopl.qty_missing or 0.0,
            #             sopl.qty_leak or 0.0,
            #             sopl.qty_seam or 0.0,
            #             sopl.qty_cambered or 0.0,
            #             sopl.qty_big_dots or 0.0])
            # op_back = False
            # if sum_q != sopl.qty_remain:
            #     raise ValidationError(_("Operation line %s: The sum of lost quantities %s is not the same of remained \
            #     quantity %s"%(sopl.name, str("%.3f" % sum_q).replace(".", ","), str("%.3f" % sopl.qty_remain).replace(".", ","))))
            #
            if float(sopl.qty_todo - sopl.qty_done) > 0:
                op_back = sopl.sale_operation_id.back_sale_operation_id or self.env['midav.sale.operation'].create({
                    'user_id': sopl.sale_operation_id.user_id.id,
                    'sale_picking_id': sopl.sale_operation_id.sale_picking_id.id,
                })
                if not sopl.sale_operation_id.back_sale_operation_id:
                    sopl.sale_operation_id.write({
                        'back_sale_operation_id': op_back.id,
                    })
                self.env['midav.sale.operation.line'].create({
                    'sale_operation_id': op_back.id,
                    'product_id': sopl.product_id.id,
                    'lot': sopl.lot,
                    'uom_id': sopl.uom_id.id,
                    'uom_packing_id': sopl.uom_packing_id.id,
                    'qty_todo': float(sopl.qty_todo - sopl.qty_done),
                    'sale_picking_line_id': sopl.sale_picking_line_id.id,

                })
            sopl.write({'state': 'done'})


class SeadTcMidav(models.Model):
    """"""
    _name = "midav.sead.tc"

    def _compute_name(self):
        for mst in self:
            mst.name = "SEAL: " + str(mst.sead or "") + " - TC: " + str(mst.tc or "")

    name = fields.Char(string=_("Name"), compute=_compute_name, readonly=True)
    sead = fields.Char(string=_("SEAL"), required=True)
    tc = fields.Char(string=_("TC"), required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))


class MouldMidav(models.Model):
    _name = "midav.mould"

    name = fields.Char(string=_('Name'), required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))


class AttachementTransitMidav(models.Model):
    _name = "midav.document"

    name = fields.Char(string=_('Document Model'), required=True)
    attachments = fields.Html(string=_('Document'))

class LadingTransitMidav(models.Model):
    _name = "midav.lading"

    name = fields.Char(string=_('Name'), required=True)
    attachments = fields.Html(string=_('Document'))


class ShCodeMidav(models.Model):
    _name = "sh.code"

    name = fields.Char(string=_('SH CODE'), required=True)
    designation = fields.Text(string=_('Designation'))


class ScientificNameMidav(models.Model):
    _name = "scientific.name"

    name = fields.Char(string=_('Name'), required=True)
