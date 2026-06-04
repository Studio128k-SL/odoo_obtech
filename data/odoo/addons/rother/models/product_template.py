from odoo import models, fields, api
import base64

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_Ref_fab = fields.Char(string='Referencia Fabricante')

    x_barcode_image = fields.Char(
        string='Imagen Barcode Base64',
        compute='_compute_barcode_image'
    )

    @api.depends('barcode')
    def _compute_barcode_image(self):
        for record in self:
            if record.barcode:
                barcode_bytes = self.env['ir.actions.report'].barcode(
                    'Code128', record.barcode, width=600, height=100
                )
                record.x_barcode_image = base64.b64encode(barcode_bytes).decode('utf-8')
            else:
                record.x_barcode_image = False