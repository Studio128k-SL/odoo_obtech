from odoo import models, fields, api

class RotherGPV(models.Model):
    _name = 'rother.gpv'
    _description = 'Grupo de Compra Rother'
    _inherit=['product.catalog.mixin']

    name = fields.Char(string='Número', readonly=True, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    entregar_a_id = fields.Many2one('res.partner', string='Entregar a')
    gpv_linea_ids = fields.One2many('rother.gpv.linea2', 'gpv_id', string='Líneas')
    pv_ids = fields.One2many('rother.pv', 'gpv_id', string='Pedidos Virtuales')
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Hecho'),
    ], string='Estado', default='draft')
        
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('rother.gpv') or 'Nuevo'
        records = super().create(vals_list)
        for rec in records:
            rec.action_generar_pv()
        return records

    @api.depends('gpv_linea_ids.importe_total')
    def _compute_importe_total(self):
        for rec in self:
            rec.importe_total = sum(
                rec.gpv_linea_ids.filtered(lambda l: not l.display_type).mapped('importe_total')
            )

    def action_generar_pv(self):
        for rec in self:
            # Se borran todos los pedidos asociados a los PV antes de eliminar estos
            for pv in rec.pv_ids:
                for po in pv.purchase_order_ids:
                    for picking in po.picking_ids:
                        if picking.state not in ('done', 'cancel'):
                            picking.action_cancel()
                    if po.state not in ('cancel',):
                        po.button_cancel()
                pv.purchase_order_ids.unlink()
            rec.pv_ids.unlink()

            lineas_ordenadas = rec.gpv_linea_ids.sorted('sequence')

            lineas_por_proveedor = {}
            proveedor_actual = None

            # Sección de proyecto actual (con project_id)
            seccion_proyecto_actual = None
            # Sección de documentación actual (sin project_id)
            seccion_doc_actual = None
            # Notas acumuladas tras la sección de documentación, antes del primer producto
            notas_doc_actual = []

            # Rastrea qué proveedores ya recibieron la sección de proyecto actual
            proyecto_volcado_a = set()
            # Rastrea qué proveedores ya recibieron la sección de doc actual + sus notas previas
            doc_volcado_a = set()

            for linea in lineas_ordenadas:

                if linea.display_type == 'line_section' and linea.project_id:
                    # Nueva sección de proyecto: resetear todo el contexto
                    seccion_proyecto_actual = linea
                    seccion_doc_actual = None
                    notas_doc_actual = []
                    proveedor_actual = None
                    proyecto_volcado_a = set()
                    doc_volcado_a = set()

                elif linea.display_type == 'line_section' and not linea.project_id:
                    # Nueva sección de documentación dentro del proyecto actual
                    seccion_doc_actual = linea
                    notas_doc_actual = []
                    proveedor_actual = None
                    doc_volcado_a = set()

                elif linea.display_type == 'line_note':
                    if proveedor_actual:
                        # Nota tras producto: va al proveedor del producto anterior
                        lineas_por_proveedor[proveedor_actual].append(linea)
                    else:
                        # Nota tras sección doc sin producto aún: acumular
                        notas_doc_actual.append(linea)

                else:
                    # Producto normal
                    proveedor_actual = linea.proveedor_id

                    if proveedor_actual:
                        if proveedor_actual not in lineas_por_proveedor:
                            lineas_por_proveedor[proveedor_actual] = []

                        # Volcar sección de proyecto si aún no se volcó a este proveedor
                        if proveedor_actual not in proyecto_volcado_a and seccion_proyecto_actual:
                            lineas_por_proveedor[proveedor_actual].append(seccion_proyecto_actual)
                            proyecto_volcado_a.add(proveedor_actual)

                        # Volcar sección de doc + sus notas previas si aún no se volcó a este proveedor
                        if proveedor_actual not in doc_volcado_a and seccion_doc_actual:
                            lineas_por_proveedor[proveedor_actual].append(seccion_doc_actual)
                            lineas_por_proveedor[proveedor_actual].extend(notas_doc_actual)
                            doc_volcado_a.add(proveedor_actual)

                        lineas_por_proveedor[proveedor_actual].append(linea)

            # Crear un PV por proveedor con sus líneas en orden
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
                        'ref_fabricante': linea.ref_fabricante if not linea.display_type else '',
                        'ref_proveedor_producto': linea.ref_proveedor_producto if not linea.display_type else '',
                        'cantidad': linea.cantidad if not linea.display_type else 0,
                        'precio_unitario': linea.precio_unitario if not linea.display_type else 0,
                        'taxes_id': [(6, 0, linea.taxes_id.ids)] if not linea.display_type else [],
                        'descuento': linea.descuento if not linea.display_type else 0,
                        'importe_total': linea.importe_total if not linea.display_type else 0,
                        'seccion_nombre': linea.project_id.name if linea.display_type == 'line_section' and linea.project_id else '',
                        'display_type': linea.display_type or False,
                    })

    def action_open_product_catalog(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Catálogo de Productos',
            'res_model': 'product.product',
            'view_mode': 'kanban,list,form',
            'target': 'new',
        }

    def _get_action_add_from_catalog_extra_context(self):
        return {
            'order_id': self.id,
            'product_catalog_order_id': self.id,
            'product_catalog_order_model': self._name,
        }

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        line = self.gpv_linea_ids.filtered(lambda l: l.product_id.id == product_id)
        product = self.env['product.product'].browse(product_id)
        if line:
            if quantity == 0:
                line.unlink()
            else:
                line.cantidad = quantity
        elif quantity > 0:
            self.env['rother.gpv.linea2'].create({
                'gpv_id': self.id,
                'product_id': product_id,
                'name': product.name,
                'cantidad': quantity,
                'precio_unitario': product.lst_price,
                'taxes_id': [(6, 0, product.taxes_id.ids)],
                'ref_fabricante': product.x_Ref_fab or '',
            })
        return product.lst_price    
    
    def write(self, vals):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("GPV write llamado con vals: %s", list(vals.keys()))
        result = super().write(vals)
        if 'gpv_linea_ids' in vals:
            _logger.info("Regenerando PVs...")
            for rec in self:
                rec.action_generar_pv()
        return result
    
    def unlink(self):
        for rec in self:
            for pv in rec.pv_ids:
                for po in pv.purchase_order_ids:
                    # Cancelar recepciones asociadas
                    for recepcion in po.picking_ids:
                        if recepcion.state not in ('done', 'cancel'):
                            recepcion.action_cancel()
                    # Cancelar el pedido si está confirmado
                    if po.state not in ('cancel',):
                        po.button_cancel()
                pv.purchase_order_ids.unlink()
        return super().unlink()
    

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
    ref_fabricante = fields.Char(string='Ref. Fabricante', compute='_compute_ref_fabricante', store=True)
    ref_proveedor_producto = fields.Char(string = 'Ref. Proveedor')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    descuento = fields.Float(string='Descuento (%)', default = 0.0)
    importe_total = fields.Float(string='Importe Total', compute='_compute_importe_total', store=True)
    proveedor_id = fields.Many2one('res.partner', string='Proveedor')
    currency_id = fields.Many2one('res.currency', string='Moneda', related='gpv_id.company_id.currency_id', store=True)

    @api.depends('cantidad', 'precio_unitario', 'taxes_id', 'display_type')
    def _compute_importe_total(self):
        for rec in self:
            if rec.display_type:
                rec.importe_total = 0.0
            else:
                subtotal = rec.cantidad * rec.precio_unitario * (1 - rec.descuento/100)
                if rec.taxes_id:
                    taxes = rec.taxes_id.compute_all(subtotal)
                    rec.importe_total = taxes['total_included']
                else:
                    rec.importe_total = subtotal

    @api.onchange('product_id', 'proveedor_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Estos siempre se rellenan independientemente del proveedor
            self.precio_unitario = self.product_id.lst_price
            self.taxes_id = self.product_id.taxes_id
            self.ref_fabricante = self.product_id.x_Ref_fab
            self.name = self.product_id.name

            # Buscar referencia del proveedor seleccionado
            supplier_info = self.product_id.seller_ids.filtered(
                lambda s: s.partner_id == self.proveedor_id
            )[:1]

            if supplier_info:
                self.ref_proveedor_producto = supplier_info.product_code or ''
            else:
                self.ref_proveedor_producto = ''
    
    @api.depends('product_id')
    def _compute_ref_fabricante(self):
        for rec in self:
            rec.ref_fabricante = rec.product_id.x_Ref_fab if rec.product_id else ''


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
    purchase_order_ids = fields.One2many('purchase.order', 'rother_pv_id', string='Pedidos de Compra', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('order_created', 'Pedido Creado'),
        ('confirmed', 'Confirmado'),
    ], string='Estado', default='draft', readonly=True)
    recepcion_count = fields.Integer(
        string='Recepciones',
        compute='_compute_reception_count'
    )

    @api.onchange('proveedor_id')
    def _onchange_proveedor_id(self):
        if self.proveedor_id:
            self.referencia_proveedor = self.proveedor_id.ref

    @api.depends('purchase_order_ids')
    def _compute_reception_count(self):
        for rec in self:
            pickings = rec.purchase_order_ids.mapped('picking_ids')
            rec.reception_count = len(pickings)

    def action_ver_recepciones(self):
        pickings = self.purchase_order_ids.mapped('picking_ids')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recepciones',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pickings.ids)],
            'context': {'list_view_ref': 'rother.rother_stock_picking_list_view'},
        }


    def action_crear_pedido(self):
        for rec in self:
            if rec.purchase_order_ids:
                continue

            # Ordenar las líneas para procesarlas en orden
            lineas_ordenadas = rec.linea_ids.sorted('id')

            # Agrupar líneas por proyecto
            # {project_id: [lineas]}
            lineas_por_proyecto = {}
            proyecto_actual = None

            for linea in lineas_ordenadas:
                if linea.display_type == 'line_section' and linea.seccion_nombre:
                    #Sección de proyecto: Busca por nombre
                    proyecto_actual = self.env['project.project'].search(
                        [('name', '=', linea.seccion_nombre)], limit = 1
                    )
                    lineas_por_proyecto.setdefault(proyecto_actual, [])
                    lineas_por_proyecto[proyecto_actual].append(linea)
                else:
                    # Resto de líneas: Van al proyecto actual
                    if proyecto_actual is not None:
                        lineas_por_proyecto[proyecto_actual].append(linea)
                    
            #Crear una solicitud de presupuesto por proyecto
            purchase_orders = []
            for proyecto, lineas in lineas_por_proyecto.items():
                order_lines = []
                for linea in lineas:
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
                    'project_id': proyecto.id if proyecto else False,
                    'date_planned': rec.llegada_prevista,
                    'rother_pv_id': rec.id,
                    'order_line': order_lines,
                })
                purchase_orders.append(purchase_order)
            
            # Se guarda la primera solicitud en purchase_order_id (referencia principal)
            # Las demás quedan vinculadas por origin y project_id
            if purchase_orders:
                rec.state = 'order_created'

    def action_confirmar_pedido(self):
        for rec in self:
            for purchase_order in rec.purchase_order_ids:
                purchase_order.button_confirm()
            rec.state = 'confirmed' 


class RotherPVLinea(models.Model):
    _name = 'rother.pv.linea'
    _description = 'Línea de PV Rother'

    pv_id = fields.Many2one('rother.pv', string='PV', ondelete='cascade')
    gpv_linea_id = fields.Many2one('rother.gpv.linea', string='Línea GPV')
    product_id = fields.Many2one('product.product', string='Producto')
    nombre = fields.Char(string='Nombre')
    ref_fabricante = fields.Char(string='Ref. Fabricante')
    ref_proveedor_producto = fields.Char(string='Ref. Proveedor')
    cantidad = fields.Float(string='Cantidad')
    precio_unitario = fields.Float(string='Precio Unitario')
    taxes_id = fields.Many2many('account.tax', string='Impuestos')
    descuento = fields.Float(string='Descuento (%)', default= 0.0)
    importe_total = fields.Float(string='Importe Total')
    seccion_nombre = fields.Char(string='Proyecto')
    display_type = fields.Selection([
        ('line_section', 'Sección'),
        ('line_note', 'Nota'),
    ], default = False)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='pv_id.gpv_id.company_id.currency_id', store=True)