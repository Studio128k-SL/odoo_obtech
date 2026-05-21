from odoo import models, fields, api

class RotherServicioExterno(models.Model):
    _name = 'rother.servicio.externo'
    _description= 'Servicios Externos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name=fields.Char(string='Nombre del Servicio', required=True, trackin=True)
    descripcion=fields.Text(string='Descripción' ,widget='text')
    imagen=fields.Binary(string='Imagen')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', required=True, tracking=True)
    precio= fields.Float(string='Precio', digits='Product Price', tracking=True)
    taxes_id= fields.Many2many(
        'account.tax',
        string= 'Impuestos',
    )
    periodo_pago = fields.Char(string='Periodos de pago', tracking= True)
    fecha_finalizacion= fields.Date(string='Fecha de Finalización', tracking=True)
    extra_ids=fields.One2many('rother.servicio.externo.linea', 'servicio_id', string='Servicios Extra')
    precio_total = fields.Float(
        string='Precio Total',
        compute='_compute_precio_total',
        store=True
    )
    currency_id=fields.Many2one(
        'res.currency',
        string='Moneda',
        default = lambda self: self.env.company.currency_id,
    )

    @api.depends('precio', 'extra_ids.precio')
    def _compute_precio_total(self):
        for rec in self:
            rec.precio_total = rec.precio + sum(rec.extra_ids.mapped('precio'))

class RotherServicioExternoLinea(models.Model):
    _name= 'rother.servicio.externo.linea'
    _description = 'Línea de Servicio Extra'

    servicio_id = fields.Many2one('rother.servicio.externo', string = 'Servicio', ondelete='cascade')
    name = fields.Char(string='Nombre', required=True)
    precio = fields.Float(string='Precio', digits= 'Precio Producto')
    periodo_pago = fields.Char(string='Periodo de Pago', tracking=True)
    fecha_finalizacion = fields.Date(string='Fecha de Finalización')