from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PayslipEmailWizard(models.TransientModel):
    _name = 'payslip.email.wizard'
    _description = 'Payslip Email Wizard'

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')
    payslip_count = fields.Integer(string='Payslip Count')
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'hr.payslip')],
        default=lambda self: self.env.ref('myis_payslip_email.payslip_email_template', raise_if_not_found=False)
    )
    only_confirmed = fields.Boolean(string='เฉพาะ Payslip ที่ Confirm แล้ว', default=True)
    only_with_email = fields.Boolean(string='เฉพาะพนักงานที่มี Email', default=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            res['payslip_ids'] = [(6, 0, self.env.context.get('active_ids', []))]
            res['payslip_count'] = len(self.env.context.get('active_ids', []))
        return res

    def action_send_emails(self):
        """ส่ง email ให้ payslips ที่เลือก"""
        if not self.email_template_id:
            raise UserError('กรุณาเลือก Email Template')

        payslips = self.payslip_ids

        # กรอง payslips ตามเงื่อนไข
        if self.only_confirmed:
            payslips = payslips.filtered(lambda p: p.state == 'done')

        if self.only_with_email:
            payslips = payslips.filtered(lambda p: p.employee_id.work_email or p.employee_id.user_id.email)

        if not payslips:
            raise UserError('ไม่พบ Payslip ที่ตรงตามเงื่อนไข')

        success_count = 0
        error_count = 0
        error_messages = []

        for payslip in payslips:
            try:
                self.email_template_id.send_mail(payslip.id, force_send=True)
                payslip.write({
                    'email_sent': True,
                    'email_sent_date': fields.Datetime.now()
                })
                success_count += 1
                _logger.info('Email sent to %s' % payslip.employee_id.name)

            except Exception as e:
                error_count += 1
                error_msg = 'พนักงาน %s: %s' % (payslip.employee_id.name, str(e))
                error_messages.append(error_msg)
                _logger.error('Failed to send email to %s: %s' % (payslip.employee_id.name, str(e)))

        # แสดงผลลัพธ์
        message = 'ส่ง Email เสร็จสิ้น:\n'
        message += '✅ สำเร็จ: %d รายการ\n' % success_count
        if error_count > 0:
            message += '❌ ไม่สำเร็จ: %d รายการ\n' % error_count
            message += '\nรายละเอียด Error:\n' + '\n'.join(error_messages[:5])
            if len(error_messages) > 5:
                message += '\n... และอีก %d รายการ' % (len(error_messages) - 5)

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
