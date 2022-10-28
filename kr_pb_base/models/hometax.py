import logging
from datetime import datetime, timedelta
from popbill import Contact, PopbillException, Taxinvoice, TaxinvoiceDetail, TaxinvoiceService

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class HometaxMove(models.Model):
    _name = "hometax.move"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _description = "Hometax move"

    name = fields.Char(string="Number", required=True, readonly=True, copy=False, default="New")
    etaxType = fields.Selection(
        [("etaxType1", "전자세금계산서"), ("etaxType2", "[수정전자세금계산서]")], string="문서형태", default="etaxType1"
    )
    issueType = fields.Selection(
        [("issueType1", "정발행"), ("issueType2", "역발행"), ("issueType3", "위수탁")],
        string="발행형태",
        default="issueType1",
    )
    purposeType = fields.Selection(
        [("purposeType1", "영수"), ("purposeType2", "청구"), ("purposeType3", "없음")],
        string="영수/청구",
        default="purposeType2",
    )
    invoiceeType = fields.Selection(
        [("invoiceeType1", "사업자"), ("invoiceeType2", "개인"), ("invoiceeType3", "외국인")],
        string="거래처유형",
        default="invoiceeType1",
    )

    @api.model
    def _get_supplier(self):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_companyid")
        if etax_linkid:
            etax_company_id = int(etax_linkid)
            return etax_company_id

    @api.model
    def _get_supplier_vat(self):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_company_no")
        if etax_linkid:
            etax_company_no = int(etax_linkid)
            return etax_company_no

    @api.model
    def _get_tax_id(self):
        etax = self.env["account.tax"].search([("e_tax_is", "=", True)], limit=1)
        if etax:
            return etax.id
        return None

    # taxType1 = fields.Selection(
    #     [("과세", "과세"), ("영세", "영세"), ("면세", "면세")],
    #     string="과세형태",
    #     default="invoiceeType1",
    # )

    #
    taxType1 = fields.Many2one("account.tax", string="과세형태", default=_get_tax_id)
    supplier_id = fields.Many2one("res.partner", string="공급자", default=_get_supplier, required=True)
    check_id = fields.Many2one("res.partner", string="공급자 확인용", default=_get_supplier, required=True)

    supplier_vat_no = fields.Char(string="등록번호", default=_get_supplier_vat, required=True)  # 사업자번호
    supplier_jong = fields.Char(string="종사업장")  # 종사업자
    supplier_sangho = fields.Char(string="상호", required=True)  # 상호
    supplier_ceo_name = fields.Char(string="성명", required=True)  # 대표자명
    supplier_address = fields.Char(string="사업장주소", default=" ")
    supplier_business_class = fields.Char(string="업태", default=" ")  # 업태
    supplier_business_type = fields.Char(string="종목", default=" ")  # 종목
    supplier_name = fields.Char(string="담당자", default=" ")  # 담당자
    supplier_tel = fields.Char(string="연락처", default=" ")  # 연락처
    supplier_email = fields.Char(string="이메일", default=" ")  # 이메일
    customer_id = fields.Many2one("res.partner", string="공급받는자")  # 공급받는자 ID
    customer_vat_no = fields.Char(string="등록번호", default=" ", required=True)  # 사업자번호
    customer_jong = fields.Char(string="종사업장", default=" ")  # 종사업자
    customer_sangho = fields.Char(string="상호", default=" ", required=True)  # 상호
    customer_ceo_name = fields.Char(string="성명", default=" ")  # 대표자명
    customer_address = fields.Char(string="사업장주소", default=" ")
    customer_business_class = fields.Char(string="업태", default=" ")  # 업태
    customer_business_type = fields.Char(string="종목", default=" ")  # 종목
    customer_name = fields.Char(string="담당자", default=" ")  # 담당자
    customer_tel = fields.Char(string="연락처", default=" ")  # 연락처
    customer_email1 = fields.Char(string="이메일1", default=" ")  # 이메일
    customer_email2 = fields.Char(string="이메일2", default=" ")  # 이메일
    writen_date = fields.Date(string="작성일자", default=fields.Date.today, readonly=True)  # 작성일자
    amount_untaxed = fields.Monetary(
        string="공급가액",
        compute="_compute_complete_amount",
        readonly=True,
        store=True,
        currency_field="currency_id",
    )
    amount_tax = fields.Monetary(
        string="세액",
        compute="_compute_complete_amount",
        readonly=True,
        store=True,
        currency_field="currency_id",
    )
    amount_total = fields.Monetary(
        string="합계금액",
        compute="_compute_complete_amount",
        readonly=True,
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", default=lambda self: self.env.company.currency_id
    )
    reference = fields.Char(string="비고", default=" ")

    cashtype1 = fields.Monetary(string="현금", currency_field="currency_id")
    cashtype2 = fields.Monetary(string="수표", currency_field="currency_id")
    cashtype3 = fields.Monetary(string="어음", currency_field="currency_id")
    cashtype4 = fields.Monetary(string="외상미수금", currency_field="currency_id")

    gubun = fields.Char(string="구분")
    issueDT = fields.Date(string="발행일자", default=fields.Date.today)  # 발행일자
    docType = fields.Char(string="문서형태")
    stateCode = fields.Integer(string="상태코드")

    p_itemKey = fields.Char(string="팝빌번호", readonly=True)
    p_taxType = fields.Char(string="과세형태", readonly=True)
    p_writeDate = fields.Char(string="작성일자", readonly=True)
    p_issueType = fields.Char(string="발행형태", readonly=True)
    p_supplyCostTotal = fields.Char(string="공급가액 합계", readonly=True)
    p_taxTotal = fields.Char(string="세액 합계", readonly=True)
    p_purposeType = fields.Char(string="영수/청구", readonly=True)
    p_issueDT = fields.Char(string="발행일시", readonly=True)
    p_stateCode = fields.Integer(string="상태코드", readonly=True)
    p_ntsconfirmNum = fields.Char(string="국세청승인번호", readonly=True)
    p_ntsresult = fields.Char(string="국세청 전송결과", readonly=True)
    p_ntssendDT = fields.Char(string="국세청 전송일시", readonly=True)
    p_ntsresultDT = fields.Char(string="국세청 결과 수신일시", readonly=True)
    p_ntssendErrCode = fields.Char(string="전송 사유코드", readonly=True)
    p_modifyCode = fields.Integer(string="수정 사유코드", readonly=True)
    P_invoicerCorpName = fields.Char(string="공급자 상호", readonly=True)
    p_invoicerCorpNum = fields.Char(string="공급자 사업자번호", readonly=True)
    p_invoicerMgtKey = fields.Char(string="공급자 문서번호", readonly=True)
    p_invoiceeCorpName = fields.Char(string="공급받는자 상호", readonly=True)
    p_invoiceeCorpNum = fields.Char(string="공급받는자 사업자번호", readonly=True)
    p_invoiceeMgtKey = fields.Char(string="공급받는자 문서번호", readonly=True)
    last_doc_no = fields.Char(string="원본문서번호")
    last_writen_date = fields.Date(string="원본작성일자")
    last_ntsconfirmNum = fields.Char(string="원본국세청승인번호")

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("sending", "Sending"),
            ("canceled", "Canceled"),
            ("sent", "Sent"),
            ("sent_error", "Sent Error"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )

    reg_date = fields.Date(string="발급일자", default=fields.Date.today)  # 발급일자
    send_date = fields.Date(string="전송일자")  # 전송일자
    hometax_accept_no = fields.Char(string="승인번호")  # 승인번호
    send_sms = fields.Boolean(string="Send SMS")
    force_issue = fields.Boolean()
    mail_title = fields.Char()
    line_ids = fields.One2many(
        "hometax.move.line",
        "move_id",
        string="품목",
        copy=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company", "Company", required=True, index=True, default=lambda self: self.env.company
    )

    date_today = datetime.today().strftime("%Y%m%d")
    date_start = datetime.today()
    date_finish = date_start + timedelta(days=-40)
    date_time = date_finish.strftime("%Y%m%d")

    @api.onchange("supplier_id")
    def _onchange_supplier_id(self):
        supplier_id = self.supplier_id
        self.supplier_vat_no = supplier_id.vat
        self.supplier_jong = supplier_id.jong_no
        self.supplier_ceo_name = supplier_id.ceo_name
        self.supplier_sangho = supplier_id.name
        self.supplier_address = supplier_id.address_all
        self.supplier_business_class = supplier_id.business_class
        self.supplier_business_type = supplier_id.business_type
        self.supplier_name = supplier_id.damdang_user
        self.supplier_tel = supplier_id.damdang_phone
        self.supplier_email = supplier_id.damdang_email

    @api.onchange("customer_id")
    def _onchange_customer_id(self):
        customer_id = self.customer_id
        self.customer_vat_no = customer_id.vat
        self.customer_jong = customer_id.jong_no
        self.customer_ceo_name = customer_id.ceo_name
        self.customer_sangho = customer_id.name
        self.customer_address = customer_id.address_all
        self.customer_business_class = customer_id.business_class
        self.customer_business_type = customer_id.business_type
        self.customer_name = customer_id.damdang_user
        self.customer_tel = customer_id.damdang_phone
        self.customer_email1 = customer_id.damdang_email1
        self.customer_email2 = customer_id.damdang_email2

    @api.onchange("check_id")
    def _onchange_check_id(self):
        check_id = self.check_id
        self.customer_vat_no = check_id.vat
        self.customer_jong = check_id.jong_no
        self.customer_ceo_name = check_id.ceo_name
        self.customer_sangho = check_id.name
        self.customer_address = check_id.address_all
        self.customer_business_class = check_id.business_class
        self.customer_business_type = check_id.business_type
        self.customer_name = check_id.damdang_user
        self.customer_tel = check_id.damdang_phone
        self.customer_email1 = check_id.damdang_email1
        self.customer_email2 = check_id.damdang_email2

    @api.onchange("taxType1")
    def _onchange_tax_type(self):
        # OVERRIDE
        # Recompute 'partner_shipping_id' based on 'partner_id'.
        taxtype = self.taxType_value
        for move in self.line_ids:
            move._compute_amount_only(taxtype)
        self._compute_complete_amount()

    @api.depends("line_ids")
    def _compute_complete_amount(self):
        amount_untaxed = 0
        amount_tax = 0
        amount_total = 0
        for move in self.line_ids:
            amount_untaxed += move.price_subtotal
            amount_tax = amount_tax + move.amount_tax
            amount_total = amount_total + move.price_subtotal + move.amount_tax
        for line in self:
            if line.p_ntsconfirmNum == False:
                self.update(
                    {
                        "amount_untaxed": amount_untaxed,
                        "amount_tax": amount_tax,
                        "amount_total": amount_total,
                        "cashtype4": amount_total,
                    }
                )

        _logger.info('------------------- amount_untaxed %s ------------------', amount_untaxed)
        _logger.info('------------------- amount_tax %s ------------------', amount_tax)
        _logger.info('------------------- amount_total %s ------------------', amount_total)

    @api.model
    def create(self, vals):
        if not vals.get("name") or vals["name"] == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("hometax.move") or _("New")

        return super(HometaxMove, self).create(vals)

    def button_cancel(self):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")

        etax_test = ICPSudo.get_param("etax_korea.etax_test")
        LinkID = etax_linkid
        SecretKey = etax_secretkey
        for item in self:
            taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
            taxinvoiceService.IsTest = etax_test
            try:

                item.update({"state": "canceled"})
                self.message_post(body=_("eTax Canceled"))
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                }
            except PopbillException as Err:
                raise exceptions.Warning(
                    _("세금계산서 취소 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )

    def update_etax_status_all(self):
        items = self.env["hometax.move"].search(
            ["|", ("state", "=", "issued"), ("state", "=", "sending")]
        )
        self.update_etax_status(items)

    def update_etax_status(self, items):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")
        etax_test = ICPSudo.get_param("etax_korea.etax_test")

        LinkID = etax_linkid
        SecretKey = etax_secretkey

        for item in items:
            taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
            taxinvoiceService.IsTest = etax_test
            try:
                CorpNum = item.supplier_vat_no
                MgtKey = item.name
                MgtKeyType = "SELL"
                response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                item.update(
                    {
                        "p_itemKey": response.itemKey,
                        "p_taxType": response.taxType,
                        "p_writeDate": response.writeDate,
                        "p_issueType": response.issueType,
                        "p_supplyCostTotal": response.supplyCostTotal,
                        "p_taxTotal": response.taxTotal,
                        "p_purposeType": response.purposeType,
                        "p_issueDT": response.issueDT,
                        "p_stateCode": response.stateCode,
                        "p_ntsconfirmNum": response.ntsconfirmNum,
                        "p_ntsresult": response.ntsresult,
                        "p_ntssendDT": response.ntssendDT,
                        "p_ntsresultDT": response.ntsresultDT,
                        "p_ntssendErrCode": response.ntssendErrCode,
                        "p_modifyCode": response.modifyCode,
                        "P_invoicerCorpName": response.invoicerCorpName,
                        "p_invoicerCorpNum": response.invoicerCorpNum,
                        "p_invoicerMgtKey": response.invoicerMgtKey,
                        "p_invoiceeCorpName": response.invoiceeCorpName,
                        "p_invoiceeCorpNum": response.invoiceeCorpNum,
                        "p_invoiceeMgtKey": response.invoiceeMgtKey,
                    }
                )
                stateCode = str(response.stateCode)
                fc = stateCode[0:1]
                sc = stateCode[2:3]
                if fc == "3" and sc == "4":
                    item.update({"state": "sent"})
                    item.message_post(body=_("eTax Sent"))
                elif sc == "5":
                    item.update({"state": "sent_error"})
                    item.message_post(body=_("eTax Sent Error"))

            except PopbillException as Err:
                raise exceptions.Warning(
                    _("세금계산서 발행 확인 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )


    def status_view(self):
        self.update_etax_status(self)

    def customer_view(self):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")
        etax_company_no = ICPSudo.get_param("etax_korea.etax_company_no")

        etax_test = ICPSudo.get_param("etax_korea.etax_test")
        LinkID = etax_linkid
        SecretKey = etax_secretkey

        for item in self:
            taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
            taxinvoiceService.IsTest = etax_test
            try:
                CorpNum = etax_company_no
                MgtKey = item.name
                MgtKeyType = "SELL"
                response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                item.update(
                    {
                        "p_itemKey": response.itemKey,
                        "p_taxType": response.taxType,
                        "p_ntsconfirmNum": response.ntsconfirmNum,
                    }
                )

            except PopbillException as Err:
                raise exceptions.Warning(
                    _("세금계산서 발행 확인 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )

    def pdfhometax(self):

        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")
        etax_company_no = ICPSudo.get_param("etax_korea.etax_company_no")
        etax_userid = ICPSudo.get_param("etax_korea.etax_userid")
        etax_test = ICPSudo.get_param("etax_korea.etax_test")
        # 1	CorpNum str 10 O 팝빌회원 사업자번호 (하이픈 '-' 제외 10 자리)
        # 2	MgtKeyType	str	-	O	세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1
        # └ SELL = 매출, BUY = 매입, TRUSTEE = 위수탁
        # 3	MgtKey	str	24	O	파트너가 할당한 문서번호
        # 4	UserID	str	50	-	팝빌회원 아이디
        CorpNum = etax_company_no
        MgtKeyType = "SELL"

        UserID = etax_userid
        try:
            for item in self:
                MgtKey = item.name

                taxinvoiceService = TaxinvoiceService(etax_linkid, etax_secretkey)
                taxinvoiceService.IsTest = etax_test
                # ljy taxinvoiceService.getPDFURL(CorpNum, MgtKeyType, MgtKey,UserID)  14 version ,
                url = taxinvoiceService.getPDFURL(CorpNum, MgtKeyType, MgtKey, UserID)
                if url:
                    return {
                        "name": "세금계산서 PDF 인쇄 ",
                        "res_model": "ir.actions.act_url",
                        "type": "ir.actions.act_url",
                        "target": "self",
                        "url": url,
                    }

        except PopbillException as Err:
            raise exceptions.Warning(
                _("세금계산서 PDF인쇄 오류 code %s message %s") % (Err.args[0], Err.args[1])
            )

    def sendhometax_minus(self):

        dup = self.copy()
        today = fields.Date.today()
        dup.update(
            {
                "etaxType": "etaxType2",
                "state": "draft",
                "last_doc_no": self.name,
                "writen_date": today,
                "last_writen_date": self.writen_date,
                "last_ntsconfirmNum": self.p_ntsconfirmNum,
            }
        )
        for line in dup.line_ids:
            line.update({"price_unit": -line.price_unit, "writen_date": today})

        accountmove = self.env["account.move"].search([("etax_id", "=", self.id)])
        for account in accountmove:
            if account:
                account.write({"etax_id": dup.id})

        return {
            "type": "ir.actions.act_window",
            "res_model": "hometax.move",
            "view_mode": "form",
            "views": [[False, "form"]],
            "res_id": dup.id,
        }

    def sendhometax(self):

        ICPSudo = self.env["ir.config_parameter"].sudo()
        etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")
        etax_company_no = ICPSudo.get_param("etax_korea.etax_company_no")
        etax_userid = ICPSudo.get_param("etax_korea.etax_userid")
        etax_issue_immediately = ICPSudo.get_param("etax_korea.etax_issue_immediately")
        etax_test = ICPSudo.get_param("etax_korea.etax_test")
        CorpNum = etax_company_no

        LinkID = etax_linkid
        SecretKey = etax_secretkey
        taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
        taxinvoiceService.IsTest = etax_test
        taxinvoiceService.IPRestrictOnOff = False

        # 팝빌회원 아이디
        UserID = etax_userid

        # [필수] 세금계산서 문서번호, 1~24자리, (영문, 숫자, '-', '_') 조합으로 사업자별로 중복되지 않도록 구성
        MgtKey = self.name

        # 지연발행 강제여부
        # 발행마감일이 지난 세금계산서를 발행하는 경우, 가산세가 부과될 수 있습니다.
        # 가산세가 부과되더라도 발행을 해야하는 경우에는 forceIssue의 값을 True로 선언
        forceIssue = False

        # 거래명세서 동시작성여부
        writeSpecification = False

        # 거래명세서 동시작성시, 명세서 관리번호, 1~24자리, (영문, 숫자, '-', '_') 조합으로 사업자별로 중복되지 않도록 구성
        dealInvoiceMgtKey = ""

        # 메모
        memo = "즉시발행 메모"

        # 발행안내 메일 제목, 미기재시 기본양식으로 전송
        emailSubject = ""
        writeDate = self.writen_date.strftime("%Y%m%d")

        supplyCostTotal = str(self.amount_untaxed)
        taxTotal = str(self.amount_tax)
        totalAmount = str(self.amount_total)
        cashtype1 = str(self.cashtype1)
        cashtype2 = str(self.cashtype2)
        cashtype3 = str(self.cashtype3)
        cashtype4 = str(self.cashtype4)
        serialNum = self.name
        remark1 = self.reference
        supplier_vat_no = self.supplier_vat_no

        issueTypecomment = {"issueType1": "정발행", "issueType2": "역발행", "issueType3": "위수탁"}
        issueType = issueTypecomment[self.issueType]
        purposeTypecomment = {"purposeType1": "영수", "purposeType2": "청구", "purposeType3": "없음"}
        purposeType = purposeTypecomment[self.purposeType]
        taxType = self.taxType1.e_tax_code

        invoiceeTypecomment = {
            "invoiceeType1": "사업자",
            "invoiceeType2": "개인",
            "invoiceeType3": "외국인",
        }
        invoiceeType = invoiceeTypecomment[self.invoiceeType]

        modifyCode = None
        orgNTSConfirmNum = None
        if self.etaxType == "etaxType2":
            modifyCode = 4
            orgNTSConfirmNum = self.last_ntsconfirmNum
            remark1 = self.last_writen_date.strftime("%Y%m%d")

        taxinvoice = Taxinvoice(
            # [필수] 작성일자, 날짜형식(yyyyMMdd) ex)20190116
            writeDate=writeDate,
            # [필수] 과금방향, [정과금(공급자), 역과금(공급받는자)]중 기재
            # 역과금의 경우 역발행세금계산서 발행시에만 사용가능
            chargeDirection="정과금",
            # [필수] 발행형태, [정발행, 역발행, 위수탁] 중 기재
            issueType=issueType,
            # [필수] [영수, 청구, 없음] 중 기재
            purposeType=purposeType,
            # [필수] 과세형태, [과세, 영세, 면세] 중 기재
            taxType=taxType,
            ######################################################################
            #                             공급자 정보
            ######################################################################
            # [필수] 공급자 사업자번호 , '-' 없이 10자리 기재.
            invoicerCorpNum=supplier_vat_no,
            # 공급자 종사업장 식별번호, 필요시 숫자 4자리 기재
            invoicerTaxRegID=None,
            # [필수] 공급자 상호
            invoicerCorpName=self.supplier_id.name,
            # [필수] 공급자 문서번호, 1~24자리, (영문, 숫자, '-', '_') 조합으로
            # 사업자별로 중복되지 않도록 구성
            invoicerMgtKey=MgtKey,
            # [필수] 공급자 대표자 성명
            invoicerCEOName=self.supplier_ceo_name,
            # 공급자 주소
            invoicerAddr=self.supplier_address,
            # 공급자 종목
            invoicerBizClass=self.supplier_business_type,
            # 공급자 업태
            invoicerBizType=self.supplier_business_class,
            # 공급자 담당자 성명
            invoicerContactName=self.supplier_name,
            # 공급자 담당자 메일주소
            invoicerEmail=self.supplier_email,
            # 공급자 담당자 연락처
            invoicerTEL=self.supplier_tel,
            # 공급자 담당자 휴대폰 번호
            invoicerHP=self.supplier_tel,
            # 발행시 알림문자 전송여부 (정발행에서만 사용가능)
            # - 공급받는자 주)담당자 휴대폰번호(invoiceeHP1)로 전송
            # - 전송시 포인트가 차감되며 전송실패하는 경우 포인트 환불처리
            invoicerSMSSendYN=False,
            ######################################################################
            #                            공급받는자 정보
            ######################################################################
            # [필수] 공급받는자 구분, [사업자, 개인, 외국인] 중 기재
            invoiceeType=invoiceeType,
            # [필수] 공급받는자 사업자번호, '-' 제외 10자리
            invoiceeCorpNum=self.customer_vat_no,
            # 공급자 종사업장 식별번호, 필요시 숫자 4자리 기재
            invoiceeTaxRegID=None,
            # [필수] 공급받는자 상호
            invoiceeCorpName=self.customer_id.name,
            # [역발행시 필수] 공급받는자 문서번호, 1~24자리 (숫자, 영문, '-', '_') 조합으로 사업자별로 중복되지 않도록 구성
            invoiceeMgtKey=None,
            # [필수] 공급받는자 대표자 성명
            invoiceeCEOName=self.customer_ceo_name,
            # 공급받는자 주소
            invoiceeAddr=self.customer_address,
            # 공급받는자 종목
            invoiceeBizClass=self.customer_business_type,
            # 공급받는자 업태
            invoiceeBizType=self.customer_business_class,
            # 공급받는자 담당자 성명
            invoiceeContactName1=self.customer_name,
            # 공급받는자 담당자 메일주소
            # 팝빌 개발환경에서 테스트하는 경우에도 안내 메일이 전송되므로,
            # 실제 거래처의 메일주소가 기재되지 않도록 주의
            invoiceeEmail1=self.customer_email1,
            # 공급받는자 연락처
            invoiceeTEL1=self.customer_tel,
            # 공급받는자 담당자 휴대폰번호
            invoiceeHP1=self.customer_tel,
            # 공급받는자 담당자 팩스번호
            invoiceeFAX1=self.customer_tel,
            ######################################################################
            #                          세금계산서 기재정보
            ######################################################################
            # [필수] 공급가액 합계
            supplyCostTotal=supplyCostTotal,
            # [필수] 세액 합계
            taxTotal=taxTotal,
            # [필수] 합계금액, 공급가액 합계 + 세액 합계
            totalAmount=totalAmount,
            # 기재상 '일련번호' 항목
            serialNum=serialNum,
            # 기재상 '현금' 항목
            cash=cashtype1,
            # 기재상 '수표' 항목
            chkBill=cashtype2,
            # 기재상 '어음' 항목
            note=cashtype3,
            # 기재상 '외상미수금' 항목
            credit=cashtype4,
            # 기재 상 '비고' 항목
            remark1=remark1,
            remark2="",
            remark3="",
            kwon=1,
            ho=2,
            businessLicenseYN=False,
            bankBookYN=False,
            modifyCode=modifyCode,
            orgNTSConfirmNum=orgNTSConfirmNum,
        )

        taxinvoice.detailList = []
        serno = 1
        for line in self.line_ids:
            serialNum = serno
            purchaseDT = line.writen_date.strftime("%Y%m%d")
            itemName = line.labelname
            qty = line.quantity
            unitCost = str(line.price_unit)
            supplyCost = str(line.price_subtotal)
            tax = str(line.amount_tax)
            remark = line.bigo
            spec = line.product_uom_id.name

            taxinvoice.detailList.append(
                TaxinvoiceDetail(
                    serialNum=serialNum,  # 일련번호, 1부터 순차기재
                    purchaseDT=purchaseDT,  # 거래일자, yyyyMMdd
                    itemName=itemName,  # 품목
                    spec=spec,  # 규격
                    qty=qty,  # 수량
                    unitCost=unitCost,  # 단가
                    supplyCost=supplyCost,  # 공급가액
                    tax=tax,  # 세액
                    remark=remark,  # 비고
                )
            )
            serno = serno + 1
        taxinvoice.addContactList = []
        if self.customer_email1:
            taxinvoice.addContactList.append(
                Contact(
                    serialNum=1,  # 일련번호, 1부터 순차기재
                    contactName=self.customer_name,  # 담당자명
                    email=self.customer_email1,  # 메일주소
                )
            )
        if self.customer_email2:
            taxinvoice.addContactList.append(
                Contact(
                    serialNum=2,  # 일련번호, 1부터 순차기재
                    contactName=self.customer_name,  # 담당자명
                    email=self.customer_email2,  # 메일주소
                )
            )

        try:
            response = taxinvoiceService.registIssue(
                CorpNum,
                taxinvoice,
                writeSpecification,
                forceIssue,
                dealInvoiceMgtKey,
                memo,
                emailSubject,
                UserID,
            )
            _logger.info('---------------------- try response -----------------')
            code = response.code

            ntsConfirmNum = response.ntsConfirmNum

            if code == 1:
                self.update({"state": "issued", "p_ntsconfirmNum": ntsConfirmNum})
                self.message_post(body=_("eTax Issued"))
                if etax_issue_immediately:
                    MgtKeyType = "SELL"
                    response = taxinvoiceService.sendToNTS(CorpNum, MgtKeyType, MgtKey, UserID)
                    if response.code == 1:
                        self.update({"state": "sending"})
                        self.message_post(body=_("eTax Sending"))

        except PopbillException as Err:

            raise exceptions.Warning(_("세금계산서발행오류 code %s message %s") % (Err.args[0], Err.args[1]))

        self.status_view()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values and self.state == "issued":
            return self.env.ref("etax_korea.order_issued")
        elif "state" in init_values and self.state == "sent":
            return self.env.ref("etax_korea.order_sent")
        elif "state" in init_values and self.state == "canceled":
            return self.env.ref("etax_korea.order_canceled")
        return super(HometaxMove, self)._track_subtype(init_values)

    def unlink(self):

        for hometaxbill in self:
            sale_ids = self.mapped("sale_ids").ids

            for vid in sale_ids:
                account_id = self.env["account.move"].browse(vid)
                hometaxmove = self.env["hometax.move"].search(
                    [("sale_ids", "in", [account_id.id]), ("id", "!=", hometaxbill.id)],
                    order="create_date desc",
                    limit=1,
                )
                if hometaxmove:
                    account_id.write({"etax_id": hometaxmove.id})
        return super(HometaxMove, self).unlink()

    def send_batch_files1(self, moves):
        if not moves:
            return


class HometaxMoveLine(models.Model):
    _name = "hometax.move.line"
    _description = "Hometax Account line"

    sequence = fields.Integer(default=10)
    move_id = fields.Many2one("hometax.move", string="Journal Entry", ondelete="cascade")
    name = fields.Char(string="Label", related="move_id.name", store=True, index=True)
    labelname = fields.Char(string="Label")
    writen_date = fields.Date(
        string="작성일자", related="move_id.writen_date", store=True, readonly=False
    )  # 작성일자
    parent_state = fields.Selection(related="move_id.state")
    product_id = fields.Many2one("product.product", string="품목")  # 품목
    product_uom_id = fields.Many2one("uom.uom", string="규격")
    bigo = fields.Char(string="비고", default=" ")
    quantity = fields.Float(string="수량", default=1.0, digits="Product Unit of Measure")
    price_unit = fields.Float(string="단가", digits="Product Price")
    price_subtotal = fields.Monetary(
        string="공급가액", compute="_compute_amount", store=True, currency_field="currency_id"
    )
    amount_tax = fields.Monetary(
        string="세액", compute="_compute_amount", store=True, currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        related="move_id.company_id", string="Company", store=True, readonly=True, index=True
    )

    @api.depends("quantity", "price_unit")
    def _compute_amount(self):

        for item in self:
            taxrate = 0.0
            if item.move_id.taxType1.amount > 0:
                taxrate = 1 / item.move_id.taxType1.amount
            item.price_subtotal = item.quantity * item.price_unit
            item.amount_tax = item.price_subtotal * taxrate

    def _compute_amount_only(self, taxType):

        taxrate = 0.0
        if taxType.amount > 0:
            taxrate = 1 / taxType.amount
        self.update({"amount_tax": self.price_subtotal * taxrate})
