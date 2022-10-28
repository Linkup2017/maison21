import logging

from odoo import _, fields, models, api
from datetime import datetime, timedelta
from popbill import Contact, PopbillException, Taxinvoice, TaxinvoiceDetail, TaxinvoiceService, EasyFinBankService, AccountCheckService
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    etax_on = fields.Boolean(string="Popbill을 사용하시겠습니까 ??")
    etax_linkid = fields.Char(string="Popbill ID", default='LINKUPINFOTECH')
    etax_secretkey = fields.Char(string="Popbill Secretkey", default='bla2mqBjqr+oeAOOxaPWy17J/LSwmqHHkvk7O2jOkPE=')
    etax_userid = fields.Char("popBill user id", default='linkup2017')
    etax_issue_immediately = fields.Boolean("Issue Immediately")
    etax_test = fields.Boolean("Is Test")
    point = fields.Monetary(string='포인트: ', )
    ceo_name = fields.Char(string="CEO Name")
    business_class = fields.Char(string="업태")
    business_type = fields.Char(string="종목")
    jong_no = fields.Char(string="종사업장")
    address_all = fields.Char(string="사업장 주소")
    damdang_user = fields.Char(string="담당자")
    damdang_phone = fields.Char(string="연락처")
    damdang_email = fields.Char(string="이메일")
    damdang_email1 = fields.Char(string="이메일1")
    damdang_email2 = fields.Char(string="이메일2")
    reverse_bool = fields.Boolean(string="역발행 업체", default=False)

    connect_check = fields.Boolean('check', default=False)
    connect_string = fields.Selection([("draft", "연결 시도중"), ("connect", "연결 성공"),
                                       ("failed", "연결 실패")], string='연결 상태', default="draft"
                                      , readonly=True)

    account_id = fields.Many2one('account.journal', string='Confirmed Account')


    def checkIsMember(self):

        _logger.info('------------- checkIsMember -------------')
        LinkID = self.etax_linkid
        SecretKey = self.etax_secretkey
        company_no = self.vat
        etax_test = self.etax_test


        if company_no:
            _logger.info('------------- company_no %s ----------', company_no)
        else:
            self.connect_string = 'failed'
            raise ValidationError(_('사업자등록번호 확인'))

        if LinkID:
            _logger.info('------------- LinkID %s -------------', LinkID)
        else:
            self.connect_string = 'failed'
            raise ValidationError(_('Link ID 확인'))

        if SecretKey:
            _logger.info('------------- SecretKey %s -------------', SecretKey)
        else:
            self.connect_string = 'failed'
            raise ValidationError(_('SecretKey 확인'))


        easyFinBankService = EasyFinBankService(LinkID, SecretKey)
        easyFinBankService.IsTest = etax_test
        easyFinBankService.IPRestrictOnOff = False
        if company_no:

            CorpNum = company_no
            _logger.info('------------- %s CorpNum -------------', CorpNum)
            response = easyFinBankService.checkIsMember(CorpNum)
            _logger.info('------------- %s response -------------', response.code)


            if response.code == 1:
                self.connect_string = 'connect'
            if response.code == 0:
                self.connect_string = 'failed'

        else:
            raise ValidationError(_(' 일반정보 탭 에서 사업자번호 확인'))


    def etax_point_status(self):

        etax_linkid = self.etax_linkid
        etax_secretkey = self.etax_secretkey
        etax_userid = self.etax_userid
        etax_company_no = self.vat
        etax_test = self.etax_test

        if etax_linkid:
            _logger.info('------ etax_linkid %s', etax_linkid)
        else:
            raise ValidationError(_(' Link ID 확인 '))

        if etax_secretkey:
            _logger.info('------ etax_linkid %s', etax_secretkey)
        else:
            raise ValidationError(_(' Secretkey 확인 '))

        if etax_userid:
            _logger.info('------ etax_linkid %s', etax_userid)
        else:
            raise ValidationError(_(' User ID 확인 '))




        accountCheckService = AccountCheckService(etax_linkid, etax_secretkey)
        accountCheckService.IsTest = etax_test

        change_date = datetime.today().strftime('%Y%m%d')
        _logger.info('----------------- wirteDate %s -----------', change_date)
        if etax_company_no:
            # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            CorpNum = etax_company_no
            balance = accountCheckService.getPartnerBalance(CorpNum)

            if balance:
                self.point = int(balance)
                _logger.info("balance (포인트) : %s " % balance)
                return {
                    'name': _('Popbill Point'),
                    'res_model': 'popbill.point.wizard',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                }

            else:
                _logger.info("포인트 확인에 오류가 발생했습니다.")
        else:
            raise UserError(_('사업자 번호가 잘못 되었거나 없는 회사 정보가 있습니다.'))

    def write(self, vals):
        res = super(ResCompanyInherit, self).write(vals)
        partner_id = self.env['res.partner'].search([])


        for item in partner_id:
            if item.company_type == 'company':
                if item.id == self.partner_id.id:
                    _logger.info('-------- %s -=---', item.company_id)
                    item.ceo_name = self.ceo_name
                    item.address_all = self.address_all
                    item.business_class = self.business_class
                    item.business_type = self.business_type
                    item.jong_no = self.jong_no
                    item.damdang_phone = self.damdang_phone
                    item.damdang_user = self.damdang_user
                    item.damdang_email = self.damdang_email
                    item.damdang_email1 = self.damdang_email1
                    item.damdang_email2 = self.damdang_email2
                    _logger.info('------------ ceo_name %s -------------', item.name)


        return res






