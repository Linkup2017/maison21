
from odoo import models, fields, api, _, SUPERUSER_ID
import requests
import ast
from odoo.tools import html2plaintext, plaintext2html

from popbill import PopbillException, ContactInfo, CorpInfo, JoinForm, MessageService, \
    MessageReceiver

import logging
_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _contact_iap(self, local_endpoint, params):
        CompanySudo = self.env['res.company'].search([('id', '=', self.env.company.id)])
        _logger.warning('-------------- companysudo %s ------------', CompanySudo)
        if CompanySudo.etax_on == False:
            return
        '''POPBILL로 문자 발송'''
        _logger.warning('-----start of _contact_iap-----%s' % params)

        sms_linkid = CompanySudo.etax_linkid
        sms_secretkey = CompanySudo.etax_secretkey
        sms_company_no = CompanySudo.vat
        sms_userid = CompanySudo.etax_userid
        sms_test = CompanySudo.etax_test
        messages = params['messages']
        newmessage = []
        testmode = 'Y'
        subject = '[LINKUP]'
        _logger.warning('-------------- sms_linkid %s ------------' % sms_linkid)
        _logger.warning('-------------- sms_secretkey %s ------------' % sms_secretkey)
        _logger.warning('-------------- sms_company_no %s ------------' % sms_company_no)
        _logger.warning('-------------- sms_userid %s ------------' % sms_userid)
        _logger.warning('-------------- sms_test %s ------------' % sms_test)

        messageService = MessageService(sms_linkid, sms_secretkey)

        # 연동환경 설정값, 개발용(True), 상업용(False)
        messageService.IsTest = sms_test

        # 인증토큰 IP제한기능 사용여부, 권장(True)
        messageService.IPRestrictOnOff = True

        # 팝빌 API 서비스 고정 IP 사용여부(GA), true-사용, false-미사용, 기본값(false)
        messageService.UseStaticIP = False

        # 로컬시스템 시간 사용여부, 권장(True)
        messageService.UseLocalTimeYN = True


        for record in messages:
            kakao_validation = False
            if 'template_id' in record:
                template = self.env['sms.template'].search([('id', '=', record['template_id'].id)])
                kakao_validation = template.kakao_validation
                next_message = template.next_message
                model_id = record['model_id']
                subject = template.name

            res_id = record['res_id']
            onumber = record['number']
            content = record['content']
            cod = {'credit': 0, 'res_id': res_id, 'state': 'success'}

            _logger.info('-------- onumber %s ----', onumber)

            #문자열 변경
            new_onumber = onumber.replace('+82', '0')
            new_sender = self.env.company.partner_id.mobile.replace('+82', '0')

            _logger.info('-------- onumber %s ----', new_onumber)
            _logger.info('-------- new_sender %s ----', new_sender)


            # 문자 발송

            CorpNum = sms_company_no
            # 팝빌회원 아이디
            UserID = sms_userid
            # 발신번호
            Sender = new_sender
            # 발신자명
            SenderName = self.env.company.partner_id.name
            # 수신번호
            ReceiverNum = new_onumber
            # 수신자명w
            ReceiverName = ''
            # 단문메시지 내용, 90Byte 초과시 길이가 조정되 전송됨
            Contents = content
            # 예약전송시간, 작성형식:yyyyMMddHHmmss, 공백 기재시 즉시전송
            reserveDT = ""
            # 광고문자 전송여부
            adsYN = False

            _logger.warning('--sender--%s SenderName %s ReceiverNum %s' % (Sender,SenderName,ReceiverNum))
            _logger.warning('--sender data -- CorpNum: %s UserID: %s Sender: %s '
                            'SenderName: %s ReceiverNum: %s ReceiverName: %s Contents: %s reserveDT: %s'
                            % (CorpNum,UserID,Sender,SenderName,ReceiverNum,ReceiverName,Contents,reserveDT))
            _logger.warning('-------------- companysudo %s ------------' % CompanySudo.vat)
            # 전송요청번호
            # 파트너가 전송 건에 대해 관리번호를 구성하여 관리하는 경우 사용.
            # 1~36자리로 구성. 영문, 숫자, 하이픈(-), 언더바(_)를 조합하여 팝빌 회원별로 중복되지 않도록 할당.
            RequestNum = ""
            receiptNum = messageService.sendSMS(CorpNum, Sender, ReceiverNum, ReceiverName,
                                                Contents, reserveDT, adsYN, UserID, SenderName, RequestNum)
            if not receiptNum:
                cod['state'] = 'wrong_number_format'
            _logger.info(cod)
            newmessage.append(cod)
        _logger.info('-----end of _contact_iap-----')
        return newmessage
    #
    # @api.model
    # def _send_sms(self, numbers, message):
    #     return super(SmsApi, self)._send_sms(numbers, message)

    @api.model
    def _send_sms_batch(self, messages):
        _logger.info('------start of _send_sms_batch-----')
        kakao_validation = False
        for record in messages:
            if 'template_id' in record:
                template_id = record['template_id']
                template = self.env['sms.template'].search([('id', '=', template_id.id)])
                kakao_validation = template.kakao_validation
        params = {'messages': messages}

        if kakao_validation:
            data = self._contact_iap('', params)
        else:
            data = self._contact_iap('', params)
        return data


