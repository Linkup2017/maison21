from odoo.http import request
from odoo import _, api, exceptions, fields, models, http

class Main(http.Controller):

  @http.route('/kr_pb_integrate/bank', auth='public', website=True)
  def books(self):
   # move = request.env['hometax.move'].sudo().search([])
   # html_result = '<html><body><ul>'
   #
   # for book in move:
   #  html_result += "<li> %s </li>" % book.name
   #  html_result += '</ul></body></html>'
   return "Test"

   @http.route('/kr_pb_integrate/bank/json', type='json',auth='none')
   def books_json(self):
    records = request.env['hometax.move'].sudo().search([])
    return records.read(['name'])
