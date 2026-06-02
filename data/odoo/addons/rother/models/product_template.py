from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_Ref_fab = fields.Char(string='Referencia Fabricante')