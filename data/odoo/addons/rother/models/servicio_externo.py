from odoo import models, fields, api
from markupsafe import Markup

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
    
    @api.model
    def _cron_alerta_fecha_finalizacion(self):
        hoy = fields.Date.today()
        fecha_1_mes = fields.Date.add(hoy, months = 1)
        fecha_15_dias = fields.Date.add(hoy, days = 15)
        fecha_7_dias = fields.Date.add(hoy, days = 7)
        fecha_1_dia = fields.Date.add(hoy, days = 1)

        servicios = self.search([
            ('fecha_finalizacion', 'in', [fecha_1_mes, fecha_15_dias, fecha_7_dias, fecha_1_dia])
        ])

        for servicio in servicios:
            dias = (servicio.fecha_finalizacion - hoy).days
            mensaje = Markup("⚠️ El servicio <b>%s</b> finaliza en <b>%s días</b> (%s).") % (servicio.name, dias, servicio.fecha_finalizacion)
            servicio.message_post(
                body = mensaje,
                subject = f"Aviso: {servicio.name} próximo a finalización",
                subtype_xmlid="mail.mt_comment",
                partner_ids = servicio._get_usuarios_notificar(),
            )
    
    def _get_usuarios_notificar(self):
        usuarios = self.env['res.users'].search([
            ('share', '=', False),
        ])
        return usuarios.mapped('partner_id').ids

class RotherServicioExternoLinea(models.Model):
    _name= 'rother.servicio.externo.linea'
    _description = 'Línea de Servicio Extra'

    servicio_id = fields.Many2one('rother.servicio.externo', string = 'Servicio', ondelete='cascade')
    name = fields.Char(string='Nombre', required=True)
    precio = fields.Float(string='Precio', digits= 'Precio Producto')
    periodo_pago = fields.Char(string='Periodo de Pago', tracking=True)
    fecha_finalizacion = fields.Date(string='Fecha de Finalización')