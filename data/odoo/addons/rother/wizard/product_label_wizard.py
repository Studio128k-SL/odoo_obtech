from odoo import models, fields

class ProductLabelWizard(models.TransientModel):
    _name = 'rother.product.label.wizard'
    _description = 'Asistente de impresión de etiquetas'

    product_id = fields.Many2one('product.template', string= 'Producto')

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Tipo de etiqueta',
        domain=[('model', '=', 'product.template'), ('report_type', '=', 'qweb-pdf')],
    )

    label_type = fields.Selection([
        # ('full', 'Etiqueta completa'),
        # ('name_only', 'Solo nombre'),
        # ('barcode_only', 'Solo código de barras'),
    ], string= 'Tipo de etiqueta', default = False)

    def action_print(self):
        if not self.report_id:
            return
        return self.report_id.report_action(self.product_id)