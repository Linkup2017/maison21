
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # is_kakaotalk = fields.Boolean('Use Kakao talk instead of SMS?')
    sms_linkid = fields.Char("LinkID")
    sms_secretkey = fields.Char("Secretkey")
    sms_company_no = fields.Char("Company Number")
    sms_userid = fields.Char("popBill user id")
    sms_test = fields.Boolean("Is Test", default=True)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        sms_secretkey = self.env['ir.config_parameter'].sudo().get_param('iap.sms_secretkey', self.sms_secretkey or "")
        sms_linkid = self.env['ir.config_parameter'].sudo().get_param('iap.sms_linkid', self.sms_linkid or "")
        sms_company_no = self.env['ir.config_parameter'].sudo().get_param('iap.sms_company_no', self.sms_company_no or "")
        sms_userid = self.env['ir.config_parameter'].sudo().get_param('iap.sms_userid')
        sms_test = self.env['ir.config_parameter'].sudo().get_param('iap.sms_test')

        res.update(
            sms_secretkey=sms_secretkey,
            sms_linkid=sms_linkid,
            sms_company_no=sms_company_no,
            sms_userid=sms_userid,
            sms_test=sms_test,
        )
        return res



    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('iap.sms_secretkey', self.sms_secretkey or "")
        self.env['ir.config_parameter'].sudo().set_param('iap.sms_linkid', self.sms_linkid or "")
        self.env['ir.config_parameter'].sudo().set_param('iap.sms_company_no', self.sms_company_no)
        self.env['ir.config_parameter'].sudo().set_param('iap.sms_userid', self.sms_userid)
        self.env['ir.config_parameter'].sudo().set_param('iap.sms_test', self.sms_test)



