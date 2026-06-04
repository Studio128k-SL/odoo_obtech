from odoo import models, fields, api

class RotherPresupuesto(models.Model):
    _name = 'rother.presupuesto'
    _description = 'Presupuesto Rother'
    _order = 'sequence, id'

    name = fields.Char(string='Número', readonly=True, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    linea_ids = fields.One2many('rother.presupuesto.linea', 'presupuesto_id', string='Líneas')
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)
    sequence = fields.Integer(string = "Secuencia", default="1")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('rother.presupuesto') or 'Nuevo'
        return super().create(vals_list)

    @api.depends('linea_ids.importe_total')
    def _compute_importe_total(self):
        for rec in self:
            rec.importe_total = sum(
                rec.linea_ids.filtered(lambda l: not l.display_type).mapped('importe_total')
            )


class RotherPresupuestoLinea(models.Model):
    _name = 'rother.presupuesto.linea'
    _description = 'Línea de Presupuesto Rother'

    presupuesto_id = fields.Many2one('rother.presupuesto', string='Presupuesto', ondelete='cascade')
    display_type = fields.Selection([
        ('line_section', 'Sección'),
    ], default=False)
    name = fields.Char(string='Nombre')
    product_id = fields.Many2one('product.product', string='Producto')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)
    sequence = fields.Integer(string='Secuencia', default=10)

    @api.depends('cantidad', 'precio_unitario', 'taxes_id', 'display_type')
    def _compute_importe_total(self):
        for rec in self:
            if rec.display_type:
                rec.importe_total = 0.0
            else:
                subtotal = rec.cantidad * rec.precio_unitario
                if rec.taxes_id:
                    taxes = rec.taxes_id.compute_all(subtotal)
                    rec.importe_total = taxes['total_included']
                else:
                    rec.importe_total = subtotal

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.precio_unitario = self.product_id.lst_price
            self.taxes_id = self.product_id.taxes_id