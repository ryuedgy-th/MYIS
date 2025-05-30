from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    email_sent = fields.Boolean(string='Email Sent', default=False)
    email_sent_date = fields.Datetime(string='Email Sent Date')

    def action_send_payslip_email(self):
        """ส่ง email payslip สำหรับ record เดียว"""
        self.ensure_one()

        if not (self.employee_id.work_email or self.employee_id.user_id.email):
            raise UserError('ไม่พบ email ของพนักงาน %s' % self.employee_id.name)

        template = self.env.ref('myis_payslip_email.payslip_email_template', raise_if_not_found=False)
        if not template:
            raise UserError('ไม่พบ Email Template')

        try:
            template.send_mail(self.id, force_send=True)
            self.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now()
            })
            self.message_post(
                body='Payslip email sent to %s' % (self.employee_id.work_email or self.employee_id.user_id.email),
                subject='Payslip Email Sent'
            )
            return True
        except Exception as e:
            _logger.error('Failed to send payslip email: %s' % str(e))
            raise UserError('ส่ง email ไม่สำเร็จ: %s' % str(e))

    def action_mass_send_emails(self):
        """เปิด wizard สำหรับส่ง email หลายคน"""
        return {
            'name': 'Send Payslip Emails',
            'type': 'ir.actions.act_window',
            'res_model': 'payslip.email.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, self.ids)],
                'default_payslip_count': len(self.ids)
            }
        }
