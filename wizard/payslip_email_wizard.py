from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PayslipEmailWizard(models.TransientModel):
    _name = 'payslip.email.wizard'
    _description = 'Payslip Email Wizard'

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')
    payslip_count = fields.Integer(string='Payslip Count')
    
    # Simple options
    only_confirmed = fields.Boolean(string='เฉพาะ Payslip ที่ Confirm แล้ว', default=True)
    only_with_email = fields.Boolean(string='เฉพาะพนักงานที่มี Email', default=True)
    skip_already_sent = fields.Boolean(string='ข้าม Payslip ที่ส่งแล้ว', default=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['payslip_ids'] = [(6, 0, active_ids)]
            res['payslip_count'] = len(active_ids)
        return res

    def action_send_emails(self):
        """ส่ง email ให้ payslips ที่เลือก"""
        payslips = self.payslip_ids

        # กรอง payslips ตามเงื่อนไข
        if self.only_confirmed:
            payslips = payslips.filtered(lambda p: p.state in ['done', 'paid'])

        if self.only_with_email:
            payslips = payslips.filtered(
                lambda p: p.employee_id.work_email or 
                (p.employee_id.user_id and p.employee_id.user_id.email)
            )
            
        if self.skip_already_sent:
            payslips = payslips.filtered(lambda p: not p.email_sent)

        if not payslips:
            raise UserError('ไม่พบ Payslip ที่ตรงตามเงื่อนไข')

        success_count = 0
        error_count = 0
        error_messages = []

        for payslip in payslips:
            try:
                employee_email = (
                    payslip.employee_id.work_email or 
                    (payslip.employee_id.user_id.email if payslip.employee_id.user_id else '')
                )
                
                if not employee_email:
                    raise Exception('ไม่พบ email address')

                # ส่ง email แบบง่าย ๆ
                mail_values = {
                    'subject': f'สลิปเงินเดือน - {payslip.employee_id.name}',
                    'email_from': 'hr@myis.ac.th',
                    'email_to': employee_email,
                    'body_html': f'''
                    <div style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>MYIS International School</h2>
                        <p>เรียน {payslip.employee_id.name},</p>
                        <p>สลิปเงินเดือนของท่านได้จัดทำเสร็จเรียบร้อยแล้ว</p>
                        <p><strong>ตำแหน่ง:</strong> {payslip.employee_id.job_id.name or 'ไม่ระบุ'}</p>
                        <p><strong>แผนก:</strong> {payslip.employee_id.department_id.name or 'ไม่ระบุ'}</p>
                        <p>กรุณาตรวจสอบข้อมูลและแจ้งกลับหากพบข้อผิดพลาด</p>
                        <p>ขอบคุณครับ/ค่ะ<br/>HR Department</p>
                    </div>
                    ''',
                }
                
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
                
                # อัพเดทสถานะ
                payslip.write({
                    'email_sent': True,
                    'email_sent_date': fields.Datetime.now(),
                    'email_sent_by': self.env.user.id
                })
                
                success_count += 1
                _logger.info(f'Email sent to {payslip.employee_id.name} ({employee_email})')

            except Exception as e:
                error_count += 1
                error_msg = f'{payslip.employee_id.name}: {str(e)}'
                error_messages.append(error_msg)
                _logger.error(f'Failed to send email to {payslip.employee_id.name}: {str(e)}')

        # แสดงผลลัพธ์
        message = f'ส่ง Email เสร็จสิ้น:\n✅ สำเร็จ: {success_count} รายการ'
        if error_count > 0:
            message += f'\n❌ ไม่สำเร็จ: {error_count} รายการ'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ผลการส่ง Email',
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
