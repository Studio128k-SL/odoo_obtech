from odoo import models, fields, api

class RotherGPV(models.Model):
    _name = 'rother.gpv'
    _description = 'Grupo de Compra Rother'

    name = fields.Char(string='Número', readonly=True, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    entregar_a = fields.Char(string='Entregar a')
    presupuesto_ids = fields.Many2many('rother.presupuesto', string='Presupuestos')
    linea_ids = fields.One2many('rother.gpv.linea', 'gpv_id', string='Líneas')
    pv_ids = fields.One2many('rother.pv', 'gpv_id', string='Pedidos Virtuales')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('rother.gpv') or 'Nuevo'
        return super().create(vals_list)

    def action_cargar_lineas(self):
        for rec in self:
            rec.linea_ids.unlink()
            lineas = []
            for presupuesto in rec.presupuesto_ids:
                secciones = presupuesto.linea_ids.filtered(lambda s: s.display_type == 'line_section')
                for linea in presupuesto.linea_ids.filtered(lambda l: not l.display_type):
                    seccion_anterior = secciones.filtered(lambda s: s.sequence < linea.sequence)
                    seccion_nombre = seccion_anterior[-1].name if seccion_anterior else ''
                    lineas.append({
                        'gpv_id': rec.id,
                        'presupuesto_linea_id': linea.id,
                        'product_id': linea.product_id.id,
                        'nombre': linea.name,
                        'cantidad': linea.cantidad,
                        'precio_unitario': linea.precio_unitario,
                        'taxes_id': [(6, 0, linea.taxes_id.ids)],
                        'importe_total': linea.importe_total,
                        'seccion_nombre': seccion_nombre,
                    })
            self.env['rother.gpv.linea'].create(lineas)

    def action_generar_pv(self):
        for rec in self:
            rec.pv_ids.unlink()
            proveedores = rec.linea_ids.filtered(lambda l: l.proveedor_id).mapped('proveedor_id')
            for proveedor in proveedores:
                pv = self.env['rother.pv'].create({
                    'gpv_id': rec.id,
                    'proveedor_id': proveedor.id,
                })
                lineas_proveedor = rec.linea_ids.filtered(lambda l: l.proveedor_id == proveedor)
                for linea in lineas_proveedor:
                    self.env['rother.pv.linea'].create({
                        'pv_id': pv.id,
                        'gpv_linea_id': linea.id,
                        'product_id': linea.product_id.id,
                        'nombre': linea.nombre,
                        'cantidad': linea.cantidad,
                        'precio_unitario': linea.precio_unitario,
                        'taxes_id': [(6, 0, linea.taxes_id.ids)],
                        'importe_total': linea.importe_total,
                        'seccion_nombre': linea.seccion_nombre,
                    })


class RotherGPVLinea(models.Model):
    _name = 'rother.gpv.linea'
    _description = 'Línea de GPV'

    gpv_id = fields.Many2one('rother.gpv', string='GPV', ondelete='cascade')
    presupuesto_linea_id = fields.Many2one('rother.presupuesto.linea', string='Línea de Presupuesto')
    product_id = fields.Many2one('product.product', string='Producto')
    nombre = fields.Char(string='Nombre')
    cantidad = fields.Float(string='Cantidad')
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    importe_total = fields.Float(string='Importe Total')
    seccion_nombre = fields.Char(string='Proyecto')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor')


class RotherPV(models.Model):
    _name = 'rother.pv'
    _description = 'Pedido Virtual Rother'

    gpv_id = fields.Many2one('rother.gpv', string='GPV', ondelete='cascade')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor')
    referencia_proveedor = fields.Char(string='Referencia Proveedor')
    llegada_prevista = fields.Date(string='Llegada Prevista')
    linea_ids = fields.One2many('rother.pv.linea', 'pv_id', string='Líneas')

    @api.onchange('proveedor_id')
    def _onchange_proveedor_id(self):
        if self.proveedor_id:
            self.referencia_proveedor = self.proveedor_id.ref


class RotherPVLinea(models.Model):
    _name = 'rother.pv.linea'
    _description = 'Línea de PV Rother'

    pv_id = fields.Many2one('rother.pv', string='PV', ondelete='cascade')
    gpv_linea_id = fields.Many2one('rother.gpv.linea', string='Línea GPV')
    product_id = fields.Many2one('product.product', string='Producto')
    nombre = fields.Char(string='Nombre')
    cantidad = fields.Float(string='Cantidad')
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    importe_total = fields.Float(string='Importe Total')
    seccion_nombre = fields.Char(string='Proyecto')