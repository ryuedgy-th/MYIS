from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    email_sent = fields.Boolean(string='Email Sent', default=False)
    email_sent_date = fields.Datetime(string='Email Sent Date')

    def action_send_payslip_email(self):
        """ส่ง email payslip"""
        self.ensure_one()
        
        # หา email ของพนักงาน
        employee_email = self.employee_id.work_email or (
            self.employee_id.user_id.email if self.employee_id.user_id else None
        )
        
        if not employee_email:
            raise UserError(f'ไม่พบ email ของพนักงาน {self.employee_id.name}')

        try:
            # สร้าง email ง่าย ๆ
            self.env['mail.mail'].create({
                'subject': f'Payslip - {self.employee_id.name}',
                'email_from': 'hr@myis.ac.th',
                'email_to': employee_email,
                'body_html': f'''
                <p>Dear {self.employee_id.name},</p>
                <p>Your payslip is ready.</p>
                <p>Best regards,<br/>HR Department<br/>MYIS International School</p>
                ''',
            }).send()
            
            # อัพเดทสถานะ
            self.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now()
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Email sent to {self.employee_id.name}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f'Failed to send email: {e}')
            raise UserError(f'Failed to send email: {e}')
