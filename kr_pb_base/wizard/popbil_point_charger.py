import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PopbillPointWizard(models.TransientModel):
    _name = 'popbill.point.charger.wizard'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    _logger.info('------------ company_id %s ----------', company_id)
    url_fields = fields.Char(string='url')


    """
        포인트 충전
    """

    def check_etax_status_point_charge(self):


        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        return self.etax_point_charge(items)

    def etax_point_charge(self, items):

        """
            포인트 충전 전 수집한 Result 데이터를 요청합니다.
        """

        CompanySudo = self.env['res.company'].search([('etax_on', '=', True)])

        for i in CompanySudo:
            for it in items:



                    # ICPSudo = self.env["ir.config_parameter"].sudo()
                etax_linkid = i.etax_linkid
                etax_secretkey = i.etax_secretkey
                etax_userid = i.etax_userid
                etax_company_no = i.vat
                etax_test = i.etax_test
                accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
                accountCheckService.IsTest = etax_test

                _logger.info('------------------ bank code items %s ---------------', it.bank_code)
                bank_code = it.bank_code
                account = it.name
                change_date = datetime.today().strftime('%Y%m%d')


                if etax_company_no:
                    if etax_userid:
                        # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
                        CorpNum = etax_company_no

                        # 조회할 계좌 기관코드
                        # - https://docs.popbill.com/accountcheck/?lang=python#BankCodeList
                        bankCode = bank_code

                        # 조회할 계좌번호 (하이픈 '-' 제외 8자리 이상 14자리 이하)
                        accountNumber = account

                        # 팝빌 회원 아이디
                        TOGO = "CHRG"


                        chargeurl = accountCheckService.getPartnerURL(CorpNum, TOGO)

                        _logger.info('------------ %s --------------', chargeurl)

                        if chargeurl:
                            self.url_fields = chargeurl
                        else:
                            raise UserError('결제 창에 오류가 발생했습니다')
                        _logger.info("chargeurl : %s " % chargeurl)
                    else:
                        raise UserError(_('팝빌 ID가 잘못 되었거나 없는 회사 정보가 있습니다.'))
                else:
                    raise UserError(_('사업자 번호가 잘못 되었거나 없는 회사 정보가 있습니다.'))



    """
          포인트 결제내역 확인
    """

    def check_etax_status_point_charge_history(self):


        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        return self.etax_point_charge_history(items)

    def etax_point_charge_history(self, items):

        """
          포인트 결제내역 확인 전 수집한 Result 데이터를 요청합니다.
        """

        CompanySudo = self.env['res.company'].search([('etax_on', '=', True)])

        for i in CompanySudo:
            for it in items:
                # ICPSudo = self.env["ir.config_parameter"].sudo()
                etax_linkid = i.etax_linkid
                etax_secretkey = i.etax_secretkey
                etax_userid = i.etax_userid
                etax_company_no = i.vat
                etax_test = i.etax_test

                accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
                accountCheckService.IsTest = etax_test

                _logger.info('------------------ bank code items %s     ---------------', it.bank_code)
                bank_code = it.bank_code
                account = it.name
                change_date = datetime.today().strftime('%Y%m%d')

                if etax_company_no:
                    if etax_userid:
                        # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
                        CorpNum = etax_company_no

                        # 조회할 계좌 기관코드
                        # - https://docs.popbill.com/accountcheck/?lang=python#BankCodeList
                        bankCode = bank_code

                        # 조회할 계좌번호 (하이픈 '-' 제외 8자리 이상 14자리 이하)
                        accountNumber = account

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
