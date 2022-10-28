import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PopbillPointWizard(models.TransientModel):
    _name = "popbill.point.wizard"

    point = fields.Char(string='포인트:')


    def check_etax_status_point_all(self):
        """
             포인트 조회 전 수집한 Result 데이터를 요청합니다.
        """

        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        return self.etax_point_status(items)

    def etax_point_status(self, items):
        for it in items:
            CompanySudo = self.env['res.company'].search([('etax_on', '=', True)])

            for i in CompanySudo:

                if i.etax_linkid:
                    _logger.info('------ etax_linkid %s', i.etax_linkid)
                else:
                    raise ValidationError(_(' Link ID 확인 '))

                if i.etax_secretkey:
                    _logger.info('------ etax_linkid %s', i.etax_secretkey)
                else:
                    raise ValidationError(_(' Secretkey 확인 '))

                if i.etax_userid:
                    _logger.info('------ etax_linkid %s', i.etax_userid)
                else:
                    raise ValidationError(_(' User ID 확인 '))

                _logger.info('------ company %s ---------', i.vat)
                # ICPSudo = self.env["ir.config_parameter"].sudo()
                etax_linkid = i.etax_linkid
                etax_secretkey = i.etax_secretkey
                etax_userid = i.etax_userid
                etax_company_no = i.vat
                etax_test = i.etax_test

                accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
                accountCheckService.IsTest = etax_test
                bank_code = it.bank_code
                account = it.name

                change_date = datetime.today().strftime('%Y%m%d')
                _logger.info('----------------- wirteDate %s -----------', change_date)
                _logger.info('----------------- bank_code %s -----------', bank_code)
                _logger.info('----------------- account %s -----------', account)
                if etax_company_no:
                    # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
                    CorpNum = etax_company_no
                    balance = accountCheckService.getBalance(CorpNum)

                    if balance:
                        self.point_type = balance
                        _logger.info("balance (포인트) : %s " % balance)
                    else:
                        _logger.info("포인트 확인에 오류가 발생했습니다.")
                else:
                    raise UserError(_('사업자 번호가 잘못 되었거나 없는 회사 정보가 있습니다.'))