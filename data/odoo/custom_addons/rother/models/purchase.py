from odoo import models, fields

class PurchaseOrderRother(models.Model):
    _inherit = 'purchase.order'

    rother_pv_id = fields.Many2one('rother.pv', string='Pedido Virtual', readonly=True)