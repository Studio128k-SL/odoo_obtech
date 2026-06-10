from odoo import models, fields, api

class StockPickingRother(models.Model):
    _inherit = 'stock.picking'

    resumen_productos = fields.Text(
        string= 'Productos',
        compute = '_compute_resumen_productos',
        store = False
    )

    @api.depends('move_ids.product_id', 'move_ids.product_uom_qty')
    def _compute_resumen_productos(self):
        for rec in self:
            lineas = []
            for move in rec.move_ids:
                ref_fab = move.product_id.product_tmpl_id.x_Ref_fab or ''
                ref_prov = move.product_id or ''
                nombre = move.product_id.name or ''

                if ref_fab:
                    lineas.append('[%s][%s] %s x%g' % (ref_fab, ref_prov, nombre, move.product_uom_qty))
                else:
                    lineas.append('%s x%g' % (nombre, move.product_uom_qty))
            rec.resumen_productos = '\n'.join(lineas)