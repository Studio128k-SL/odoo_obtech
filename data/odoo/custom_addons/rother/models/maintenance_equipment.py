from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    x_soc_activo = fields.Boolean(string='SOC')
    x_soc_nombre = fields.Char(string='Nombre SOC')

    x_edr_activo = fields.Boolean(string='EDR')
    x_edr_nombre = fields.Char(string='Nombre EDR')