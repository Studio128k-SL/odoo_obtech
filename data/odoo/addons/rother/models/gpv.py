from odoo import models, fields, api

class RotherGPV(models.Model):
    _name = 'rother.gpv'
    _description = 'Grupo de Compra Rother'

    name = fields.Char(string='Número', readonly=True, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    entregar_a = fields.Char(string='Entregar a')
    gpv_linea_ids = fields.One2many('rother.gpv.linea2', 'gpv_id', string='Líneas')
    pv_ids = fields.One2many('rother.pv', 'gpv_id', string='Pedidos Virtuales')
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('rother.gpv') or 'Nuevo'
        return super().create(vals_list)

    @api.depends('gpv_linea_ids.importe_total')
    def _compute_importe_total(self):
        for rec in self:
            rec.importe_total = sum(
                rec.gpv_linea_ids.filtered(lambda l: not l.display_type).mapped('importe_total')
            )

    def action_generar_pv(self):
        for rec in self:

            #Se eliminan los PV existentes para regenerarlos
            rec.pv_ids.unlink()

            # Ordenamos las líneas por secuencia 
            lineas_ordenadas = rec.gpv_linea_ids.sorted('sequence')

            # Construimos un mapa: Cada línea -> proveedor al que pertenece
            # Las secciones y notas "heredan" el proveedor del último producto visto
            lineas_por_proveedor = {} 
            proveedor_actual = None

            # Buffer que guarda la sección actual y sus notas inmediatas,
            # para volcarlas a cada proveedor de la sección
            buffer_seccion = []

            for linea in lineas_ordenadas:
                
                if linea.display_type == 'line_section':
                    # Nueva sección: resetear el buffer con esta sección.
                    # El proveedor también se resetea porque cambia de contexto
                    buffer_seccion = [linea]
                    proveedor_actual = None
                
                elif linea.display_type == 'line_note':
                    if proveedor_actual:
                        # Nota inmediata a un producto
                        # Se asocia al mismo proveedor que el producto
                        lineas_por_proveedor[proveedor_actual].append(linea)
                    else:
                        # Nota inmediata a una sección (sin producto)
                        # Se guarda en el buffer para volcarse con la sección
                        buffer_seccion.append(linea)
                
                else:
                    # Linea de producto normal
                    proveedor_actual = linea.proveedor_id

                    if proveedor_actual:
                        if proveedor_actual not in lineas_por_proveedor:
                            # Proveedor nuevo: Inicializa su lista y vuelca el buffer
                            # (sección + notas de sección) si hay.
                            lineas_por_proveedor[proveedor_actual] = []
                            if buffer_seccion:
                                lineas_por_proveedor[proveedor_actual].extend(buffer_seccion)
                        
                        lineas_por_proveedor[proveedor_actual].append(linea)
            
            # Crea un PV por cada proveedor con líneas ordenadas
            for proveedor, lineas in lineas_por_proveedor.items():
                pv = self.env['rother.pv'].create({
                    'gpv_id': rec.id,
                    'proveedor_id': proveedor.id,
                })
                for linea in lineas:
                    self.env['rother.pv.linea'].create({
                        'pv_id': pv.id,
                        'product_id': linea.product_id.id if not linea.display_type else False,
                        'nombre': linea.name,
                        'cantidad': linea.cantidad if not linea.display_type else 0,
                        'precio_unitario': linea.precio_unitario if not linea.display_type else 0,
                        'taxes_id': [(6,0, linea.taxes_id.ids)] if not linea.display_type else [],
                        'importe_total': linea.importe_total if not linea.display_type else 0,
                        # El nombre del proyecto solo se extrae en líneas de tipo sección
                        'seccion_nombre': linea.project_id.name if linea.display_type == 'line_section' and linea.project_id else '',
                        'display_type': linea.display_type or False,
                    })


class RotherGPVLinea2(models.Model):
    _name = 'rother.gpv.linea2'
    _description = 'Línea de GPV'

    gpv_id = fields.Many2one('rother.gpv', string='GPV', ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', default=10)
    display_type = fields.Selection([
        ('line_section', 'Sección'),
        ('line_note', 'Nota'),
    ], default=False)
    name = fields.Char(string='Nombre')
    project_id = fields.Many2one('project.project', string='Proyecto')
    product_id = fields.Many2one('product.product', string='Producto')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)
    proveedor_id = fields.Many2one('res.partner', string='Proveedor')

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


class RotherGPVLinea(models.Model):
    _name = 'rother.gpv.linea'
    _description = 'Línea de GPV antigua'

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
    referencia_gpv = fields.Char(string='Referencia GPV', related='gpv_id.name', store=True)
    llegada_prevista = fields.Date(string='Llegada Prevista')
    linea_ids = fields.One2many('rother.pv.linea', 'pv_id', string='Líneas')
    purchase_order_id = fields.Many2one('purchase.order', string='Pedido de Compra', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('order_created', 'Pedido Creado'),
        ('confirmed', 'Confirmado'),
    ], string='Estado', default='draft', readonly=True)

    @api.onchange('proveedor_id')
    def _onchange_proveedor_id(self):
        if self.proveedor_id:
            self.referencia_proveedor = self.proveedor_id.ref

    def action_crear_pedido(self):
        for rec in self:
            if rec.purchase_order_id:
                continue
            order_lines = []
            for linea in rec.linea_ids:
                if linea.display_type:
                    order_lines.append((0, 0, {
                        'display_type': linea.display_type,
                        'name': linea.nombre if linea.nombre else '-',
                        'product_qty': 0,
                        'price_unit': 0,
                        'date_planned': rec.llegada_prevista or fields.Date.today(),
                    }))
                else:
                    order_lines.append((0, 0, {
                        'product_id': linea.product_id.id,
                        'name': linea.nombre if linea.nombre else linea.product_id.name,
                        'product_qty': linea.cantidad,
                        'price_unit': linea.precio_unitario,
                        'taxes_id': [(6, 0, linea.taxes_id.ids)],
                        'date_planned': rec.llegada_prevista or fields.Date.today(),
                        'product_uom': linea.product_id.uom_po_id.id,
                    }))
            purchase_order = self.env['purchase.order'].create({
                'partner_id': rec.proveedor_id.id,
                'partner_ref': rec.referencia_proveedor,
                'origin': rec.referencia_gpv,
                'date_planned': rec.llegada_prevista,
                'order_line': order_lines,
            })
            rec.purchase_order_id = purchase_order.id
            rec.state = 'order_created'

    def action_confirmar_pedido(self):
        for rec in self:
            if rec.purchase_order_id:
                rec.purchase_order_id.button_confirm()
                rec.state = 'confirmed'


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
    display_type = fields.Selection([
        ('line_section', 'Sección'),
        ('line_note', 'Nota'),
    ], default = False)