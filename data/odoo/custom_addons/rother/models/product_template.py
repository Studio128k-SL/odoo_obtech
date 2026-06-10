from odoo import models, fields, api
import base64


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_Ref_fab = fields.Char(string='Referencia Fabricante')

    x_barcode_image = fields.Char(
        string='Imagen Barcode Base64',
        compute='_compute_barcode_image'
    )

    x_display_name_label = fields.Char(
        string='Nombre Etiqueta',
        compute='_compute_display_name_label'
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

    @api.depends('name')
    def _compute_display_name_label(self):
        for record in self:
            if record.name and len(record.name) > 60:
                record.x_display_name_label = record.name[:60] + '...'
            else:
                record.x_display_name_label = record.name or ''

    def action_realizar_traslado(self):
        self.ensure_one()

        quants = self.env['stock.quant'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ])
        location_ids = quants.mapped('location_id').ids

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location_ids[0] if location_ids else picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'move_ids': [(0, 0, {
                'name': self.name,
                'product_id': self.product_variant_ids[0].id,
                'product_uom_qty': 1,
                'product_uom': self.uom_id.id,
                'picking_type_id': picking_type.id,
                'location_id': location_ids[0] if location_ids else picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Realizar Traslado',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'view_id': self.env.ref('rother.rother_stock_picking_traslado_form').id,
            'context': dict(self.env.context, allowed_location_ids=location_ids),
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allowed_location_ids = fields.Many2many(
        'stock.location',
        string='Allowed Source Locations',
        compute='_compute_allowed_location_ids',
        store=False,
    )

    @api.depends_context('allowed_location_ids')
    def _compute_allowed_location_ids(self):
        for picking in self:
            ids_ = picking.env.context.get('allowed_location_ids', [])
            picking.allowed_location_ids = [(6, 0, ids_)]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            domain = ['|', '|', '|',
                ('default_code', operator, name),
                ('name', operator, name),
                ('barcode', operator, name),
                ('x_Ref_fab', operator, name),
            ] + domain
            return self._search(domain, limit=limit, order=order)
        return super()._name_search(name, domain, operator, limit, order)