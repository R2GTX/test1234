# -*- coding: utf-8 -*-
from ast import literal_eval
from datetime import datetime
from odoo import models, fields, api, _

class EmptyCansMidav(models.Model):
    _name = 'midav.empty.cans'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_empty_cans', 'unique (code)', _('The empty cans code must be unique!')),
    ]

class FishMidav(models.Model):
    _name = 'midav.fish'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_fish', 'unique (code)', _('The fish code must be unique!')),
    ]

class PreparationMidav(models.Model):
    _name = 'midav.preparation'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_preparation', 'unique (code)', _('The preparation code must be unique!')),
    ]

class JutageMidav(models.Model):
    _name = 'midav.jutage'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_jutage', 'unique (code)', _('The jutage code must be unique!')),
    ]

class CasesMidav(models.Model):
    _name = 'midav.cases'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_cases', 'unique (code)', _('The cases code must be unique!')),
    ]

class CartonsMidav(models.Model):
    _name = 'midav.cartons'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    qty_per_one = fields.Float(string = _("Quantity per one"), required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_cartons', 'unique (code)', _('The cartons code must be unique!')),
    ]

class TagMidavMidav(models.Model):
    _name = 'midav.tag'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_tag', 'unique (code)', _('The tag code must be unique!')),
    ]

class StickersBtesMidav(models.Model):
    _name = 'midav.stickers.btes'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    mcode = fields.Char(string='Management Code', required=False)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_stickers_btes', 'unique (code)', _('The stickers code must be unique!')),
    ]

class StickersBarqMidav(models.Model):
    _name = 'midav.stickers.barq'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    mcode = fields.Char(string='Management Code', required=False)
    company_id = fields.Many2one('res.company', string=_('Company'))

    _sql_constraints = [
        ('unique_code_barq', 'unique (code)', _('The barq code must be unique!')),
    ]

class BrandMidav(models.Model):
    _name = 'midav.brand'

    name = fields.Char(string='Designation', required=True)
    code = fields.Char(string='Code', required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))


