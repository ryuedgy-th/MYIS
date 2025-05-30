from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    email_sent = fields.Boolean(
        string='Email Sent', 
        default=False,
        help="Indicates if payslip email has been sent to employee"
    )
    email_sent_date = fields.Datetime(
        string='Email Sent Date',
        help="Date and time when payslip email was sent"
    )
    email_sent_by = fields.Many2one(
        'res.users',
        string='Email Sent By',
        help="User who sent the payslip email"
    )

    def _get_employee_email(self):
        """ดึง email ของพนักงาน"""
        self.ensure_one()
        return self.employee_id.work_email or (self.employee_id.user_id.email if self.employee_id.user_id else '')

    def action_send_payslip_email(self):
        """ส่ง email payslip แบบง่าย ๆ"""
        self.ensure_one()

        employee_email = self._get_employee_email()
        if not employee_email:
            raise UserError(f'ไม่พบ email ของพนักงาน {self.employee_id.name}')

        try:
            # ส่ง email แบบง่าย ๆ
            mail_values = {
                'subject': f'สลิปเงินเดือน - {self.employee_id.name}',
                'email_from': 'hr@myis.ac.th',
                'email_to': employee_email,
                'body_html': f'''
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>MYIS International School</h2>
                    <p>เรียน {self.employee_id.name},</p>
                    <p>สลิปเงินเดือนของท่านได้จัดทำเสร็จเรียบร้อยแล้ว</p>
                    <p><strong>ตำแหน่ง:</strong> {self.employee_id.job_id.name or 'ไม่ระบุ'}</p>
                    <p><strong>แผนก:</strong> {self.employee_id.department_id.name or 'ไม่ระบุ'}</p>
                    <p>กรุณาตรวจสอบข้อมูลและแจ้งกลับหากพบข้อผิดพลาด</p>
                    <p>ขอบคุณครับ/ค่ะ<br/>HR Department</p>
                </div>
                ''',
            }
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
            
            # อัพเดทสถานะ
            self.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now(),
                'email_sent_by': self.env.user.id
            })
            
            # Log message
            self.message_post(
                body=f'Payslip email sent to {employee_email}',
                subject='Payslip Email Sent'
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Email ส่งสำเร็จ',
                    'message': f'ส่ง Payslip email ให้ {self.employee_id.name} เรียบร้อยแล้ว',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            error_msg = f'ส่ง email ไม่สำเร็จ: {str(e)}'
            _logger.error(error_msg)
            raise UserError(error_msg)

    def action_mass_send_emails(self):
        """เปิด wizard สำหรับส่ง email หลายคน"""
        valid_payslips = self.filtered(
            lambda p: p.state in ['done', 'paid'] and p._get_employee_email()
        )
        
        if not valid_payslips:
            raise UserError(
                'ไม่พบ Payslip ที่พร้อมส่ง email\n'
                'เงื่อนไข: Payslip ต้องอยู่ในสถานะ "Done" หรือ "Paid" และพนักงานต้องมี email'
            )
        
        return {
            'name': 'Send Payslip Emails',
            'type': 'ir.actions.act_window',
            'res_model': 'payslip.email.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, valid_payslips.ids)],
                'default_payslip_count': len(valid_payslips),
            }
        }
