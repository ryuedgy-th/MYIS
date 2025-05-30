{
    'name': 'MYIS Payslip Email Sender',
    'version': '18.0.1.0.0',
    'summary': 'Send payslip emails to employees',
    'description': """
        Custom module for MYIS International School
        - Send payslip emails to multiple employees
        - Compatible with hr_payroll_community (Community Edition)
        - Custom email templates
        - Mass email functionality
        - Email tracking and status
    """,
    'author': 'MYIS IT Department',
    'website': 'https://myis.ac.th',
    'category': 'Human Resources',
    'depends': [
        'hr_payroll_community',  # ใช้ community edition
        'mail',
        'hr',  # เพิ่ม hr dependency
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'views/hr_payslip_views.xml',
        'wizard/payslip_email_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',  # เพิ่ม license
}
