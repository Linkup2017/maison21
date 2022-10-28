from odoo import _, api, exceptions, fields, models
from datetime import datetime, timedelta
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class SearchBankList(models.TransientModel):
    _name = 'search.bank.account'

    date_select = fields.Selection([
        ("7", "7 Days"),
        ("15", "15 Days"),
        ("30", "30 Days")
    ], string="Select Search Date", default="7")
    sdate = fields.Date(string='Start date')
    edate = fields.Date(string='End date', default=datetime.today())


    #
    # def search_etax_status_all(self):
    #     items = self.env["account.bank.statement"].search([("name", '=', self.bank_id.name)])
    #
    #     return self.requestJob(items)
    #
    # def requestJob(self, items):
    #
    #     if self.date_select == "7":
    #         if self.sdate <= self.edate + timedelta(days=-2):
    #             cal_date = self.sdate
    #             _logger.info('------------------------- %s cal_date 1 --------------------', cal_date)
    #
    #     if self.date_select == "15":
    #         cal_date = self.sdate + timedelta(days=-15)
    #
    #     if self.date_select == "30":
    #         cal_date = self.sdate + timedelta(days=-30)
    #
    #     for i in items:
    #         _logger.info('------------------------- %s i --------------------', i.date)
    #         if i.date <= cal_date:
    #             filter_date = i.date
    #             _logger.info('------------------------- %s cal_date 2 --------------------', cal_date)
    #             _logger.info('------------------------- %s filter_date --------------------', filter_date)
    #         action = {
    #             'name': _('Search Account Bank '),
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'tree',
    #             'res_model': 'account.bank.statement',
    #             'view_id': self.env.ref('account.view_bank_statement_tree').id,
    #             'domain': [('name', '=', self.bank_id.name), ('date', '<=', cal_date)],
    #         }
    #         return action

    def search_bank_check_etax_status_all(self):
        """
             계좌 거래내역 수집을 요청합니다.
             - 검색기간은 현재일 기준 90일 이내로만 요청할 수 있습니다.
             - 수집 요청후 반환받은 작업아이디(JobID)의 유효시간은 1시간 입니다.
        """

        items = self.env["account.journal"].search([('bank_code', '!=', None)])

        self.requestJob(items)

    def requestJob(self, items):

        for it in items:
            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

        if CompanySudo == None:
            return
        _logger.info('------------------ CompanySudo %s ---------------', CompanySudo)
        _logger.info('------------------ CompanySudo %s ---------------', CompanySudo.name)
        if CompanySudo.etax_on == True:
            # ICPSudo = self.env["ir.config_parameter"].sudo()
            etax_linkid = CompanySudo.etax_linkid
            etax_secretkey = CompanySudo.etax_secretkey
            etax_userid = CompanySudo.etax_userid
            etax_company_no = CompanySudo.vat
            etax_test = CompanySudo.etax_test

            _logger.info('------------------ etax_linkid %s ---------------', etax_linkid)
            _logger.info('------------------ etax_secretkey %s ---------------', etax_secretkey)
            _logger.info('------------------ etax_userid %s ---------------', etax_userid)
            _logger.info('------------------ etax_company_no %s ---------------', etax_company_no)
            _logger.info('------------------ etax_test %s ---------------', etax_test)
            easyFinBankService = EasyFinBankService(etax_linkid, etax_secretkey)
            easyFinBankService.IsTest = etax_test
        else:
            raise UserError(
                _("Check that you have entered the popbill information correctly for your company in Settings -> Users and Companies -> Company."))

        for i in items:

            _logger.info('------------------ bank code items %s ---------------', i.bank_code)
            bank_code = i.bank_code
            account = i.name
            start_change_date = self.sdate.strftime('%Y%m%d')
            end_change_date = self.edate.strftime('%Y%m%d')
            _logger.info('----------------- wirteDate %s -----------', start_change_date)
            _logger.info('----------------- bank_code %s -----------', bank_code)
            _logger.info('----------------- account %s -----------', account)

            # 팝빌회원 사업자번호
            CorpNum = etax_company_no

            # 팝빌회원 아이디
            UserID = etax_userid

            # 기관코드
            BankCode = bank_code

            # 계좌번호
            AccountNumber = account

            # 시작일자, 날짜형식(yyyyMMdd)
            SDate = start_change_date

            # 종료일자, 날짜형식(yyyyMMdd)
            EDate = end_change_date

            result = easyFinBankService.requestJob(CorpNum, BankCode, AccountNumber, SDate, EDate,
                                                   UserID)
            i.result_data = result
            _logger.info('-------------- result %s --------------', result)

            history_id = self.env['transaction.history.inquiry'].search([])
            currency_id = self.env['res.currency'].search([('name', '=', 'KRW')], limit=1)

            start_balance = []
            start_tid = []
            tid_list = []

            for lo in history_id:
                if lo:
                    tid_list.append(lo.tid)
                    _logger.info('-------------------- tid_list %s -----------------', tid_list)

            currency = currency_id.id

            create_name = i.name
            account = i.accountnumber
            if result:
                # 수집요청(requestJob)시 발급받은 작업아이디
                JobID = result

                # 거래유형 배열, I - 입금 / O - 출금
                TradeType = ["I", "O"]

                # 조회 검색어 - 입금/출금액, 메모, 적요 like 검색 가능
                SearchString = ""

                # 페이지번호
                Page = 1

                # 페이지당 목록개수, 최대값 1000
                PerPage = 100

                # 정렬방향 D-내림차순, A-오름차순
                Order = "D"

                response = easyFinBankService.search(CorpNum, JobID, TradeType, SearchString, Page, PerPage,
                                                     Order, UserID)

                # _logger.info('-------------------- result %s -----------------', JobID)
                # _logger.info('-------------------- response %s -----------------', response.code)
                # _logger.info('-------------------- response list %s -----------------', response.list)

            i.status = 'create'
            for li in response.list:
                start_tid.append(li.tid)

            for info in response.list:

                start_balance.append(info.balance)

                if info.tid not in tid_list:
                    _logger.info('-------- info.tid %s ------------', info.tid)
                    _logger.info('-------- info.accIn %s ------------', info.accIn)
                    _logger.info('-------- info.accOut %s ------------', info.accOut)

                    create_list = self.env['transaction.history.inquiry'].create({
                        'name': create_name,
                        'date': datetime.strptime(info.trdate, '%Y%m%d'),
                        'payment_ref': info.remark1,
                        'narration': info.memo,
                        'transaction_type': info.remark3,
                        'foreign_currency_id': currency,
                        'deposit': int(info.accIn),
                        'withdraw': -int(info.accOut),
                        'amount': info.balance,
                        'tid': info.tid,
                        'trdt': datetime.strptime(info.trdt, '%Y%m%d%H%M%S'),
                    })
                    i.warning = False
                    _logger.info('--------- create --------')
                    _logger.info('--------- %s -----------', create_name)
                else:
                    i.warning = False
                    _logger.info('--------- no create ------')
