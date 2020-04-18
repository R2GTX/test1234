# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MIDAV BASE',
    'version' : '0.1',
    'summary': 'The base of MIDAV project',
    'description': """
        Midav Base
    """,
    'category': 'Accounting',
    'author': "Talouzet Houria, Abdelmajid ELhamdaoui, KARIZMA CONSEIL",
    'website': 'http://www.karizma-conseil.com',
    'images' : [
    ],
    'depends' : [
        'base',
        'web',
        'sale_management',
        'product',
        'account',
    ],
    'data': [
        'security/midav_security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/paper_report_format.xml',
        'data/incoterms.xml',
        'views/products.xml',
        'views/action_tmp.xml',
        'views/sale_order.xml',
        'views/midav_sale.xml',
        'views/midav_product_views.xml',
        'views/menus_actions.xml',
        'views/res_company_views.xml',
        'views/sale_layout_category_view.xml',
        'views/account_invoice.xml',
        'views/account_tax_view.xml',
        'views/res_country_view.xml',
        'report/external_layout_report.xml',
        'report/report_templates.xml',
        'report/suggested_product_preformat_report.xml',
        'report/proformat_invoice_report_template.xml',
        'report/health_certificate_report.xml',
        'report/report_health_certificate_model_2.xml',
        'report/sanitary_certificate_report.xml',
        'report/order_preparation_report.xml',
        'report/report_invoice_document.xml',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    #'post_init_hook': '_auto_install_l10n',
}
