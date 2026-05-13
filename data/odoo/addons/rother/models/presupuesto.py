from odoo import models, fields, api

class RotherPresupuesto(models.Model) :
    _name="rother.presupuesto"
    _description="Presupuesto Rother"

    name = fields.Char(string="Número", readOnly=True, default="Nuevo")
    fecha = fields.Date(string ="Fecha", default=fields.Date.today)
    seccion_ids="fields.One2many"('rother.presupuesto.seccion', 'presupuesto_id', string="Secciones")
    importe_total=fields.Float(string="Importe total", compute="_compute_importe_total", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo" :
                vals["name"] = self.env["ir.sequence"].next_by_code("rother.presupuesto") or "Nuevo"
        return super().create(vals_list)
    
    @api.depends('seccion_ids.importe_total')
    def _compute_importe_total(self):
        for rec in self:
            rec.importe_total = sum(rec.seccion_ids.mapped('importe_total'))

class RotherPresupuestoSeccion(models.Model):
    _name = "rother.presupuesto.seccion"
    _description = "Sección de Presupuesto Rother"

    name= fields.Char(string="Nombre del proyecto", required=True)
    presupuesto_id=fields.Many2one("rother.presupuesto", string="Presupuesto", ondelete="cascade")
    linea_ids = fields.One2many("rother.presupuesto.linea", "seccion.id", string="Líneas")
    importe_total = fields.Float(string="Importe Total", compute="_compute_importe_total", store=True)

    @api.depends("linea_ids.importe_total")
    def _compute_importe_total(self):
        for rec in self:
            rec.importe_total = sum(rec.linea_ids.mapped("importe_total"))

class RotherPresupuestoLinea(models.Model):
    _name="rother.presupuesto.linea"
    _description="Línea de Presupuesto Rother"

    seccion_id=fields.Many2one("rother.presupuesto.seccion", string="Sección", ondelete="cascade")        
    product_id=fields.Many2one("product.template", string="Producto", required=True)
    nombre = fields.Char(string="Nombre", related="product_id.name", store=True)
    cantidad= fields.Float(string="Cantidad", default=1.0)
    precio_unitario=fields.Float(string="Precio Unitario")
    taxes_id= fields.Many2many("account.tax", string="Impuestos")
    proveedor_id= fields.Many2one("res.partner", string="Proveedor", related="product_id.seller_ids.partner_id", store= True, readOnly=True) 
    importe_total= fields.Float(string="Importe total", compute="_compute_importe_total", store= True)

    @api.depends("cantidad", "precio_unitario", "taxes_id")
    def _compute_importe_total(self):
        for rec in self:
            subtotal = rec.cantidad * rec.precio_unitario
            if rec.taxes_id:
                taxes = rec.taxes_id.compute_all(subtotal)
                rec.importe_total = taxes['total_included']       
            else:
                rec.importe_total = subtotal