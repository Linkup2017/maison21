import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError
import collections
from odoo.tools import float_is_zero


try:
    sys.setdefaultencoding('UTF8')
except Exception as E:
    pass

import logging
_logger = logging.getLogger(__name__)


class stataementlineadd(models.Model):
    _inherit = "account.bank.statement.line"

    deposit = fields.Monetary(currency_field='currency_id')
    withdraw = fields.Monetary(currency_field='currency_id')
    tid = fields.Char(stirng='tid')



class InheritAccountJournal(models.Model):
    _inherit = "account.journal"

    status = fields.Selection([('draft', 'Draft'),
                              ('create', 'Create')], string="State"
                              , default="draft")
    bank_code = fields.Char(string='Bank Code', readonly=True, copy=True)
    bank_type = fields.Selection(
        [("개인", "개인"), ("법인", "법인")], string="Bank Account Type", default="개인"
    )
    accountnumber = fields.Char(string='Account Number')
    result_data = fields.Char(string="Data")
    check_create = fields.Char(string="Check")
    birth_date = fields.Char(string="Birth Date")
    bank_password = fields.Char(string="Bank PW")
    search_bank_id = fields.Char(string="Search Bank ID")
    search_bank_password = fields.Char(string="Search Bank PW")
    bank_id = fields.Many2one('res.bank', related='bank_account_id.bank_id', readonly=False)
    bank_list_id = fields.Many2one('res.bank.list', readonly=False)
    value_bank_id = fields.Char(string="Bank ID")
    date_today = fields.Date(string="Transaction from", default=fields.Date.today)
    warning = fields.Boolean(default=False)
    currency_id = fields.Many2one(
        "res.currency", string="Currency", default=lambda self: self.env.company.currency_id
    )

    def status_changer(self):
        if self.status == 'create':
            self.status = 'draft'
    def open_account_bank_statement_view(self):
        account_bank_id = self.env['transaction.history.inquiry'].search([('name', '=', self.name)], limit=1)
        # if account_bank_id:
        _logger.info('--------- id %s  ----------', account_bank_id)
        action = {
            "type": "ir.actions.act_window",
            "name": _("Transaction History"),
            "res_model": "transaction.history.inquiry",
            "view_mode": "tree,form",
            'domain': [('name', '=', account_bank_id.name)],
        }
        _logger.info('--------- action %s  ----------', action)
        return action



    """
        계좌 등록
    """

    def set_bank_data(self):

        """
        계좌 등록 하는 부분 입니다.
        """

        CompanySudo = self.env['res.company'].search([('id','=',self.company_id.id)], limit=1)

        if CompanySudo == None:
            return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        if etax_linkid :

            easyFinBankService = EasyFinBankService(etax_linkid, etax_secretkey)
            easyFinBankService.IsTest = etax_test

            try:
                CorpNum = etax_company_no
                UserID = etax_userid
                infoObj = BankAccountInfo(
                    # [필수] 기관코드
                    # 산업은행-0002 / 기업은행-0003 / 국민은행-0004 /수협은행-0007 / 농협은행-0011 / 우리은행-0020
                    # SC은행-0023 / 대구은행-0031 / 부산은행-0032 / 광주은행-0034 / 제주은행-0035 / 전북은행-0037
                    # 경남은행-0039 / 새마을금고-0045 / 신협은행-0048 / 우체국-0071 / KEB하나은행-0081 / 신한은행-0088 /씨티은행-0027
                    BankCode=self.bank_code,

                    # [필수] 계좌번호 하이픈('-') 제외
                    AccountNumber=self.name,

                    # [필수] 계좌비밀번호
                    AccountPWD=self.bank_password,

                    # [필수] 계좌유형, "법인" 또는 "개인" 입력

                    AccountType=self.bank_type,

                    # [필수] 예금주 식별정보 (‘-‘ 제외)
                    # 계좌유형이 “법인”인 경우 : 사업자번호(10자리)
                    # 계좌유형이 “개인”인 경우 : 예금주 생년월일 (6자리-YYMMDD)
                    IdentityNumber=self.birth_date,

                    # 계좌 별칭
                    AccountName="",

                    # 인터넷뱅킹 아이디 (국민은행 필수)
                    BankID=self.value_bank_id,

                    # 조회전용 계정 아이디 (대구은행, 신협, 신한은행 필수)
                    FastID=self.search_bank_id,

                    # 조회전용 계정 비밀번호 (대구은행, 신협, 신한은행 필수)
                    FastPWD=self.bank_password,

                    # 결제기간(개월), 1~12 입력가능, 미기재시 기본값(1) 처리
                    # - 파트너 과금방식의 경우 입력값에 관계없이 1개월 처리
                    UsePeriod="1",

                    # 메모
                    Memo="",
                )
                _logger.info("데이터  : %s" % (infoObj))
                _logger.info('----------------- bank_code %s ---------  -----------', self.bank_code)
                _logger.info('----------------- BankID %s ---------  -----------', self.value_bank_id)
                _logger.info('----------------- account %s --------------------', self.name)
                _logger.info('----------------- bank_password %s --------------------', self.bank_password)
                _logger.info('----------------- bank_type %s --------------------', self.bank_type)
                _logger.info('----------------- etax_test %s --------------------', etax_test)
                _logger.info('----------------- status %s --------------------', self.status)

                self.check_create = "1"
                self.status = "create"

                result = easyFinBankService.registBankAccount(CorpNum, infoObj, UserID)
                _logger.info("처리결과 : [%d] %s" % (result.code, result.message))
            except PopbillException as PE:
                _logger.info('---------------- %s -------------', PE.code)
                if PE.code == -18000019:
                    self.status = "create"
                    self.warning = True
                else:
                    raise UserError(_("오류가 발생했습니다 : [%d] %s" % (PE.code, PE.message))
                        )

                # if PE.code:
                #

    def get_bank_data(self):

        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)], limit=1)

        if CompanySudo == None:
            return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        easyFinBankService = EasyFinBankService(etax_linkid, etax_secretkey)
        easyFinBankService.IsTest = etax_test

        bank_ids = self.env["account.journal"].search([("type", "=", 'bank')])

        for line in bank_ids.bank_list_id:
            bank_code = line.bank_code
            account = line.accountnumber
            try:
                CorpNum = etax_company_no
                UserID = etax_userid
                BankCode = str(bank_code)
                AccountNumber = account
                _logger.info("--------------------- CorpNum %s --------------------", CorpNum)
                _logger.info("--------------------- UserID %s --------------------", UserID)
                _logger.info("--------------------- BankCode %s --------------------", BankCode)
                _logger.info("--------------------- AccountNumber %s --------------------", AccountNumber)
                result = easyFinBankService.getBankAccountInfo(CorpNum, BankCode, AccountNumber, UserID)
                self.status = 'create'
                _logger.info('---------------------- result %s --------------------------', result)

                return result
            except PopbillException as PE:
                raise exceptions.Warning(
                    _("Exception Occur : [%d] %s" % (PE.code, PE.message))

                )



    """
        Popbill 과 통신하여 데이터 수집
    """

    def bank_check_etax_status_all(self):
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
            change_date = datetime.today().strftime('%Y%m%d')
            _logger.info('----------------- wirteDate %s -----------', change_date)
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
            SDate = change_date

            # 종료일자, 날짜형식(yyyyMMdd)
            EDate = change_date

            result = easyFinBankService.requestJob(CorpNum, BankCode, AccountNumber, SDate, EDate,
                                                   UserID)
            i.result_data = result
            _logger.info('-------------- result %s --------------', result)



    """
        분개장 생성
    """

    def account_bank_statement(self):
            """
                 계좌 거래내역 생성 전 수집한 Result 데이터를 요청합니다.
            """
            items = self.env["account.journal"].search([("bank_code", '!=', None)])
            _logger.info('------------------ items items %s ---------------', items)

            return self.create_account_bank_statement(items)

    def create_account_bank_statement(self, items):

        for it in items:

            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

            if CompanySudo == None:

                return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test


        easyFinBankService = EasyFinBankService(etax_linkid, etax_secretkey)
        easyFinBankService.IsTest = etax_test

        # bank_ids = self.env["account.journal"].search([("type", "=", 'bank')])
        company_id = self.env.company.partner_id.id
        currency_id = self.env['res.currency'].search([('name', '=', 'KRW')], limit=1)
        account_id = self.env["account.bank.statement"].search([])

        start_balance = []
        acc_list = []
        vals_line = []
        update_line = []
        line_ids = []
        tid_list = []
        line_tid_list = []
        for i in items:

            create_id = i.id
            currecny = currency_id
            create_name = i.name
            account = i.accountnumber

            # 팝빌회원 사업자번호
            CorpNum = etax_company_no

            # 팝빌회원 아이디
            UserID = etax_userid

            # 수집요청(requestJob)시 발급받은 작업아이디
            JobID = i.result_data

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

            _logger.info('-------------------- result %s -----------------', JobID)
            _logger.info('-------------------- response %s -----------------', response.list)

            i.status = 'create'
            currency = currency_id.id


            for info in response.list:

                start_balance.append(info.balance)

                fc = start_balance[0]
                sc = start_balance[1:2]
                sc_str = ''.join(sc)

                if int(info.accIn) > 0:
                    acc_list.append(int(info.accIn))

                if int(info.accOut) > 0:
                    acc_list.append(-int(info.accOut))
                value = int(info.accIn) + -int(info.accOut)
                tid_list.append(info.tid)
                vals_line.append((0, 0, {
                        'date': datetime.strptime(info.trdate, '%Y%m%d'),
                        'payment_ref': info.remark1,
                        'partner_id': company_id,
                        'narration': info.memo,
                        'transaction_type': info.remark3,
                        'amount': value,
                        'account_number': account,
                        'tid': info.tid,
                        'journal_id': i.id,
                        'statement_id': i.id,
                                  }))

                _logger.info('--------- vals_list %s -------', vals_line)
                _logger.info('--------- fc %s -------', fc)
            start_str = start_balance[-1]
            acc_str = acc_list[-1]
            if acc_str > 0:
                acc = int(start_str) + int(acc_str)
            else:
                acc = int(start_str) + -int(acc_str)

            _logger.info('--------- acc %s -------', acc)
            # vals_line.append((0, 0, {
            #     'date': datetime.strptime(info.trdate, '%Y%m%d'),
            #     'payment_ref': "잔금",
            #     'amount': acc,
            #     'foreign_currency_id': currecny,
            #     'journal_id': i.id,
            #     'statement_id': i.id,
            # }))
            _logger.info('%s', account_id)
            if account_id:
                _logger.info('----- account_id %s ------', account_id)
                _logger.info('----- self %s ------', self.name)
                for ac in account_id:
                    _logger.info('----- account_id %s ------', ac.name)

                    if i.name == ac.journal_id.name:
                        _logger.info('---------- i name %s ----------', i.name)
                        _logger.info('---------- ac.journal_id.name %s ----------', ac.journal_id.name)
                        for line in ac.line_ids:
                            line_ids.append(int(line.amount))
                            line_tid_list.append(line.tid)

                        # if collections.Counter(acc_list) == collections.Counter(line_ids):
                        for j in response.list:

                            if j.tid not in line_tid_list:
                                _logger.info('--- 생성해야함 ---')
                                _logger.info('--- j.tid %s ---', j.tid)
                                _logger.info('--- line_tid_list %s ---', line_tid_list)

                                if int(j.accIn) > 0:
                                    acc_list.append(int(j.accIn))

                                if int(j.accOut) > 0:
                                    acc_list.append(-int(j.accOut))
                                value = int(j.accIn) + -int(j.accOut)
                                update_line.append((0, 0, {
                                    'date': datetime.strptime(j.trdate, '%Y%m%d'),
                                    'payment_ref': j.remark1,
                                    'partner_id': company_id,
                                    'narration': j.memo,
                                    'foreign_currency_id': currecny,
                                    'transaction_type': j.remark3,
                                    'amount': value,
                                    'account_number': account,
                                    'tid': j.tid,
                                    'journal_id': i.id,
                                    'statement_id': i.id,
                                }))

                        ac.update({
                            'balance_end_real': fc,
                            'line_ids': update_line,
                        })
                        _logger.info('---------- update_line %s  ----------', update_line)
                        update_line.clear()
                        vals_line.clear()
                        _logger.info('---------- update ----------')

            else:
                create_tree = self.env['account.bank.statement'].create({
                    'journal_id': i.id,
                    'name': create_name,
                    'balance_start': sc_str,
                    'balance_end_real': fc,
                    'line_ids': vals_line,
                })

                _logger.info('---------- craete ---------')
                vals_line.clear()
                start_balance.clear()

            self.warning = False



    """ 
        계좌 거래 내역 생성
    """

    def bank_check_etax_status_create_all(self):


        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        return self.create_bank_status(items)

    def create_bank_status(self, items):

        """
            requestJob에서 생성한 Result 데이터를 요청하여 계좌 거래 내역을 생성 합니다
        """


        for it in items:

            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

            if CompanySudo == None:

                return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        easyFinBankService = EasyFinBankService(etax_linkid, etax_secretkey)
        easyFinBankService.IsTest = etax_test

        history_id = self.env['transaction.history.inquiry'].search([])
        currency_id = self.env['res.currency'].search([('name', '=', 'KRW')], limit=1)

        start_balance = []
        start_tid = []
        tid_list = []

        for lo in history_id:
            if lo:
                tid_list.append(lo.tid)
                _logger.info('-------------------- tid_list %s -----------------', tid_list)

        for i in items:

            currency = currency_id.id

            create_name = i.name
            account = i.accountnumber

            # 팝빌회원 사업자번호
            CorpNum = etax_company_no

            # 팝빌회원 아이디
            UserID = etax_userid

            # 수집요청(requestJob)시 발급받은 작업아이디
            JobID = i.result_data

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

            _logger.info('-------------------- result %s -----------------', JobID)
            _logger.info('-------------------- response %s -----------------', response.code)
            _logger.info('-------------------- response list %s -----------------', response.list)


            i.status = 'create'
            for li in response.list:
                start_tid.append(li.tid)

            for info in response.list:
                start_balance.append(info.balance)


                if info.tid not in tid_list:
                    _logger.info('-------- info.tid %s ------------', info.tid)
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
                    self.warning = False
                    _logger.info('--------- create --------')
                else:
                    self.warning = False
                    _logger.info('--------- no create ------')



    """
        예금주 조회
    """

    def check_etax_account_holder(self):



        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        return self.check_etax_account_holder_status(items)

    def check_etax_account_holder_status(self, items):

        """
            예금주 조회 전 수집한 Result 데이터를 요청합니다.
        """


        for it in items:

            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

            if CompanySudo == None:
                return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
        accountCheckService.IsTest = etax_test

        for i in items:
            _logger.info('------------------ bank code items %s ---------------', i.bank_code)
            bank_code = i.bank_code
            account = i.name
            change_date = datetime.today().strftime('%Y%m%d')
            _logger.info('----------------- wirteDate %s -----------', change_date)
            _logger.info('----------------- bank_code %s -----------', bank_code)
            _logger.info('----------------- account %s -----------', account)

            # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            CorpNum = etax_company_no

            # 조회할 계좌 기관코드
            # - https://docs.popbill.com/accountcheck/?lang=python#BankCodeList
            bankCode = bank_code

            # 조회할 계좌번호 (하이픈 '-' 제외 8자리 이상 14자리 이하)
            accountNumber = account

            # 팝빌 회원 아이디
            userId = etax_userid

            accountInfo = accountCheckService.checkAccountInfo(CorpNum, bankCode, accountNumber, userId)

            _logger.info("=" * 15 + " 예금주조회 " + "=" * 15)

            _logger.info("bankCode (기관코드) : %s " % accountInfo.bankCode)
            _logger.info("accountNumber (계좌번호) : %s " % accountInfo.accountNumber)
            _logger.info("accountName (예금주 성명) : %s " % accountInfo.accountName)
            _logger.info("checkDate (확인일시) : %s " % accountInfo.checkDate)
            _logger.info("resultCode (응답코드) : %s " % accountInfo.resultCode)
            _logger.info("resultMessage (응답메시지) : %s " % accountInfo.resultMessage)



    """
        포인트 확인
    """

    def check_etax_status_point_all(self):


            items = self.env["account.journal"].search([("bank_code", '!=', None)])
            _logger.info('------------------ items items %s ---------------', items)

            return self.etax_point_status(items)

    def etax_point_status(self, items):

        """
             포인트 조회 전 수집한 Result 데이터를 요청합니다.
        """

        for it in items:

            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

            if CompanySudo == None:
                return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
        accountCheckService.IsTest = etax_test

        for i in items:
            _logger.info('------------------ bank code items %s ---------------', i.bank_code)
            bank_code = i.bank_code
            account = i.name
            change_date = datetime.today().strftime('%Y%m%d')
            _logger.info('----------------- wirteDate %s -----------', change_date)
            _logger.info('----------------- bank_code %s -----------', bank_code)
            _logger.info('----------------- account %s -----------', account)

            # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            CorpNum = etax_company_no

            balance = accountCheckService.getBalance(CorpNum)

            _logger.info("balance (포인트) : %s " % balance)