class SmsSms(models.Model):
    _inherit = 'sms.sms'

    IAP_TO_SMS_STATE = {
        'success': 'sent',
        'insufficient_credit': 'sms_credit',
        'wrong_number_format': 'sms_number_format',
        'server_error': 'sms_server'
    }

    template_id = fields.Many2one('sms.template')
    model_id = fields.Integer()

    def _send(self, unlink_failed=False, unlink_sent=True, raise_exception=False):

        iap_data = [{
            'res_id': record.id,
            'number': record.number,
            'content': record.body,
            'template_id': record.template_id,
            'model_id': record.model_id
        }for record in self]

        try:
            iap_results = self.env['sms.api']._send_sms_batch(iap_data)
        except Exception as e:
            _logger.info('Sent batch %s SMS: %s: failed with exception %s', len(self. ids), self.ids, e)
            _logger.info('res_id : %s number : %s content : %s template_id : %s model_id : %s',
                         self.id, self.number, self.body, self.template_id, self.model_id)

            if raise_exception:
                raise
            self._postprocess_iap_sent_sms([{'res_id': sms.id, 'state':'server_error'}for sms in self],
                                           unlink_failed=unlink_failed, unlink_sent=unlink_sent)
        else:
            _logger.info('Send batch %s SMS: %s: gave %s', len(self.ids), self.ids, iap_results)
            self._postprocess_iap_sent_sms(iap_results, unlink_failed=unlink_failed, unlink_sent=unlink_sent)

    def _postprocess_iap_sent_sms(self, iap_results, failure_reason=None, unlink_failed=False, unlink_sent=True):
        _logger.info('-----postprocess_iap_sent_sms-----')
        _logger.info(iap_results)

        todelete_sms_ids = []

        if unlink_failed:
            todelete_sms_ids += [item['res_id'] for item in iap_results if item['state'] != 'success']
        if unlink_sent:
            todelete_sms_ids += [item['res_id'] for item in iap_results if item['state'] == 'success']


        for state in self.IAP_TO_SMS_STATE.keys():
            sms_ids = [item['res_id'] for item in iap_results if item['state'] == state]
            if sms_ids:
                if state != 'success' and not unlink_failed:
                    _logger.info('------ ')
                    self.env['sms.sms'].sudo().browse(sms_ids).write({
                        'state': 'error',
                        'failure_type': self.IAP_TO_SMS_STATE[state],

                    })
                if state == 'success' and not unlink_sent:
                    self.env['sms.sms'].sudo().browse(sms_ids).write({
                        'state': 'sent',
                        'failure_type': False,
                    })
                notifications = self.env['mail.notification'].sudo().search([
                    ('notification_type', '=', 'sms'),
                    ('sms_id', 'in', sms_ids),
                    ('notification_status', 'not in', ('sent', 'canceled'))
                ])
                if notifications:
                    _logger.warning('-----notifications-----')

                    notifications.write({
                        'notification_status': 'sent' if state == 'success' else 'exception',
                        'failure_type': self.IAP_TO_SMS_STATE[state] if state != 'success' else False,
                        'failure_reason': failure_reason if failure_reason else False,
                    })
                    _logger.warning(notifications)
        self.mail_message_id._notify_message_notification_update()

        if todelete_sms_ids:
            self.browse(todelete_sms_ids).sudo().unlink()

        # if todelete_sms_ids:
        #     self.browse(todelete_sms_ids).sudo().unlink()

class SMSTemplate(models.Model):
    _inherit = 'sms.template'

    token = fields.Char(string='Token', compute='compute_kakao_api_token')
    template_code = fields.Char(readonly=True)
    kakao_validation = fields.Boolean(string='Kakao Talk Validation')
    next_message = fields.Many2one('sms.template', string='Next Message', default=False)
    result_approve = fields.Char(readonly=True)
