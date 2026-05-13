<<<<<<< HEAD:__manifest__.py
{
    'name': 'Rother',
    'version': '18.0.1.0.0',
    'category':'Inventory',
    'summary':'Módulo de productos de Rother',
    'author':'Rother Industries & Technologies',
    'depends':['product', 'stock', 'purchase', 'sale', 'mail'],
    'data':[
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/report_template.xml',
        'report/report_label_dymo.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True
=======
{
    'name': 'Rother',
    'version': '18.0-20250930',
    'category':'Inventory',
    'summary':'Módulo de productos de Rother',
    'author':'Rother Industries & Technologies',
    'depends':['product', 'stock', 'purchase', 'sale'],
    'data':[
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'report/report.xml',
        'report/report_template.xml'
        'report/report_label_dymo.xml'
    ],
    'installable': True,
    'application': True
>>>>>>> caf21e96dfddca395d7cbeaec2510e747dc8572e:Odoo-Modules/Rother/__manifest__.py
}