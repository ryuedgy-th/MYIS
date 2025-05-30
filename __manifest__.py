{
    'name': 'MYIS Payslip Email Sender',
    'version': '18.0.1.0.0',
    'summary': 'Send payslip emails to employees',
    'description': """
        Custom module for MYIS International School
        - Send payslip emails to multiple employees
        - Email tracking and status
        - Mass email functionality
    """,
    'author': 'MYIS IT Department',
    'website': 'https://myis.ac.th',
    'category': 'Human Resources',
    'depends': [
        'hr',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'wizard/payslip_email_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