class InheritSetupWizard(models.TransientModel):
    _inherit = "account.setup.bank.manual.config"

    bank_list_id = fields.Many2one('res.bank.list', string='Financial Institution List')
    bank_availability = fields.Selection(
        [("사용", "사용 가능"), ("불가", "사용 불가")], string="Bank Availability", default="불가")
    bank_type = fields.Selection(
        [("개인", "개인"), ("법인", "법인")], string="Bank Account Type", default="개인")
    accountnumber = fields.Char(string='Account Number')
    result_data = fields.Char(string="Data")
    check_create = fields.Char(string="Check")
    birth_date = fields.Char(string="Birth Date", help="“개인”인 경우 : 예금주 생년월일 (6자리-YYMMDD), “법인”인 경우 : 사업자번호(10자리)")
    search_bank_id = fields.Char(string="Search Bank ID", help="“조회전용 계정 아이디 (대구은행, 신협, 신한은행 필수)”")
    search_bank_password = fields.Char(string="Search Bank PW", help="“조회전용 계정 비밀번호 (대구은행, 신협, 신한은행 필수)”")
    bank_code = fields.Char(string='Bank Code', copy=True)
    bank_password = fields.Char(string='Bank PW')
    value_bank_id = fields.Char(string='Bank ID', help="“국민”인 경우 필수 입력")
    date_today = fields.Date(string="Transaction from")


    @api.onchange('bank_list_id')
    def _onchange_bank_code(self):

        for i in self.bank_list_id:
            if i.name == '농협은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '기업은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '국민은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '우리은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '신한은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '하나은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == 'SC제일은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '산업은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '씨티은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '대구은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '부산은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '경남은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '광주은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '전북은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '제주은행':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '우체국':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '새마을금고':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '신협':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"
            if i.name == '수협':
                self.bank_code = i.bank_code
                self.bank_availability = "사용"



    def set_linked_journal_id(self):
        """ Called when saving the wizard.
        """
        for record in self:
            selected_journal = record.linked_journal_id

            if not selected_journal:
                new_journal_code = self.env['account.journal'].get_next_bank_cash_default_code('bank', self.env.company)
                company = self.env.company
                bank_code = self.bank_code
                bank_type = self.bank_type
                result_data = self.result_data
                birth_date = self.birth_date
                bank_password = self.bank_password
                search_bank_id = self.search_bank_id
                search_bank_password = self.search_bank_password
                bank_id = self.value_bank_id
                bank_list_id = self.bank_list_id.id
                date_today = self.date_today
                selected_journal = self.env['account.journal'].create({
                    'name': record.new_journal_name,
                    'code': new_journal_code,
                    'type': 'bank',
                    'company_id': company.id,
                    'bank_account_id': record.res_partner_bank_id.id,
                    'bank_code': bank_code,
                    'bank_type': bank_type,
                    'result_data': result_data,
                    'birth_date': birth_date,
                    'search_bank_id': search_bank_id,
                    'search_bank_password': search_bank_password,
                    'bank_password': bank_password,
                    'value_bank_id': bank_id,
                    'bank_list_id': bank_list_id,
                    'date_today': date_today,
                })
                _logger.info('----------- create ----------')
            else:
                selected_journal.bank_account_id = record.res_partner_bank_id.id
                selected_journal.name = record.new_journal_name

        return selected_journal



    @api.model
    def create(self, vals):
        """ This wizard is only used to setup an account for the current active
        company, so we always inject the corresponding partner when creating
        """
        vals['partner_id'] = self.env.company.partner_id.id
        vals['new_journal_name'] = vals['acc_number']

        # If no bank has been selected, but we have a bic, we are using it to find or create the bank
        if not vals['bank_list_id'] and vals['bank_bic']:
            vals['bank_list_id'] = self.env['res.bank'].search([('bic', '=', vals['bank_bic'])], limit=1).id \
                              or self.env['res.bank'].create({'name': vals['name'], 'bic': vals['bank_bic'],
                                                              'bank_code': vals['bank_code']}).id

        return super(InheritSetupWizard, self).create(vals)


