from odoo import models, fields, api, tools
from markupsafe import Markup
from dateutil.relativedelta import relativedelta

class RotherServicioExterno(models.Model):
    _name = 'rother.servicio.externo'
    _description= 'Servicios Externos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    mostrar_alerta_completa = fields.Boolean(string='Mostrar mensaje completo', default=False)

    name = fields.Char(string='Nombre del Servicio', required=True, tracking=True)
    descripcion = fields.Text(string='Descripción', widget='text')
    imagen = fields.Binary(string='Imagen')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', required=True, tracking=True)
    precio = fields.Float(string='Precio', digits='Product Price', tracking=True)
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    fecha_inicio = fields.Date(string='Fecha de Inicio')

    periodo_anios = fields.Integer(string='Años', default=0)
    periodo_meses = fields.Integer(string='Meses', default=0)
    periodo_dias = fields.Integer(string='Días', default=0)

    forma_pago = fields.Char(string="Forma de pago", tracking=True)
    cuenta_origen=fields.Char(string="Cuenta de origen", tracking=True)
    cuenta_destino=fields.Char(string="Cuenta de destino", tracking=True)

    doc_archivo = fields.Binary(string = 'Archivo relacionado al Servicio' , attachment=True)
    nombre_doc_archivo = fields.Char(string='Documento relacionado con el Servicio')

    doc_archivo_ids = fields.Many2many(
        'ir.attachment',
        'tu_modelo_doc_archivo_rel',
        'record_id',
        'attachment_id',
        string='Archivos del Servicio'
    )

    fecha_finalizacion = fields.Date(
        string='Fecha de Finalización',
        compute='_compute_fecha_finalizacion',
        store=True,
        readonly=True,
    )
    extra_ids = fields.One2many('rother.servicio.externo.linea', 'servicio_id', string='Servicios Extra')
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
    )
    periodo_display = fields.Char(
        string='Periodo de Renovación',
        compute='_compute_periodo_display',
    )
    precio_total_sin_iva = fields.Float(
        string='Total sin IVA',
        compute='_compute_precios_iva',
        store=True
    )
    precio_total_con_iva = fields.Float(
        string='Total con IVA',
        compute='_compute_precios_iva',
        store=True
    )

    def toggle_alerta(self):
        for record in self:
            record.mostrar_alerta_completa = not record.mostrar_alerta_completa

    @api.depends('precio', 'extra_ids.precio', 'taxes_id')
    def _compute_precios_iva(self):
        for rec in self:
            base = rec.precio + sum(rec.extra_ids.mapped('precio'))
            rec.precio_total_sin_iva = base
            if rec.taxes_id:
                taxes = rec.taxes_id.compute_all(base)
                rec.precio_total_con_iva = taxes['total_included']
            else:
                rec.precio_total_con_iva = base

    @api.depends('fecha_inicio', 'periodo_anios', 'periodo_meses', 'periodo_dias')
    def _compute_fecha_finalizacion(self):
        for rec in self:
            if rec.fecha_inicio and (rec.periodo_anios or rec.periodo_meses or rec.periodo_dias):
                rec.fecha_finalizacion = rec.fecha_inicio + relativedelta(
                    years=rec.periodo_anios,
                    months=rec.periodo_meses,
                    days=rec.periodo_dias,
                )
            else:
                rec.fecha_finalizacion = False

    @api.depends('periodo_anios', 'periodo_meses', 'periodo_dias')
    def _compute_periodo_display(self):
        for rec in self:
            partes = []
            if rec.periodo_anios:
                partes.append(f"{rec.periodo_anios} año(s)")
            if rec.periodo_meses:
                partes.append(f"{rec.periodo_meses} mes(es)")
            if rec.periodo_dias:
                partes.append(f"{rec.periodo_dias} día(s)")
            rec.periodo_display = ', '.join(partes) if partes else False

    @api.model
    def _cron_alerta_fecha_finalizacion(self):
        hoy = fields.Date.today()
        fecha_1_mes = fields.Date.add(hoy, months=1)
        fecha_15_dias = fields.Date.add(hoy, days=15)
        fecha_7_dias = fields.Date.add(hoy, days=7)
        fecha_1_dia = fields.Date.add(hoy, days=1)

        servicios = self.search([
            ('fecha_finalizacion', 'in', [fecha_1_mes, fecha_15_dias, fecha_7_dias, fecha_1_dia])
        ])

        for servicio in servicios:
            dias = (servicio.fecha_finalizacion - hoy).days
            mensaje = Markup("⚠️ El servicio <b>%s</b> finaliza en <b>%s días</b> (%s).") % (servicio.name, dias, servicio.fecha_finalizacion)
            servicio.message_post(
                body=mensaje,
                subject=f"Aviso: {servicio.name} próximo a finalización",
                subtype_xmlid="mail.mt_comment",
                partner_ids=servicio._get_usuarios_notificar(),
            )

    def _get_usuarios_notificar(self):
        usuarios = self.env['res.users'].search([('share', '=', False)])
        return usuarios.mapped('partner_id').ids

    def action_renovar(self):
        for rec in self:
            if rec.fecha_finalizacion and (rec.periodo_anios or rec.periodo_meses or rec.periodo_dias):
                antigua = rec.fecha_finalizacion
                rec.fecha_inicio = rec.fecha_finalizacion
                nueva = rec.fecha_inicio + relativedelta(
                    years=rec.periodo_anios,
                    months=rec.periodo_meses,
                    days=rec.periodo_dias,
                )
                rec.fecha_finalizacion = nueva
                rec.message_post(
                    body=Markup(
                        "🔄 El servicio <b>%s</b> ha sido renovado. Nueva fecha de finalización: <b>%s</b> (anterior: %s)."
                    ) % (rec.name, nueva, antigua),
                    subject=f"Servicio renovado: {rec.name}",
                    subtype_xmlid='mail.mt_comment',
                )

    def action_guardar(self):
        return True