class AccountMove(models.Model):
    _inherit = "account.move"

    etax_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("sending", "Sending"),
            ("canceled", "Canceled"),
            ("sent", "Sent"),
            ("sent_error", "Sent Error"),
        ],
        string="eTax State",
        related="etax_id.state",
    )

    etax_id = fields.Many2one("hometax.move", string="Hometax bill", copy=False)
    etax_amount_total = fields.Monetary(
        string="eTax Amount", compute="_compute_tax_amount_total", currency_field="currency_id"
    )
    etax_type = fields.Selection(
        [("etaxType1", "전자세금계산서"), ("etaxType2", "[수정전자세금계산서]")],
        string="eTax Type",
        related="etax_id.etaxType",
    )
    etax_name = fields.Char(string="eTax number", related="etax_id.name")
    reverse_bool = fields.Boolean(string="Reverse eTax Partner", related="partner_id.reverse_bool")
    _logger.info('---------- reverse_bool ------  %s', reverse_bool)
    invisible_create_etax = fields.Boolean(
        string="Invisible Create eTax", compute="_compute_invisible_create_etax"
    )
    _logger.info('---------- invisible_create_etax ------  %s', invisible_create_etax)

    def _compute_invisible_create_etax(self):
        for item in self:
            invisible = False
            if item.state != "posted":
                invisible = True
            if item.reverse_bool:
                invisible = True

            if item.etax_id:
                invisible = True

            if (
                item.etax_id is not False
                and item.etax_type == "etaxType2"
                and item.etax_state == "sent"
            ):
                invisible = False

            item.write({"invisible_create_etax": invisible})

    def _compute_tax_amount_total(self):
        for item in self:
            item.etax_amount_total = 0
            if item.state == "posted":
                total = 0
                moves = (
                    self.env["hometax.move"]
                    .sudo()
                    .search([("sale_ids", "in", [item.id]), ("state", "!=", "draft")])
                )
                for move in moves:
                    total += move.amount_total

                item.etax_amount_total = total

    def create_etax(self):
        CompanySudo = self.env['res.company'].search([('id', '=', self.company_id.id)])

        if CompanySudo == None:
            return

        etax_company_id = CompanySudo.id
        etax_company_vat = CompanySudo.vat
        etax_company_jong_no = CompanySudo.jong_no
        etax_company_name = CompanySudo.name
        etax_company_ceo_name = CompanySudo.ceo_name
        etax_company_address_all = CompanySudo.address_all
        etax_company_business_class = CompanySudo.business_class
        etax_company_business_type = CompanySudo.business_type
        etax_company_damdang_user = CompanySudo.damdang_user
        etax_company_damdang_phone = CompanySudo.damdang_phone
        etax_company_damdang_email = CompanySudo.damdang_email
        etax_test = CompanySudo.etax_test

        etax_company = self.env["res.partner"].search([("id", "=", etax_company_id)], limit=1)
        _logger.info(' ------------------- etax_company %s -----------------', etax_company)
        saleobj = self.env["hometax.move"].create(
            {
                "sale_ids": [(6, 0, [self.id])],
                "check_id": etax_company_id,
                "supplier_id": etax_company_id,
                "supplier_vat_no": etax_company_vat,
                "supplier_jong": etax_company_jong_no,
                "supplier_sangho": etax_company_name,
                "supplier_ceo_name": etax_company_ceo_name,
                "supplier_address": etax_company_address_all,
                "supplier_business_class": etax_company_business_class,
                "supplier_business_type": etax_company_business_type,
                "supplier_name": etax_company_damdang_user,
                "supplier_tel": etax_company_damdang_phone,
                "supplier_email": etax_company_damdang_email,
                "customer_id": self.partner_id.id,
                "customer_vat_no": self.partner_id.vat,
                "customer_jong": self.partner_id.jong_no,
                "customer_sangho": self.partner_id.name,
                "customer_ceo_name": self.partner_id.ceo_name,
                "customer_address": self.partner_id.address_all,
                "customer_business_class": self.partner_id.business_class,
                "customer_business_type": self.partner_id.business_type,
                "customer_name": self.partner_id.damdang_user,
                "customer_tel": self.partner_id.damdang_phone,
                "customer_email1": self.partner_id.damdang_email1,
                "customer_email2": self.partner_id.damdang_email2,
                "etax_test": etax_test,
                # 'account_id':self.id
            }
        )
        saleobj.create_from_sale()
        self.write({"etax_id": saleobj.id})

        return saleobj

    def action_create_etax(self):
        if self.state == "posted":
            if self.etax_state is not None:
                saleobj = self.create_etax()
                self.update({"etax_id": saleobj.id})
                saleobj.sendhometax()
            else:
                hometaxmain = self.env["hometax.move"].search(
                    [("id", "=", self.etax_id.id)], limit=1
                )
                if hometaxmain:
                    hometaxmain.sendhometax()

    def open_etaxview(self):
        hometax_id = self.etax_id
        if hometax_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Home tax"),
                "res_model": "hometax.move",
                "view_mode": "form",
                "res_id": hometax_id.id,
                "views": [[False, "form"]],
            }