class InheritAccountBankStatemenet(models.Model):
    _inherit = 'account.bank.statement'


    # @api.depends('line_ids', 'balance_start', 'line_ids.amount', 'balance_end_real')
    # def _end_balance(self):
    #     for statement in self:
    #         statement.total_entry_encoding = sum([line.amount for line in statement.line_ids])
    #         statement.balance_end = statement.balance_start + statement.total_entry_encoding
    #         statement.balance_end_real = statement.balance_end
    #         statement.difference = statement.balance_end_real - statement.balance_end

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    connect_bank = fields.Selection([("draft", "연동계좌 확인중"), ("connect", "연동계좌 확인완료"),
                                       ("failed", "연동계좌 확인실패")], string='연결 상태', default="draft"
                                      , readonly=True)


    def check_etax_account_holder(self):
        """
            예금주 조회 전 수집한 Result 데이터를 요청합니다.
        """

        items = self.env["account.journal"].search([("bank_code", '!=', None)])
        _logger.info('------------------ items items %s ---------------', items)

        if items:
            return self.check_etax_account_holder_status(items)
        else:
            raise ValidationError(_(' 은행 계좌가 등록되어있는지  확인해주세요 '))


    def check_etax_account_holder_status(self, items):

        for it in items:

            CompanySudo = self.env['res.company'].search([('id', '=', it.company_id.id)])

            if CompanySudo == None:
                return
            # ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_userid = CompanySudo.etax_userid
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        if etax_linkid:
            _logger.info('------- true -----')
        else:
            raise ValidationError(_(' Link ID 값 확인'))

        if etax_secretkey:
            _logger.info('------- true -----')
        else:
            raise ValidationError(_(' Secretkey 값 확인'))

        if etax_userid:
            _logger.info('------- true -----')
        else:
            raise ValidationError(_(' User ID 값 확인'))

        accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
        accountCheckService.IsTest = etax_test

        for i in items:
            _logger.info('------------------ bank code items %s ---------------', i.bank_code)
            bank_code = i.bank_code
            account = i.name
            change_date = datetime.today().strftime('%Y%m%d')
            _logger.info('----------------- wirteDate %s -----------', change_date)
            _logger.info('----------------- bank_code %s -----------', bank_code)
            _logger.info('----------------- account %s -----------', account)

            # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            CorpNum = etax_company_no

            # 조회할 계좌 기관코드
            # - https://docs.popbill.com/accountcheck/?lang=python#BankCodeList
            bankCode = bank_code

            # 조회할 계좌번호 (하이픈 '-' 제외 8자리 이상 14자리 이하)
            accountNumber = account

            # 팝빌 회원 아이디
            userId = etax_userid

            accountInfo = accountCheckService.checkAccountInfo(CorpNum, bankCode, accountNumber, userId)

            _logger.info("=" * 15 + " 예금주조회 " + "=" * 15)

            _logger.info("bankCode (기관코드) : %s " % accountInfo.bankCode)
            _logger.info("accountNumber (계좌번호) : %s " % accountInfo.accountNumber)
            _logger.info("accountName (예금주 성명) : %s " % accountInfo.accountName)
            _logger.info("checkDate (확인일시) : %s " % accountInfo.checkDate)
            _logger.info("resultCode (응답코드) : %s " % accountInfo.resultCode)
            _logger.info("resultMessage (응답메시지) : %s " % accountInfo.resultMessage)

            if accountInfo.resultMessage == '정상처리':
                self.connect_bank = 'connect'
            else:
                self.connect_bank = 'failed'


