{
    'name': 'Rother',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Módulo de Rother',
    'author': 'Rother Industries & Technologies',
    'license': 'LGPL-3',
    'depends': ['product', 'stock', 'purchase', 'sale', 'mail', 'project', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/cron_servicio_externo.xml',
        'report/report.xml',
        'report/report_template.xml',
        'report/report_label_dymo.xml',
        'report/gpv_report.xml',
        'report/balance_servicios_report.xml',
        'views/gpv_views.xml',
        'views/product_label_wizard_views.xml',
        'views/product_views.xml',
        'views/presupuesto_views.xml',
        'views/stock_views.xml',
        'views/servicio_externo_views.xml',
        'views/maintenance_equipment_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'rother/static/src/css/gpv.css',
        ],
    },
    'installable': True,
    'application': True,
}