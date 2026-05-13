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
}