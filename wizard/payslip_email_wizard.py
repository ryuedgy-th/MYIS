from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PayslipEmailWizard(models.TransientModel):
    _name = 'payslip.email.wizard'
    _description = 'Payslip Email Wizard'

    payslip_ids = fields.Many2many(
        'hr.payslip', 
        string='Payslips',
        help="Payslips to send emails for"
    )
    payslip_count = fields.Integer(
        string='Payslip Count',
        help="Number of payslips ready to send"
    )
    total_selected = fields.Integer(
        string='Total Selected',
        help="Total number of payslips originally selected"
    )
    filtered_count = fields.Integer(
        string='Filtered Count',
        help="Number of payslips after filtering"
    )
    
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'hr.payslip')],
        required=True,
        help="Email template to use for sending payslip emails"
    )
    
    # Filter options
    only_confirmed = fields.Boolean(
        string='เฉพาะ Payslip ที่ Confirm แล้ว', 
        default=True,
        help="Only include confirmed payslips (state = done or paid)"
    )
    only_with_email = fields.Boolean(
        string='เฉพาะพนักงานที่มี Email', 
        default=True,
        help="Only include employees with valid email addresses"
    )
    skip_already_sent = fields.Boolean(
        string='ข้าม Payslip ที่ส่งแล้ว',
        default=True,
        help="Skip payslips that have already been sent"
    )
    
    # Summary fields
    preview_count = fields.Integer(
        string='จำนวนที่จะส่ง',
        compute='_compute_preview_count',
        help="Number of emails that will be sent based on current filters"
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get payslips from context
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['payslip_ids'] = [(6, 0, active_ids)]
            res['payslip_count'] = len(active_ids)
            res['total_selected'] = self.env.context.get('default_total_selected', len(active_ids))
            res['filtered_count'] = self.env.context.get('default_filtered_count', len(active_ids))
        
        # Set default template
        template = self.env.ref(
            'myis_payslip_email.payslip_email_template', 
            raise_if_not_found=False
        )
        if template:
            res['email_template_id'] = template.id
            
        return res

    @api.depends('payslip_ids', 'only_confirmed', 'only_with_email', 'skip_already_sent')
    def _compute_preview_count(self):
        for wizard in self:
            payslips = wizard._get_filtered_payslips()
            wizard.preview_count = len(payslips)

    def _get_filtered_payslips(self):
        """ดึง payslips ที่ผ่านการกรองตามเงื่อนไข"""
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

        return payslips

    def action_preview_recipients(self):
        """แสดงรายชื่อผู้รับที่จะได้รับ email"""
        payslips = self._get_filtered_payslips()
        
        if not payslips:
            raise UserError('ไม่พบ Payslip ที่ตรงตามเงื่อนไข')
        
        # สร้าง list view แสดงรายชื่อ
        action = {
            'name': f'ผู้รับ Email ({len(payslips)} รายการ)',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'tree',
            'target': 'new',
            'domain': [('id', 'in', payslips.ids)],
            'context': {'create': False, 'edit': False, 'delete': False}
        }
        return action

    @api.model
    def _validate_email_template(self, template_id):
        """ตรวจสอบ email template"""
        if not template_id:
            raise UserError('กรุณาเลือก Email Template')
        
        template = self.env['mail.template'].browse(template_id)
        if not template.exists():
            raise UserError('ไม่พบ Email Template ที่เลือก')
        
        if template.model != 'hr.payslip':
            raise UserError('Email Template ต้องเป็นสำหรับ model hr.payslip เท่านั้น')
            
        return template

    def action_send_emails(self):
        """ส่ง email ให้ payslips ที่เลือก"""
        # Validate template
        template = self._validate_email_template(self.email_template_id.id)
        
        # Get filtered payslips
        payslips = self._get_filtered_payslips()
        
        if not payslips:
            raise UserError(
                'ไม่พบ Payslip ที่ตรงตามเงื่อนไข\n\n'
                'กรุณาตรวจสอบ:\n'
                '- Payslip ต้องอยู่ในสถานะ "Done" หรือ "Paid"\n'
                '- พนักงานต้องมี email address\n'
                '- ยังไม่เคยส่ง email (ถ้าเลือกข้าม Payslip ที่ส่งแล้ว)'
            )

        # Send emails
        success_count = 0
        error_count = 0
        error_details = []
        
        total_payslips = len(payslips)
        _logger.info(f'Starting to send {total_payslips} payslip emails')

        for i, payslip in enumerate(payslips, 1):
            try:
                # Get employee email
                employee_email = (
                    payslip.employee_id.work_email or 
                    (payslip.employee_id.user_id.email if payslip.employee_id.user_id else '')
                )
                
                if not employee_email:
                    raise Exception('ไม่พบ email address')
                
                # Send email with context
                template.with_context(
                    timestamp=fields.Datetime.now(),
                    payslip_id=payslip.id
                ).send_mail(payslip.id, force_send=True)
                
                # Update payslip status
                payslip.write({
                    'email_sent': True,
                    'email_sent_date': fields.Datetime.now(),
                    'email_sent_by': self.env.user.id
                })
                
                # Log success
                payslip.message_post(
                    body=f'Payslip email sent to {employee_email} via wizard',
                    subject='Payslip Email Sent (Batch)',
                    message_type='notification'
                )
                
                success_count += 1
                _logger.info(
                    f'[{i}/{total_payslips}] Email sent to {payslip.employee_id.name} '
                    f'({employee_email})'
                )

            except Exception as e:
                error_count += 1
                error_msg = f'{payslip.employee_id.name}: {str(e)}'
                error_details.append(error_msg)
                _logger.error(
                    f'[{i}/{total_payslips}] Failed to send email to '
                    f'{payslip.employee_id.name}: {str(e)}'
                )

        # Prepare result message
        message_lines = []
        message_lines.append(f'📊 สรุปการส่ง Email:')
        message_lines.append(f'✅ สำเร็จ: {success_count} รายการ')
        
        if error_count > 0:
            message_lines.append(f'❌ ไม่สำเร็จ: {error_count} รายการ')
            message_lines.append('')
            message_lines.append('🔍 รายละเอียด Error:')
            
            # Show first 5 errors
            for error in error_details[:5]:
                message_lines.append(f'• {error}')
            
            if len(error_details) > 5:
                message_lines.append(f'• ... และอีก {len(error_details) - 5} รายการ')

        message = '\n'.join(message_lines)
        
        # Log summary
        _logger.info(
            f'Payslip email batch completed: {success_count} success, '
            f'{error_count} errors out of {total_payslips} total'
        )

        # Return notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ผลการส่ง Email Payslip',
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
