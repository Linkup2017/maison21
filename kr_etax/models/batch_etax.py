# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BatchEtaxapply(models.Model):
    _name = "batch.hometax.move"
    _description = "Issue tax invoices batch."

    def issue_move_batch(self):
        domain = [("id", "in", self._context.get("active_ids", [])), ("state", "=", "posted")]
        etaxmoves = self.env["account.move"].search(domain)
        if not etaxmoves:
            raise UserError(_("There are no etax items in the draft state to post."))
        supplier = None
        for move in etaxmoves:
            if supplier is None:
                supplier = move.partner_id.id
            elif supplier != move.partner_id.id:
                raise UserError(_("The selected invoice is different from the customer"))

        for move in etaxmoves:
            if move.etax_id:
                if move.etax_id.state != "cancelled" and not (
                    move.etax_type == "etaxType2" and move.etax_state == "sent"
                ):
                    raise UserError(_("This Invoice(s) already has been Issued"))
            elif move.reverse_bool:
                raise UserError(_("you can’t make an eTax for this customer(reversed)"))

        self.env["hometax.move"].sudo().create_batch_files(etaxmoves)
        return {"type": "ir.actions.act_window_close"}


class BatchEtaxsend1(models.Model):
    _name = "batch.send.hometax.move"
    _description = "Issue tax invoices batch."

    def issue_move_batch_send(self):
        domain = [("id", "in", self._context.get("active_ids", [])), ("state", "=", "draft")]
        etaxmoves = self.env["hometax.move"].search(domain)
        if not etaxmoves:
            raise UserError(_("There are no etax items in the draft state"))
        for etax in etaxmoves:
            etax.sendhometax()
        return {"type": "ir.actions.act_window_close"}
