from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
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
        """ดึง email ของพนักงาน โดยให้ความสำคัญกับ work_email ก่อน"""
        self.ensure_one()
        return (
            self.employee_id.work_email or 
            (self.employee_id.user_id.email if self.employee_id.user_id else '') or
            ''
        )

    def _check_email_requirements(self):
        """ตรวจสอบความพร้อมในการส่ง email"""
        self.ensure_one()
        
        # ตรวจสอบ payslip state
        if self.state not in ['done', 'paid']:
            raise UserError(
                f'ไม่สามารถส่ง email ได้ เนื่องจาก Payslip ของ {self.employee_id.name} '
                f'อยู่ในสถานะ "{self.state}" (ต้องเป็น "Done" หรือ "Paid")'
            )
        
        # ตรวจสอบ employee email
        employee_email = self._get_employee_email()
        if not employee_email:
            raise UserError(
                f'ไม่พบ email ของพนักงาน {self.employee_id.name}\n'
                'กรุณาตรวจสอบ work_email หรือ user email ในข้อมูลพนักงาน'
            )
        
        return employee_email

    @api.model
    def _get_payslip_email_template(self):
        """ดึง email template สำหรับ payslip"""
        template = self.env.ref(
            'myis_payslip_email.payslip_email_template', 
            raise_if_not_found=False
        )
        if not template:
            raise UserError(
                'ไม่พบ Email Template สำหรับ Payslip\n'
                'กรุณาติดตั้ง module ใหม่หรือติดต่อผู้ดูแลระบบ'
            )
        return template

    def action_send_payslip_email(self):
        """ส่ง email payslip สำหรับ record เดียว"""
        self.ensure_one()

        try:
            # ตรวจสอบความพร้อม
            employee_email = self._check_email_requirements()
            template = self._get_payslip_email_template()
            
            # ส่ง email
            template.with_context(
                timestamp=fields.Datetime.now()
            ).send_mail(self.id, force_send=True)
            
            # อัพเดทสถานะ
            self.write({
                'email_sent': True,
                'email_sent_date': fields.Datetime.now(),
                'email_sent_by': self.env.user.id
            })
            
            # Log message
            self.message_post(
                body=f'Payslip email sent to {employee_email}',
                subject='Payslip Email Sent',
                message_type='notification'
            )
            
            _logger.info(
                f'Payslip email sent successfully to {self.employee_id.name} '
                f'({employee_email}) by {self.env.user.name}'
            )
            
            # แสดง notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Email ส่งสำเร็จ',
                    'message': f'ส่ง Payslip email ให้ {self.employee_id.name} เรียบร้อยแล้ว',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            error_msg = f'ส่ง email ไม่สำเร็จสำหรับ {self.employee_id.name}: {str(e)}'
            _logger.error(error_msg)
            raise UserError(error_msg)

    def action_mass_send_emails(self):
        """เปิด wizard สำหรับส่ง email หลายคน"""
        # กรองเฉพาะ payslips ที่สามารถส่ง email ได้
        valid_payslips = self.filtered(
            lambda p: p.state in ['done', 'paid'] and p._get_employee_email()
        )
        
        if not valid_payslips:
            raise UserError(
                'ไม่พบ Payslip ที่พร้อมส่ง email\n\n'
                'เงื่อนไข:\n'
                '- Payslip ต้องอยู่ในสถานะ "Done" หรือ "Paid"\n'
                '- พนักงานต้องมี email address'
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
                'default_total_selected': len(self),
                'default_filtered_count': len(valid_payslips)
            }
        }

    def action_reset_email_status(self):
        """รีเซ็ต email status (สำหรับ debugging)"""
        self.write({
            'email_sent': False,
            'email_sent_date': False,
            'email_sent_by': False
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Email Status Reset',
                'message': f'รีเซ็ต email status สำหรับ {len(self)} รายการ',
                'type': 'info',
            }
        }
