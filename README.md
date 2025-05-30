# MYIS Payslip Email Sender

Custom Odoo 18 module for MYIS International School to send payslip emails to employees.

## 🚀 Features

- **Individual Email Sending**: Send payslip email to single employee
- **Mass Email Functionality**: Send emails to multiple employees at once
- **Email Status Tracking**: Track sent emails with timestamp and sender
- **Resend Capability**: Resend emails if needed
- **Custom Email Template**: Professional Thai language email template
- **Smart Filtering**: Filter payslips by status, email availability, etc.
- **Security Integration**: Proper access control for HR staff
- **Preview Recipients**: Preview who will receive emails before sending

## 📋 Requirements

- Odoo 18.0 Community Edition
- `hr_payroll_community` module
- `mail` module
- `hr` module

## 🔧 Installation

1. **Download/Clone the module:**
   ```bash
   cd /path/to/odoo/addons/
   git clone https://github.com/ryuedgy-th/MYIS.git
   ```

2. **Restart Odoo server:**
   ```bash
   sudo systemctl restart odoo
   ```

3. **Install the module:**
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "MYIS Payslip Email Sender"
   - Click Install

## 📖 Usage

### Send Individual Email

1. Navigate to **Payroll > Payslips**
2. Open a confirmed payslip
3. Click **"Send Email"** button in the header
4. Email will be sent automatically to employee's work email

### Send Mass Emails

1. Navigate to **Payroll > Payslips**
2. Select multiple payslips (use checkboxes)
3. Go to **Action menu > Send Payslip Emails**
4. Configure filter options in the wizard:
   - ✅ Only confirmed payslips
   - ✅ Only employees with email
   - ✅ Skip already sent payslips
5. Preview recipients if needed
6. Click **"ส่ง Emails"** to send

### Email Status Tracking

- **Email Sent**: Boolean field showing if email was sent
- **Email Sent Date**: Timestamp of when email was sent
- **Email Sent By**: User who sent the email
- **Search Filters**: Filter by email status in list view

## 🎨 Email Template Features

The custom email template includes:

- **Professional Thai Design**: MYIS branded template
- **Payslip Details**: Employee info, period, net salary
- **Status Information**: Payslip approval status
- **Verification Checklist**: Items for employee to verify
- **Contact Information**: HR contact details for questions
- **Responsive Design**: Works on mobile and desktop

## 🔐 Security & Permissions

| Group | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| Payroll Manager | ✅ | ✅ | ✅ | ✅ |
| Payroll User | ✅ | ✅ | ✅ | ✅ |
| HR Officer | ✅ | ✅ | ✅ | ❌ |

## 📁 Module Structure

```
myis_payslip_email/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── hr_payslip.py
├── wizard/
│   ├── __init__.py
│   ├── payslip_email_wizard.py
│   └── payslip_email_wizard_views.xml
├── views/
│   └── hr_payslip_views.xml
├── data/
│   └── email_template.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## 🔄 Changelog

### Version 18.0.1.0.0
- Initial release
- Individual email sending
- Mass email wizard
- Email status tracking
- Custom Thai email template
- Security integration

## 🛠️ Configuration

### Email Server Setup
Ensure your Odoo instance has mail server configured:
1. Go to **Settings > Technical > Email > Outgoing Mail Servers**
2. Configure SMTP settings
3. Test the connection

### Employee Email Setup
Make sure employees have email addresses:
- **Work Email**: Preferred (hr_payslip uses this first)
- **User Email**: Fallback option

## 🐛 Troubleshooting

### Common Issues

**Email not sending?**
- Check mail server configuration
- Verify employee has email address
- Check payslip is in 'Done' or 'Paid' state
- Review Odoo logs for detailed errors

**Permission errors?**
- Ensure user is in correct security group
- Check access rights in Security settings

**Template not found?**
- Reinstall the module
- Check if email template exists in Settings > Technical > Email Templates

## 📞 Support

For issues and questions:
- **Email**: hr@myis.ac.th
- **GitHub Issues**: [Create an issue](https://github.com/YOUR_USERNAME/myis_payslip_email/issues)

## 📄 License

This module is licensed under LGPL-3.

---

**Developed by MYIS IT Department**  
*MYIS International School*
