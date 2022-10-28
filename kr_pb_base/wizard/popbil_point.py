import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PopbillPointWizard(models.TransientModel):
    _name = 'popbill.point.wizard'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    _logger.info('------------ company_id %s ----------', company_id)

    @api.model
    def get_point(self):
        """
        포인트 조회 전 수집한 Result 데이터를 요청합니다.
        """
        company_id = self.env.company.id
        _logger.info('------------ company_id %s ----------', self.company_id)
        CompanySudo = self.env['res.company'].search([('id', '=', company_id)])

        if CompanySudo:
            _logger.info('------------ %s ----------', CompanySudo)
            return CompanySudo.point

        return None

    currency_id = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id)
    point = fields.Monetary(string='포인트 : ', default=get_point, readonly=True)


    def point_charger_wizard(self):
            return {
                'name': _('Popbill Point Charger'),
                'res_model': 'popbill.point.charger.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
            }

    def etax_point_charge(self):

        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)])
        _logger.info('------------ %s -----------', CompanySudo)
        for i in CompanySudo:
            etax_linkid = i.etax_linkid
            etax_secretkey = i.etax_secretkey
            etax_userid = i.etax_userid
            etax_company_no = i.vat
            etax_test = i.etax_test
            accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
            accountCheckService.IsTest = etax_test



            if etax_company_no:
                if etax_userid:
                    # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
                    CorpNum = etax_company_no


                    # 팝빌 회원 아이디
                    TOGO = "linkup2017"

                    chargeurl = accountCheckService.getPartnerURL(CorpNum, TOGO)
                    _logger.info('------------ %s --------------', chargeurl)


                    if chargeurl:
                        return {
                            "type": "ir.actions.act_url",
                            "url": "%s" % chargeurl,
                            "target": "new"
                        }
                        _logger.info('------------ %s --------------', chargeurl)

                    else:
                        raise UserError('결제 창에 오류가 발생했습니다')
                    _logger.info("chargeurl : %s " % chargeurl)
                else:
                    raise UserError(_('팝빌 ID가 잘못 되었거나 없는 회사 정보가 있습니다.'))
            else:
                raise UserError(_('사업자 번호가 잘못 되었거나 없는 회사 정보가 있습니다.'))




    def etax_point_charge_history(self):

        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)])

        for i in CompanySudo:

            etax_linkid = i.etax_linkid
            etax_secretkey = i.etax_secretkey
            etax_userid = i.etax_userid
            etax_company_no = i.vat
            etax_test = i.etax_test

            accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
            accountCheckService.IsTest = etax_test

            if etax_company_no:
                if etax_userid:
                    # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
                    CorpNum = etax_company_no

                    # 팝빌 회원 아이디
                    userId = etax_userid

                    payment = accountCheckService.getPaymentURL(CorpNum, userId)

                    if payment:
                        return {
                            "type": "ir.actions.act_url",
                            "url": "%s" % payment,
                            "target": "new"
                        }
                        _logger.info('------------ %s --------------', payment)
                    else:
                        raise UserError('결제 창에 오류가 발생했습니다')
                    _logger.info("payment : %s " % payment)
                else:
                    raise UserError(_('팝빌 ID가 잘못 되었거나 없는 회사 정보가 있습니다.'))
            else:
                raise UserError(_('사업자 번호가 잘못 되었거나 없는 회사 정보가 있습니다.'))