class RotherServicioExternoLinea(models.Model):
    _name = 'rother.servicio.externo.linea'
    _description = 'Línea de Servicio Extra'

    servicio_id = fields.Many2one('rother.servicio.externo', string='Servicio', ondelete='cascade')
    name = fields.Char(string='Nombre', required=True)
    precio = fields.Float(string='Precio', digits='Precio Producto')
    periodo_pago = fields.Char(string='Periodo de Pago')
    fecha_finalizacion = fields.Date(string='Fecha de Finalización')


class ServicioExternoReport(models.Model):
    _name = 'rother.servicio.externo.report'
    _description = 'Análisis Gastos Servicios'
    _auto = False

    name = fields.Char(string='Servicio', readonly=True)
    name_display = fields.Char(string='Servicio (Proveedor)', readonly=True)
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    precio_total = fields.Float(string='Precio Total', readonly=True)
    mes = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'),
        ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
        ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
    ], string='Mes', readonly=True)

    anio = fields.Char(string="Año", readonly=True)

    tipo = fields.Selection([
        ('inicio', 'Contratación'),
        ('renovacion', 'Renovación'),
    ], string='Tipo', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    s.id * 2 AS id,
                    s.name,
                    s.name || ' (' || p.name || ')' AS name_display,
                    s.proveedor_id,
                    s.precio_total_sin_iva AS precio_total,
                    TO_CHAR(s.fecha_inicio, 'MM') AS mes,
                    TO_CHAR(s.fecha_inicio, 'YYYY') AS anio,
                    'inicio' AS tipo
                FROM rother_servicio_externo s
                LEFT JOIN res_partner p ON p.id = s.proveedor_id
                WHERE s.fecha_inicio IS NOT NULL
                AND (
                    s.fecha_finalizacion IS NULL
                    OR TO_CHAR(s.fecha_inicio, 'MM-YYYY') != TO_CHAR(s.fecha_finalizacion, 'MM-YYYY')            
                )

                UNION ALL

                SELECT
                    s.id * 2 + 1 AS id,
                    s.name,
                    s.name || ' (' || p.name || ')' AS name_display,
                    s.proveedor_id,
                    s.precio_total_sin_iva AS precio_total,
                    TO_CHAR(s.fecha_finalizacion, 'MM') AS mes,
                    TO_CHAR(s.fecha_finalizacion, 'YYYY') AS anio,
                    'renovacion' AS tipo
                FROM rother_servicio_externo s
                LEFT JOIN res_partner p ON p.id = s.proveedor_id
                WHERE s.fecha_finalizacion IS NOT NULL

                UNION ALL

                SELECT
                    -(m.n * 1000 + s.id) AS id,
                    s.name,
                    s.name || ' (' || p.name || ')' AS name_display,
                    s.proveedor_id,
                    0 AS precio_total,
                    LPAD(m.n::text, 2, '0') AS mes,
                    TO_CHAR(CURRENT_DATE, 'YYYY') AS anio,
                    'placeholder' AS tipo
                FROM generate_series(1, 12) AS m(n)
                CROSS JOIN rother_servicio_externo s
                LEFT JOIN res_partner p ON p.id = s.proveedor_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM rother_servicio_externo s2
                    WHERE s2.id = s.id
                    AND (
                        TO_CHAR(s2.fecha_inicio, 'MM') = LPAD(m.n::text, 2, '0')
                        OR TO_CHAR(s2.fecha_finalizacion, 'MM') = LPAD(m.n::text, 2, '0')
                    )
                )
            )
        """ % self._table)