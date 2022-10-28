# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)




class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_kr_pb_bank = fields.Boolean(string='Pb Bank')
    module_kr_pb_issue = fields.Boolean(string='Pb Issue')
    module_kr_pb_integrate = fields.Boolean(string='Pb Integrate')
    module_kr_pb_sms = fields.Boolean(string='Pb Sms')
    module_account_card = fields.Boolean(string='Pb Card')