class HometaxMove(models.Model):
    _inherit = "hometax.move"
    sale_ids = fields.Many2many("account.move", string="Orders")  # 공급자 ID

    def create_batch_files(self, moves):

        if not moves:
            return

        CompanySudo = self.env['res.company'].search([("name", '=', self.partner_id.name)])


        for li in CompanySudo:
            etax_linkid = li.id

            _logger.info(' ------------------- etax_linkid %s -----------------', etax_linkid)
        etax_company_id = etax_linkid
        _logger.info(' ------------------- etax_linkid %s -----------------', etax_linkid)

        move = moves[0]
        saleobj = self.env["hometax.move"].create(
            {
                "sale_ids": [(6, 0, moves.ids)],
                "supplier_id": etax_company_id,
                "customer_id": move.partner_id.id,
                "supplier_vat_no": etax_company_id.vat,
                "supplier_jong": etax_company_id.jong_no,
                "supplier_sangho": etax_company_id.name,
                "supplier_ceo_name": etax_company_id.ceo_name,
                "supplier_address": etax_company_id.address_all,
                "supplier_business_class": etax_company_id.business_class,
                "supplier_business_type": etax_company_id.business_type,
                "supplier_name": etax_company_id.damdang_user,
                "supplier_tel": etax_company_id.damdang_phone,
                "supplier_email": etax_company_id.damdang_email,
                "customer_vat_no": move.partner_id.vat,
                "customer_jong": move.partner_id.jong_no,
                "customer_sangho": move.partner_id.name,
                "customer_ceo_name": move.partner_id.ceo_name,
                "customer_address": move.partner_id.address_all,
                "customer_business_class": move.partner_id.business_class,
                "customer_business_type": move.partner_id.business_type,
                "customer_name": move.partner_id.damdang_user,
                "customer_tel": move.partner_id.damdang_phone,
                "customer_email1": move.partner_id.damdang_email1,
                "customer_email2": move.partner_id.damdang_email2,
            }
        )
        saleobj.create_from_sale()
        moves.write({"etax_id": saleobj.id})

    def create_from_sale(self):

        sale_ids = self.sale_ids.ids

        items = self.env["account.move.line"].sudo().search([("move_id", "in", sale_ids)])
        for item in items:
            product_id = item.product_id
            quantity = item.quantity
            totalprice = item.credit - item.debit
            if quantity > 0:
                price_unit = totalprice / quantity

            # if not item.exclude_from_invoice_tab :
            if product_id:
                self.env["hometax.move.line"].sudo().create(
                    {
                        "move_id": self.id,
                        "labelname": item.name,
                        "product_id": product_id.id,
                        "quantity": quantity,
                        "product_uom_id": item.product_uom_id.id,
                        "price_unit": price_unit,
                    }
                )
            elif item.name :
                if item.product_uom_id:
                    self.env["hometax.move.line"].sudo().create(
                        {
                            "move_id": self.id,
                            "labelname": item.name,
                            "quantity": quantity,
                            "product_uom_id": item.product_uom_id.id,
                            "price_unit": price_unit,
                        }
                    )
                else:
                    self.env["hometax.move.line"].sudo().create(
                        {
                            "move_id": self.id,
                            "labelname": item.name,
                            "quantity": quantity,
                            "price_unit": price_unit,
                        }
                    )


