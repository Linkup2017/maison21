import sys
from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from popbill import EasyFinBankService, PopbillException, ContactInfo, JoinForm, CorpInfo, BankAccountInfo, AccountCheckService
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class HomeTaxOrdersWizard(models.TransientModel):
    _name = "hometax.orders.wizard"

    @api.model
    def get_values(self):
        ids = self.env['account.move'].search([('payment_state', '=', 'not_paid')]).ids
        _logger.info('----------- %s ids ---------------', ids)
        return ids



    hometax_id = fields.Many2one('hometax.move')
    account_ids = fields.Many2many('account.move', 'amount_total_signed', string='account')

    def sendaccount(self):
        ids = []
        domain = [("id", "in", self._context.get("active_ids", [])), ("state", "=", "sent")]
        moves = self.env["hometax.move"].search(domain)
        _logger.info('-------------------- send account -------------------')
        value = self.env.context.get('active_id')
        _logger.info('---------- value %s', value)
        _logger.info('---------- etaxmoves %s', moves.sale_ids)
        if value:
            vat = value
            _logger.info('---------- vat %s', vat)
            for lo in self.account_ids:
                _logger.info('--------- tax %s ---------', lo.id)
                ids.append(lo.id)
                _logger.info('--------- ids %s ---------', ids)
        moves.write({"sale_ids": [(6, 0, ids)]})