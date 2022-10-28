import logging
from datetime import datetime, timedelta
from popbill import Contact, PopbillException, Taxinvoice, TaxinvoiceDetail, TaxinvoiceService

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class HometaxMove(models.Model):
    _inherit = "hometax.move"

    def check_etax_status_all(self):
        items = self.env["hometax.move"].search([("state", "=", "sent")])
        _logger.info('--------------- items %s --------------', items)
        if items:
            return self.check_etax_status(items)
        return None

    def check_etax_status(self, items):

        nfnum = []
        sdate = self.date_today
        ddate = self.date_time
        _logger.info('-------------- sdate %s -----------------', sdate)
        _logger.info('-------------- ddate %s -----------------', ddate)

        for obj in items:
            nfnum.append(obj.name)
            _logger.info('---------------- nfnum %s ----------------', nfnum)
            _logger.info('---------------- start %s ----------------', type(obj.date_today))
            _logger.info('---------------- finish %s ----------------', type(obj.date_time))

            CompanySudo = self.env['res.company'].search([('id', '=', obj.supplier_id.id)])
            _logger.info('--------------- companysudo %s --------------', CompanySudo)
            if CompanySudo == None:
                return
            etax_linkid = CompanySudo.etax_linkid
            SecretKey = CompanySudo.etax_secretkey
            user_id = CompanySudo.etax_userid
            etax_test = CompanySudo.etax_test
            company_no = CompanySudo.vat

        LinkID = etax_linkid
        SecretKey = SecretKey
        user_id = user_id
        etax_test = etax_test
        company_no = company_no


        taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
        taxinvoiceService.IsTest = etax_test
        list_name = []
        response_list = []
        CorpNum = company_no
        _logger.info('-------------- CorpNum %s -----------------', CorpNum)
        _logger.info('-------------- taxinvoiceService.IsTest %s -----------------', taxinvoiceService.IsTest)
        MgtKeyType = "SELL"
        DType = "R"
        SDate = ddate
        EDate = sdate
        State = ""
        Type = ""
        TaxType = ""
        LateOnly = ""
        TaxRegIDYN = ""
        TaxRegIDType = ""
        TaxRegID = ""
        Page = ""
        PerPage = ""
        Order = ""
        UserID = user_id
        QString = ""
        InterOPYN = ""
        IssueType = ""
        RegType = ""
        CloseDownState = ""
        MgtKey = ""

        response = taxinvoiceService.search(CorpNum, MgtKeyType, DType, SDate, EDate, State, Type, TaxType,
                                            LateOnly, TaxRegIDYN, TaxRegIDType, TaxRegID, Page, PerPage, Order,
                                            UserID, QString, InterOPYN, IssueType, RegType, CloseDownState,
                                            MgtKey)
        _logger.info('------------- response  %s ---------', response)

        # 매출 문서함 거래 내역 조회 하여 문서번호 조회 내역 리스트에 적재
        for i in response.list:
            response_list.append(i.invoicerMgtKey)

        # 리스트에 적재한 문서번호를 상세조회 하여 데이터 추출
        for j in response_list:
            try:
                if j not in nfnum:
                    _logger.info('------------- j %s ---------', j)

                    MgtKey = j
                    detail_response = taxinvoiceService.getDetailInfo(CorpNum, MgtKeyType, MgtKey)
                    info_response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                    product_uom_data = 1
                    tax_type = 1

                    # 규격 받아올때 사용하는 for문
                    for spec in detail_response.detailList:
                        t_sepc = str(spec.spec)
                        _logger.info('------------- t_spec %s -------------', t_sepc)

                        if t_sepc == "단위":
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "다스":
                            product_uom_data = 2
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "일":
                            product_uom_data = 3
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "시간":
                            product_uom_data = 4
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m":
                            product_uom_data = 5
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mm":
                            product_uom_data = 6
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "km":
                            product_uom_data = 7
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "cm":
                            product_uom_data = 8
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m²":
                            product_uom_data = 9
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "L":
                            product_uom_data = 10
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m³":
                            product_uom_data = 11
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "kg":
                            product_uom_data = 12
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "g":
                            product_uom_data = 13
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "t":
                            product_uom_data = 14
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "lb":
                            product_uom_data = 15
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "oz":
                            product_uom_data = 16
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "분류":
                            product_uom_data = 17
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft":
                            product_uom_data = 18
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mi":
                            product_uom_data = 19
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft²":
                            product_uom_data = 20
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "fl oz (US)":
                            product_uom_data = 21
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "qt(US)":
                            product_uom_data = 22
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 23
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 24
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "in³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "Units":
                            product_uom_data = 1
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)



                    ntsconfirmNum = str(info_response.ntsconfirmNum)
                    ntsresult = str(info_response.ntsresult)
                    ntssendDT = str(info_response.ntssendDT)
                    ntsresultDT = str(info_response.ntsresultDT)
                    ntssendErrCode = str(info_response.ntssendErrCode)
                    stateCode = int(info_response.stateCode)
                    itemKey = int(info_response.itemKey)

                    supplyCostTotal = str(detail_response.supplyCostTotal)
                    taxTotal = str(detail_response.taxTotal)
                    totalAmount = str(detail_response.totalAmount)
                    issueType = str(detail_response.issueType)
                    purposeType = str(detail_response.purposeType)
                    remark1 = str(detail_response.remark1)
                    taxType = str(detail_response.taxType)
                    ntsconfirmNum = str(detail_response.ntsconfirmNum)

                    if issueType == "정발행":
                        issueType = "issueType1"
                    if issueType == "역발행":
                        issueType = "issueType2"
                    if issueType == "위수탁":
                        issueType = "issueType3"

                    if purposeType == "영수":
                        purposeType = "purposeType1"
                    if purposeType == "청구":
                        purposeType = "purposeType2"
                    if purposeType == "없음":
                        purposeType = "purposeType3"

                    invoicerCorpName = str(detail_response.invoicerCorpName)
                    invoicerCEOName = str(detail_response.invoicerCEOName)
                    invoicerCorpNum = str(detail_response.invoicerCorpNum)
                    invoicerAddr = str(detail_response.invoicerAddr)
                    invoicerBizType = str(detail_response.invoicerBizType)
                    invoicerContactName = str(detail_response.invoicerContactName)
                    invoicerEmail = str(detail_response.invoicerEmail)
                    invoicerTEL = str(detail_response.invoicerTEL)
                    invoicerBizClass = str(detail_response.invoicerBizClass)



                    invoiceeCorpName = str(detail_response.invoiceeCorpName)
                    invoiceeCorpNum = str(detail_response.invoiceeCorpNum)
                    invoiceeMgtKey = str(detail_response.invoiceeMgtKey)
                    invoiceeType = str(detail_response.invoiceeType)
                    invoiceeCEOName = str(detail_response.invoiceeCEOName)
                    invoiceeAddr = str(detail_response.invoiceeAddr)
                    invoiceeBizType = str(detail_response.invoiceeBizType)
                    invoiceeBizClass = str(detail_response.invoiceeBizClass)
                    invoiceeContactName1 = str(detail_response.invoiceeContactName1)
                    invoiceeTEL1 = str(detail_response.invoiceeTEL1)
                    invoiceeEmail1 = str(detail_response.invoiceeEmail1)
                    invoiceeEmail2 = str(detail_response.invoiceeEmail2)

                    format = '%Y%m%d'
                    input = str(detail_response.writeDate)
                    writeDate = datetime.strptime(input, format)
                    invoicerMgtKey = str(detail_response.invoicerMgtKey)
                    customer_id = items.customer_id.id
                    customer_name = items.customer_id.name

                    list_name.append(str(detail_response.ntsconfirmNum))

                    obj.create({
                        'name': detail_response.invoicerMgtKey,
                        'supplier_id': customer_id,
                        'check_id': customer_id,
                        'supplier_vat_no': invoicerCorpNum,
                        'supplier_sangho': customer_name,
                        'supplier_ceo_name': invoicerCEOName,
                        'supplier_address': invoicerAddr,
                        'supplier_business_class': invoicerBizType,
                        'supplier_business_type': invoicerBizClass,
                        'supplier_name': invoicerContactName,
                        'supplier_email': invoicerEmail,
                        'supplier_tel': invoicerTEL,
                        'customer_id': customer_id,
                        'customer_vat_no': invoiceeCorpNum,
                        'customer_sangho': invoiceeCorpName,
                        'customer_jong': '',
                        'customer_ceo_name': invoiceeCEOName,
                        'customer_address': invoiceeAddr,
                        'customer_business_class': invoiceeBizType,
                        'customer_business_type': invoiceeBizClass,
                        'customer_name': invoiceeContactName1,
                        'customer_tel': invoiceeTEL1,
                        'customer_email1': invoiceeEmail1,
                        'customer_email2': invoiceeEmail2,
                        'writen_date': writeDate,
                        'amount_untaxed': supplyCostTotal,
                        'amount_tax': taxTotal,
                        "amount_total": totalAmount,
                        "issueType": issueType,
                        "purposeType": purposeType,
                        "reference": remark1,
                        "p_itemKey": itemKey,
                        "p_stateCode": stateCode,
                        "p_ntsconfirmNum": ntsconfirmNum,
                        "p_ntsresult": ntsresult,
                        "p_ntssendDT": ntssendDT,
                        "p_ntssendErrCode": ntssendErrCode,
                        "p_invoiceeCorpName": invoiceeCorpName,
                        "p_invoiceeCorpNum": invoiceeCorpNum,
                        'line_ids': [(0, 0, {
                            'writen_date': writeDate,
                            'labelname': str(i.itemName),
                            'product_uom_id': product_uom_data,
                            'quantity': str(i.qty),
                            'price_unit': int(i.unitCost),
                            'price_subtotal': str(i.supplyCost),
                            'amount_tax': str(i.tax),
                            'bigo': str(i.remark),
                        }) for i in detail_response.detailList],
                        'state': 'sent',
                    })
                    _logger.info('------------ data 1  %s ----------', str(spec.qty))
                    _logger.info('------------ data 2  %s ----------', int(spec.unitCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))

                    _logger.info('------------ 생성 함 --------------')

                    amount_untaxed = 0
                    amount_tax = 0
                    amount_total = 0
                    for move in self.line_ids:
                        amount_untaxed += move.price_subtotal
                        amount_tax = amount_tax + move.amount_tax
                        amount_total = amount_total + move.price_subtotal + move.amount_tax

                    self.update(
                        {
                            "amount_untaxed": amount_untaxed,
                            "amount_tax": amount_tax,
                            "amount_total": amount_total,
                            "cashtype4": amount_total,
                        }
                    )
                else:

                    _logger.info('------------ 생성 되어 있음 --------------')

            except PopbillException as Err:
                raise exceptions.Warning(
                    _("세금계산서 최산화 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )


    def check_etax_status_all_buy(self):
        items = self.env["hometax.move"].search(
            [("state", "=", "sent")]
        )
        _logger.info('--------------- items %s --------------', items)
        if items:
            return self.check_etax_status_buy(items)
        return None

    def check_etax_status_buy(self, items):

        nfnum = []
        sdate = self.date_today
        ddate = self.date_time


        for obj in items:
            nfnum.append(obj.name)
            _logger.info('--------------------- nfum %s ---------------', nfnum)


            CompanySudo = self.env['res.company'].search([('id', '=', obj.supplier_id.id)])

            if CompanySudo == None:
                return
            etax_linkid = CompanySudo.etax_linkid
            SecretKey = CompanySudo.etax_secretkey
            user_id = CompanySudo.etax_userid
            etax_test = CompanySudo.etax_test
            company_no = CompanySudo.vat

        LinkID = etax_linkid
        SecretKey = SecretKey
        user_id = user_id
        etax_test = etax_test
        company_no = company_no


        taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
        taxinvoiceService.IsTest = etax_test
        list_name = []
        response_list = []
        CorpNum = company_no
        _logger.info('-------------- CorpNum %s -----------------',CorpNum)
        _logger.info('-------------- taxinvoiceService.IsTest %s -----------------', taxinvoiceService.IsTest)
        MgtKeyType = "BUY"
        DType = "R"
        SDate = ddate
        EDate = sdate
        State = ""
        Type = ""
        TaxType = ""
        LateOnly = ""
        TaxRegIDYN = ""
        TaxRegIDType = ""
        TaxRegID = ""
        Page = ""
        PerPage = ""
        Order = ""
        UserID = user_id
        QString = ""
        InterOPYN = ""
        IssueType = ""
        RegType = ""
        CloseDownState = ""
        MgtKey = ""

        response = taxinvoiceService.search(CorpNum, MgtKeyType, DType, SDate, EDate, State, Type, TaxType,
                                            LateOnly, TaxRegIDYN, TaxRegIDType, TaxRegID, Page, PerPage, Order,
                                            UserID, QString, InterOPYN, IssueType, RegType, CloseDownState,
                                            MgtKey)

        _logger.info('------------- response %s ---------', response.MgtKeyType)
        # 매출 문서함 거래 내역 조회 하여 문서번호 조회 내역 리스트에 적재
        for i in response.list:
            response_list.append(i.invoicerMgtKey)
            _logger.info('------------- response %s ---------', i.issueType)

        # 리스트에 적재한 문서번호를 상세조회 하여 데이터 추출
        for j in response_list:
            try:
                if j not in nfnum:
                    _logger.info('------------- j %s ---------', j)

                    MgtKey = j
                    detail_response = taxinvoiceService.getDetailInfo(CorpNum, MgtKeyType, MgtKey)
                    info_response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                    product_uom_data = 1
                    tax_type = 1

                    # 규격 받아올때 사용하는 for문
                    for spec in detail_response.detailList:
                        t_sepc = str(spec.spec)
                        _logger.info('------------- t_spec %s -------------', t_sepc)

                        if t_sepc == "단위":
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "다스":
                            product_uom_data = 2
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "일":
                            product_uom_data = 3
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "시간":
                            product_uom_data = 4
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m":
                            product_uom_data = 5
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mm":
                            product_uom_data = 6
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "km":
                            product_uom_data = 7
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "cm":
                            product_uom_data = 8
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m²":
                            product_uom_data = 9
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "L":
                            product_uom_data = 10
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m³":
                            product_uom_data = 11
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "kg":
                            product_uom_data = 12
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "g":
                            product_uom_data = 13
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "t":
                            product_uom_data = 14
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "lb":
                            product_uom_data = 15
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "oz":
                            product_uom_data = 16
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "분류":
                            product_uom_data = 17
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft":
                            product_uom_data = 18
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mi":
                            product_uom_data = 19
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft²":
                            product_uom_data = 20
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "fl oz (US)":
                            product_uom_data = 21
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "qt(US)":
                            product_uom_data = 22
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 23
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 24
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "in³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "Units":
                            product_uom_data = 1
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)



                    ntsconfirmNum = str(info_response.ntsconfirmNum)
                    ntsresult = str(info_response.ntsresult)
                    ntssendDT = str(info_response.ntssendDT)
                    ntsresultDT = str(info_response.ntsresultDT)
                    ntssendErrCode = str(info_response.ntssendErrCode)
                    stateCode = int(info_response.stateCode)
                    itemKey = int(info_response.itemKey)

                    supplyCostTotal = str(detail_response.supplyCostTotal)
                    taxTotal = str(detail_response.taxTotal)
                    totalAmount = str(detail_response.totalAmount)
                    issueType = str(detail_response.issueType)
                    purposeType = str(detail_response.purposeType)
                    remark1 = str(detail_response.remark1)
                    taxType = str(detail_response.taxType)
                    ntsconfirmNum = str(detail_response.ntsconfirmNum)

                    if issueType == "정발행":
                        issueType = "issueType1"
                    if issueType == "역발행":
                        issueType = "issueType2"
                    if issueType == "위수탁":
                        issueType = "issueType3"

                    if purposeType == "영수":
                        purposeType = "purposeType1"
                    if purposeType == "청구":
                        purposeType = "purposeType2"
                    if purposeType == "없음":
                        purposeType = "purposeType3"

                    invoicerCorpName = str(detail_response.invoicerCorpName)
                    invoicerCEOName = str(detail_response.invoicerCEOName)
                    invoicerCorpNum = str(detail_response.invoicerCorpNum)
                    invoicerAddr = str(detail_response.invoicerAddr)
                    invoicerBizType = str(detail_response.invoicerBizType)
                    invoicerContactName = str(detail_response.invoicerContactName)
                    invoicerEmail = str(detail_response.invoicerEmail)
                    invoicerTEL = str(detail_response.invoicerTEL)
                    invoicerBizClass = str(detail_response.invoicerBizClass)



                    invoiceeCorpName = str(detail_response.invoiceeCorpName)
                    invoiceeCorpNum = str(detail_response.invoiceeCorpNum)
                    invoiceeMgtKey = str(detail_response.invoiceeMgtKey)
                    invoiceeType = str(detail_response.invoiceeType)
                    invoiceeCEOName = str(detail_response.invoiceeCEOName)
                    invoiceeAddr = str(detail_response.invoiceeAddr)
                    invoiceeBizType = str(detail_response.invoiceeBizType)
                    invoiceeBizClass = str(detail_response.invoiceeBizClass)
                    invoiceeContactName1 = str(detail_response.invoiceeContactName1)
                    invoiceeTEL1 = str(detail_response.invoiceeTEL1)
                    invoiceeEmail1 = str(detail_response.invoiceeEmail1)
                    invoiceeEmail2 = str(detail_response.invoiceeEmail2)

                    format = '%Y%m%d'
                    input = str(detail_response.writeDate)
                    writeDate = datetime.strptime(input, format)
                    invoicerMgtKey = str(detail_response.invoicerMgtKey)
                    customer_id = items.customer_id.id
                    customer_name = items.customer_id.name

                    list_name.append(str(detail_response.ntsconfirmNum))

                    obj.create({
                        'name': detail_response.invoicerMgtKey,
                        'supplier_id': customer_id,
                        'check_id': customer_id,
                        'supplier_vat_no': invoicerCorpNum,
                        'supplier_sangho': customer_name,
                        'supplier_ceo_name': invoicerCEOName,
                        'supplier_address': invoicerAddr,
                        'supplier_business_class': invoicerBizType,
                        'supplier_business_type': invoicerBizClass,
                        'supplier_name': invoicerContactName,
                        'supplier_email': invoicerEmail,
                        'supplier_tel': invoicerTEL,
                        'customer_id': customer_id,
                        'customer_vat_no': invoiceeCorpNum,
                        'customer_sangho': invoiceeCorpName,
                        'customer_jong': '',
                        'customer_ceo_name': invoiceeCEOName,
                        'customer_address': invoiceeAddr,
                        'customer_business_class': invoiceeBizType,
                        'customer_business_type': invoiceeBizClass,
                        'customer_name': invoiceeContactName1,
                        'customer_tel': invoiceeTEL1,
                        'customer_email1': invoiceeEmail1,
                        'customer_email2': invoiceeEmail2,
                        'writen_date': writeDate,
                        'amount_untaxed': supplyCostTotal,
                        'amount_tax': taxTotal,
                        "amount_total": totalAmount,
                        "issueType": issueType,
                        "purposeType": purposeType,
                        "reference": remark1,
                        "p_itemKey": itemKey,
                        "p_stateCode": stateCode,
                        "p_ntsconfirmNum": ntsconfirmNum,
                        "p_ntsresult": ntsresult,
                        "p_ntssendDT": ntssendDT,
                        "p_ntssendErrCode": ntssendErrCode,
                        "p_invoiceeCorpName": invoiceeCorpName,
                        "p_invoiceeCorpNum": invoiceeCorpNum,
                        'line_ids': [(0, 0, {
                            'writen_date': writeDate,
                            'labelname': str(i.itemName),
                            'product_uom_id': product_uom_data,
                            'quantity': str(i.qty),
                            'price_unit': int(i.unitCost),
                            'price_subtotal': str(i.supplyCost),
                            'amount_tax': str(i.tax),
                            'bigo': str(i.remark),
                        }) for i in detail_response.detailList],
                        'state': 'sent',
                    })
                    _logger.info('------------ data 1  %s ----------', str(spec.qty))
                    _logger.info('------------ data 2  %s ----------', int(spec.unitCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))

                    _logger.info('------------ 생성 함 --------------')

                    amount_untaxed = 0
                    amount_tax = 0
                    amount_total = 0
                    for move in self.line_ids:
                        amount_untaxed += move.price_subtotal
                        amount_tax = amount_tax + move.amount_tax
                        amount_total = amount_total + move.price_subtotal + move.amount_tax

                    self.update(
                        {
                            "amount_untaxed": amount_untaxed,
                            "amount_tax": amount_tax,
                            "amount_total": amount_total,
                            "cashtype4": amount_total,
                        }
                    )
                else:

                    _logger.info('------------ 생성 되어 있음 --------------')

            except PopbillException as Err:
                raise UserError(
                    _("세금계산서 최산화 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )


    def check_etax_status_all_trustee(self):
        items = self.env["hometax.move"].search(
            [("state", "=", "sent")]
        )
        _logger.info('--------------- items %s --------------', items)
        if items:
            return self.check_etax_status_trustee(items)
        return None

    def check_etax_status_trustee(self, items):

        nfnum = []
        sdate = self.date_today
        ddate = self.date_time
        _logger.info('-------------- sdate %s -----------------', sdate)
        _logger.info('-------------- ddate %s -----------------', ddate)

        for obj in items:
            nfnum.append(obj.name)
            _logger.info('---------------- nfnum %s ----------------', nfnum)
            _logger.info('---------------- start %s ----------------', type(obj.date_today))
            _logger.info('---------------- finish %s ----------------', type(obj.date_time))

            CompanySudo = self.env['res.company'].search([('id', '=', obj.supplier_id.id)])
            _logger.info('--------------- companysudo %s --------------', CompanySudo)
            if CompanySudo == None:
                return
            etax_linkid = CompanySudo.etax_linkid
            SecretKey = CompanySudo.etax_secretkey
            user_id = CompanySudo.etax_userid
            etax_test = CompanySudo.etax_test
            company_no = CompanySudo.vat

        LinkID = etax_linkid
        SecretKey = SecretKey
        user_id = user_id
        etax_test = etax_test
        company_no = company_no


        taxinvoiceService = TaxinvoiceService(LinkID, SecretKey)
        taxinvoiceService.IsTest = etax_test
        list_name = []
        response_list = []
        CorpNum = company_no
        _logger.info('-------------- CorpNum %s -----------------',CorpNum)
        _logger.info('-------------- taxinvoiceService.IsTest %s -----------------', taxinvoiceService.IsTest)
        MgtKeyType = "BUY"
        DType = "R"
        SDate = ddate
        EDate = sdate
        State = ""
        Type = ""
        TaxType = ""
        LateOnly = ""
        TaxRegIDYN = ""
        TaxRegIDType = ""
        TaxRegID = ""
        Page = ""
        PerPage = ""
        Order = ""
        UserID = user_id
        QString = ""
        InterOPYN = ""
        IssueType = ""
        RegType = ""
        CloseDownState = ""
        MgtKey = ""

        response = taxinvoiceService.search(CorpNum, MgtKeyType, DType, SDate, EDate, State, Type, TaxType,
                                            LateOnly, TaxRegIDYN, TaxRegIDType, TaxRegID, Page, PerPage, Order,
                                            UserID, QString, InterOPYN, IssueType, RegType, CloseDownState,
                                            MgtKey)

        _logger.info('------------- response %s ---------', response.list)
        # 매출 문서함 거래 내역 조회 하여 문서번호 조회 내역 리스트에 적재
        for i in response.list:
            response_list.append(i.invoicerMgtKey)

        # 리스트에 적재한 문서번호를 상세조회 하여 데이터 추출
        for j in response_list:
            try:
                if j not in nfnum:
                    _logger.info('------------- j %s ---------', j)
                    MgtKey = j
                    detail_response = taxinvoiceService.getDetailInfo(CorpNum, MgtKeyType, MgtKey)
                    info_response = taxinvoiceService.getInfo(CorpNum, MgtKeyType, MgtKey)
                    product_uom_data = 1
                    tax_type = 1

                    # 규격 받아올때 사용하는 for문
                    for spec in detail_response.detailList:
                        t_sepc = str(spec.spec)
                        _logger.info('------------- t_spec %s -------------', t_sepc)

                        if t_sepc == "단위":
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "다스":
                            product_uom_data = 2
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "일":
                            product_uom_data = 3
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "시간":
                            product_uom_data = 4
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m":
                            product_uom_data = 5
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mm":
                            product_uom_data = 6
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "km":
                            product_uom_data = 7
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "cm":
                            product_uom_data = 8
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m²":
                            product_uom_data = 9
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "L":
                            product_uom_data = 10
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "m³":
                            product_uom_data = 11
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "kg":
                            product_uom_data = 12
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "g":
                            product_uom_data = 13
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "t":
                            product_uom_data = 14
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "lb":
                            product_uom_data = 15
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "oz":
                            product_uom_data = 16
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "분류":
                            product_uom_data = 17
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft":
                            product_uom_data = 18
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "mi":
                            product_uom_data = 19
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft²":
                            product_uom_data = 20
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "fl oz (US)":
                            product_uom_data = 21
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "qt(US)":
                            product_uom_data = 22
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 23
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "gal(US)":
                            product_uom_data = 24
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "in³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "ft³":
                            product_uom_data = 25
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)

                        if t_sepc == "Units":
                            product_uom_data = 1
                            _logger.info('-------------- 1 %s -------------', t_sepc)
                            _logger.info('-------------- product_uom_data %s -------------', product_uom_data)



                    ntsconfirmNum = str(info_response.ntsconfirmNum)
                    ntsresult = str(info_response.ntsresult)
                    ntssendDT = str(info_response.ntssendDT)
                    ntsresultDT = str(info_response.ntsresultDT)
                    ntssendErrCode = str(info_response.ntssendErrCode)
                    stateCode = int(info_response.stateCode)
                    itemKey = int(info_response.itemKey)

                    supplyCostTotal = str(detail_response.supplyCostTotal)
                    taxTotal = str(detail_response.taxTotal)
                    totalAmount = str(detail_response.totalAmount)
                    issueType = str(detail_response.issueType)
                    purposeType = str(detail_response.purposeType)
                    remark1 = str(detail_response.remark1)
                    taxType = str(detail_response.taxType)
                    ntsconfirmNum = str(detail_response.ntsconfirmNum)

                    if issueType == "정발행":
                        issueType = "issueType1"
                    if issueType == "역발행":
                        issueType = "issueType2"
                    if issueType == "위수탁":
                        issueType = "issueType3"

                    if purposeType == "영수":
                        purposeType = "purposeType1"
                    if purposeType == "청구":
                        purposeType = "purposeType2"
                    if purposeType == "없음":
                        purposeType = "purposeType3"

                    invoicerCorpName = str(detail_response.invoicerCorpName)
                    invoicerCEOName = str(detail_response.invoicerCEOName)
                    invoicerCorpNum = str(detail_response.invoicerCorpNum)
                    invoicerAddr = str(detail_response.invoicerAddr)
                    invoicerBizType = str(detail_response.invoicerBizType)
                    invoicerContactName = str(detail_response.invoicerContactName)
                    invoicerEmail = str(detail_response.invoicerEmail)
                    invoicerTEL = str(detail_response.invoicerTEL)
                    invoicerBizClass = str(detail_response.invoicerBizClass)



                    invoiceeCorpName = str(detail_response.invoiceeCorpName)
                    invoiceeCorpNum = str(detail_response.invoiceeCorpNum)
                    invoiceeMgtKey = str(detail_response.invoiceeMgtKey)
                    invoiceeType = str(detail_response.invoiceeType)
                    invoiceeCEOName = str(detail_response.invoiceeCEOName)
                    invoiceeAddr = str(detail_response.invoiceeAddr)
                    invoiceeBizType = str(detail_response.invoiceeBizType)
                    invoiceeBizClass = str(detail_response.invoiceeBizClass)
                    invoiceeContactName1 = str(detail_response.invoiceeContactName1)
                    invoiceeTEL1 = str(detail_response.invoiceeTEL1)
                    invoiceeEmail1 = str(detail_response.invoiceeEmail1)
                    invoiceeEmail2 = str(detail_response.invoiceeEmail2)

                    format = '%Y%m%d'
                    input = str(detail_response.writeDate)
                    writeDate = datetime.strptime(input, format)
                    invoicerMgtKey = str(detail_response.invoicerMgtKey)
                    customer_id = items.customer_id.id
                    customer_name = items.customer_id.name

                    list_name.append(str(detail_response.ntsconfirmNum))

                    obj.create({
                        'name': detail_response.invoicerMgtKey,
                        'supplier_id': customer_id,
                        'check_id': customer_id,
                        'supplier_vat_no': invoicerCorpNum,
                        'supplier_sangho': customer_name,
                        'supplier_ceo_name': invoicerCEOName,
                        'supplier_address': invoicerAddr,
                        'supplier_business_class': invoicerBizType,
                        'supplier_business_type': invoicerBizClass,
                        'supplier_name': invoicerContactName,
                        'supplier_email': invoicerEmail,
                        'supplier_tel': invoicerTEL,
                        'customer_id': customer_id,
                        'customer_vat_no': invoiceeCorpNum,
                        'customer_sangho': invoiceeCorpName,
                        'customer_jong': '',
                        'customer_ceo_name': invoiceeCEOName,
                        'customer_address': invoiceeAddr,
                        'customer_business_class': invoiceeBizType,
                        'customer_business_type': invoiceeBizClass,
                        'customer_name': invoiceeContactName1,
                        'customer_tel': invoiceeTEL1,
                        'customer_email1': invoiceeEmail1,
                        'customer_email2': invoiceeEmail2,
                        'writen_date': writeDate,
                        'amount_untaxed': supplyCostTotal,
                        'amount_tax': taxTotal,
                        "amount_total": totalAmount,
                        "issueType": issueType,
                        "purposeType": purposeType,
                        "reference": remark1,
                        "p_itemKey": itemKey,
                        "p_stateCode": stateCode,
                        "p_ntsconfirmNum": ntsconfirmNum,
                        "p_ntsresult": ntsresult,
                        "p_ntssendDT": ntssendDT,
                        "p_ntssendErrCode": ntssendErrCode,
                        "p_invoiceeCorpName": invoiceeCorpName,
                        "p_invoiceeCorpNum": invoiceeCorpNum,
                        'line_ids': [(0, 0, {
                            'writen_date': writeDate,
                            'labelname': str(i.itemName),
                            'product_uom_id': product_uom_data,
                            'quantity': str(i.qty),
                            'price_unit': int(i.unitCost),
                            'price_subtotal': str(i.supplyCost),
                            'amount_tax': str(i.tax),
                            'bigo': str(i.remark),
                        }) for i in detail_response.detailList],
                        'state': 'sent',
                    })
                    _logger.info('------------ data 1  %s ----------', str(spec.qty))
                    _logger.info('------------ data 2  %s ----------', int(spec.unitCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))
                    _logger.info('------------ data 3  %s ----------', str(spec.supplyCost))

                    _logger.info('------------ 생성 함 --------------')

                    amount_untaxed = 0
                    amount_tax = 0
                    amount_total = 0
                    for move in self.line_ids:
                        amount_untaxed += move.price_subtotal
                        amount_tax = amount_tax + move.amount_tax
                        amount_total = amount_total + move.price_subtotal + move.amount_tax

                    self.update(
                        {
                            "amount_untaxed": amount_untaxed,
                            "amount_tax": amount_tax,
                            "amount_total": amount_total,
                            "cashtype4": amount_total,
                        }
                    )
                else:

                    _logger.info('------------ 생성 되어 있음 --------------')

            except PopbillException as Err:
                raise exceptions.Warning(
                    _("세금계산서 최산화 오류 code %s message %s") % (Err.args[0], Err.args[1])
                )

