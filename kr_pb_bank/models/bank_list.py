import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService


class BankList(models.Model):
    _name = 'res.bank.list'

    name = fields.Char(string='Bank Name')
    bank_code = fields.Char(string='Bank Code')
    type_selection = fields.Selection([('bank', '은행'),
                                       ('card', '카드사')], string="Type"
                                      , default="bank")
