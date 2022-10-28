import logging
from datetime import datetime, timedelta
from popbill import Contact, PopbillException, Taxinvoice, TaxinvoiceDetail, TaxinvoiceService

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class HometaxMoveInherit(models.Model):
    _inherit = "hometax.move"


    def button_cancel(self):
        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)], limit=1)

        if CompanySudo == None:
            return


        etax_linkid = CompanySudo.etax_userid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_test = CompanySudo.etax_test

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
        _logger.info('------- %s items ----------', items)
        self.update_etax_status(items)

    def update_etax_status(self, items):
        _logger.info('----------- CorpNum %s ------------', items)
        for item in items:

            CompanySudo = self.env['res.company'].search([('id', '=', item.supplier_id.id)])
            _logger.info('----------- item.supplier_id.id %s ------------', item.supplier_id.id)
            _logger.info('----------- CompanySudo %s ------------', CompanySudo)
            if CompanySudo == None:
                return

            etax_linkid = CompanySudo.etax_linkid
            etax_secretkey = CompanySudo.etax_secretkey

            LinkID = etax_linkid
            SecretKey = etax_secretkey
            Test = CompanySudo.etax_test


            taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
            taxinvoiceService.IsTest = Test
            _logger.info('----------- taxinvoiceService%s ------------',taxinvoiceService)
            _logger.info('----------- CorpNum %s ------------', etax_linkid)
            _logger.info('----------- MgtKey  %s ------------', etax_secretkey)
            _logger.info('----------- CorpNum %s ------------', item.supplier_vat_no)
            _logger.info('----------- MgtKey  %s ------------', item.name)



            try:
                CorpNum = item.supplier_vat_no
                MgtKey = item.name
                MgtKeyType = "SELL"
                response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                _logger.info('----------- response %s ------------', response)
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
                _logger.info('------------ %s ----------', stateCode)
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
        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)], limit=1)

        if CompanySudo == None:
            return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_company_no = CompanySudo.vat
        etax_test = CompanySudo.etax_test

        LinkID = etax_linkid
        SecretKey = etax_secretkey
        _logger.info('-------------- linkid %s ------------', LinkID)
        _logger.info('-------------- SecretKey %s ------------', SecretKey)

        for item in self:
            taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
            taxinvoiceService.IsTest = etax_test
            _logger.info('-------------- taxinvoiceService %s ------------', taxinvoiceService)
            try:
                CorpNum = etax_company_no
                MgtKey = item.name
                MgtKeyType = "SELL"
                response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                _logger.info('-------------- MgtKey %s ------------', MgtKey)
                _logger.info('-------------- response %s ------------', response.stateCode)
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
        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)], limit=1)

        if CompanySudo == None:
            return


        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_company_no = CompanySudo.vat
        etax_userid = CompanySudo.etax_userid
        etax_test = CompanySudo.etax_test
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

        # ICPSudo = self.env["ir.config_parameter"].sudo()
        # etax_linkid = ICPSudo.get_param("etax_korea.etax_linkid")
        # etax_secretkey = ICPSudo.get_param("etax_korea.etax_secretkey")
        # etax_company_no = ICPSudo.get_param("etax_korea.etax_company_no")
        # etax_userid = ICPSudo.get_param("etax_korea.etax_userid")
        # etax_issue_immediately = ICPSudo.get_param("etax_korea.etax_issue_immediately")
        # etax_test = ICPSudo.get_param("etax_korea.etax_test")
        # _logger.info('---------------- ICPSudo %s --------------------', ICPSudo)

        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)], limit=1)

        if CompanySudo == None:
            return

        etax_linkid = CompanySudo.etax_linkid
        etax_secretkey = CompanySudo.etax_secretkey
        etax_company_no = CompanySudo.vat
        etax_userid = CompanySudo.etax_userid
        etax_issue_immediately = CompanySudo.etax_issue_immediately
        etax_test = CompanySudo.etax_test

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
        taxType = self.taxType1

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
            # [필수] 공급받는자 사업자번호, '-' 제 외 10자리
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


    def create_order_wizard(self):
        return {
            'name': _("Ordner erstellen"),
            'type': 'ir.actions.act_window',
            'res_model': 'hometax.orders.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }



    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values and self.state == "issued":
            return self.env.ref("etax_korea.order_issued")
        elif "state" in init_values and self.state == "sent":
            return self.env.ref("etax_korea.order_sent")
        elif "state" in init_values and self.state == "canceled":
            return self.env.ref("etax_korea.order_canceled")
        return super(HometaxMoveInherit, self)._track_subtype(init_values)

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
        return super(HometaxMoveInherit, self).unlink()

    def send_batch_files1(self, moves):
        if not moves:
            return
