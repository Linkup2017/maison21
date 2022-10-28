import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo

try:
    sys.setdefaultencoding('UTF8')
except Exception as E:
    pass

import logging
_logger = logging.getLogger(__name__)


class banklookup(models.Model):
    _name = "transaction.history.inquiry"
    _order = "trdt desc"

    name = fields.Char(string='Name')
    date = fields.Date(string='Date', required=True, index=True, copy=False, default=fields.Date.context_today)
    payment_ref = fields.Char(string='Label', required=True)
    narration = fields.Char(string='Memo')
    transaction_type = fields.Char(string='Transaction Type')
    amount_currency = fields.Monetary(currency_field='foreign_currency_id',
        help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    foreign_currency_id = fields.Many2one('res.currency', string='Foreign Currency')
    deposit = fields.Monetary(currency_field='foreign_currency_id', string='deposit')
    withdraw = fields.Monetary(currency_field='foreign_currency_id', string='withdraw')
    amount = fields.Monetary(currency_field='foreign_currency_id')
    account_number = fields.Char(string='Bank Account Number')
    currency_id = fields.Many2one('res.currency', string='Journal Currency')
    trdt = fields.Datetime(string='Transaction Date')
    tid = fields.Char(string='tid')
    bank_id = fields.Many2one('account.journal', string='Bank ID',  default=lambda self: self.env['account.journal'].search(['|', ('type', '=', 'bank'), ('name', '=', 'name')]))
    bank_id_name = fields.Many2one(related='bank_id.bank_id', string="Bank ID")


class SearchResBank(models.Model):
    _inherit = 'res.bank'

    bank_code = fields.Char(string='Bank Code')
