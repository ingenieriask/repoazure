import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.contrib.postgres.search import SearchVector, SearchQuery
from correspondence.models import Radicate, ProcessActionStep, ReceptionMode, RadicateTypes, AlfrescoFile
from workflow.models import FilingFlow, FilingNode
from core.models import Alert, Template
from pqrs.models import PQRS, Record, PqrsContent, SubType, Type
from django.contrib.auth.models import User
from django.contrib import messages
from core.services import UserHelper
from django.shortcuts import get_object_or_404
from django.core.files.temp import NamedTemporaryFile
from core.utils_services import FormatHelper
import logging
import json
import os
from django.core.files import File
from core.models import AppParameter, RequestResponse
from core.services import NotificationsHandler, RecordCodeService, Recipients, DocxCreationService, HtmlPdfCreationService
from pinax.eventlog.models import log, Log
from django.urls import reverse
from crum import get_current_user
from correspondence.ecm_services import ECMService

logger = logging.getLogger(__name__)

class RadicateService(object):
    '''Utilities for Radicate'''

    @classmethod
    def add_to_record(cls, parent, current):
        for record in parent.records.all():
            record.radicates.add(current)
            record.save()
            ECMService.copy_item(current.folder_id, record.cmis_id)

    @classmethod
    def process_next_action(cls, pqrs):
        try:
            flow = FilingFlow.objects.get(subtype=pqrs.subtype)
        except FilingFlow.DoesNotExist:
            flow = None

        if flow:
            try:
                notification = FilingNode.objects.get(type='Asignar', filing_flow=flow)
            except:
                notification = None
            if notification:
                user = notification.users.all()[0]
                ###TODO definir el área
                RadicateService.assign_to_user_service(pqrs, user, None, 'Asignación automática', reverse('pqrs:detail_pqr', kwargs={'pk': pqrs.pk}), get_current_user(), PQRS.Status.ASSIGNED)
                
                pqrs.pqrsobject.save()
                pqrs.save()
            try:
                notification = FilingNode.objects.get(type='Notificar', filing_flow=flow)
            except:
                notification = None
            if notification:
                users = []
                for user in notification.users.all():
                    users.append(user.pk)
                RadicateService.report_to_users_service(pqrs, users, 'Notificación automática', reverse('pqrs:reported_detail_pqr', kwargs={'pk': pqrs.pk}), get_current_user())
                pqrs.save()

    @classmethod
    def answer_radicate(cls, radicate, answered, request):
        radicate.number = RecordCodeService.get_consecutive(RecordCodeService.Type.OUTPUT)
        cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
        radicate.folder_id = ECMService.create_folder(cmis_id, radicate.number)
        radicate.classification = Radicate.Classification.COMPLETE_ANSWER
        radicate.stage = Radicate.Stage.CLOSED
        radicate.mother = answered
        radicate.save()

        answered.stage = Radicate.Stage.CLOSED
        radicate.classification = Radicate.Classification.ANSWERED
        answered.save()

        for file in AlfrescoFile.objects.filter(radicate=radicate):
            ECMService.move_item(file.cmis_id, radicate.folder_id)

        DocxCreationService.mix_from_template(Template.Types.PQR_CREATION, radicate)
        query_url = "{0}://{1}/pqrs/consultation/result/{2}".format(request.scheme, request.get_host(), answered.pk)
        radicate.url = query_url

        NotificationsHandler.send_notification('EMAIL_PQR_ANSWER', radicate, Recipients(radicate.person.email if radicate.person else radicate.email_user_email))
        
        action = ProcessActionStep()
        action.user = get_current_user()
        action.action = ProcessActionStep.ActionTypes.ANSWER
        action.detail = 'La PQRSD %s ha sido respondida con el radicado %s' % (radicate.parent.number, radicate.number) 
        action.radicate = radicate
        action.save()

    @classmethod
    def create_record(cls, pqrs):
        record = Record()
        record.type = pqrs.pqrsobject.pqr_type
        record.subtype = pqrs.subtype
        record.responsable = get_current_user()
        record.subject = pqrs.subject
        record.source = str(pqrs.person) if pqrs.person else pqrs.email_user_name
        record.name = RecordCodeService.get_proceedings_consecutive(str(pqrs.pqrsobject.pqr_type.pk).zfill(2) + str(pqrs.subtype.pk).zfill(3))
        cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
        record.cmis_id = ECMService.create_folder(cmis_id, record.name)
        record.save()
        record.radicates.add(pqrs)
        record.save()
        ECMService.copy_item(pqrs.folder_id, record.cmis_id)

    @classmethod
    def process_files(cls, files, instance, request=None):
        consecutive = 0
        for fileUploaded in files:
            consecutive += 1
            document_temp_file = NamedTemporaryFile()
            for chunk in fileUploaded.chunks():
                document_temp_file.write(chunk)

            document_temp_file.seek(0)
            document_temp_file.flush()

            node_id = ECMService.upload(File(document_temp_file, name=fileUploaded.name), instance.folder_id)
            alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=instance,
                                        name=os.path.splitext(instance.number+'-'+str(consecutive).zfill(5))[0],
                                        extension=os.path.splitext(fileUploaded.name)[1],
                                        size=int(fileUploaded.size/1000))
            alfrescoFile.save()

            if request and not node_id or not ECMService.request_renditions(node_id):
                messages.error(request, "Ha ocurrido un error al guardar el archivo en el gestor de contenido")
        instance.attachment_quantity = consecutive
        instance.save()

    @classmethod
    def create_action_creation(cls, instance):
        action = ProcessActionStep()
        action.user = get_current_user()
        action.action = ProcessActionStep.ActionTypes.CREATION
        action.detail = 'El radicado %s ha sido creado' % (instance.number) 
        action.radicate = instance
        action.save()

        log(
            user=get_current_user(),
            action="RADICATE_CREATED",
            obj=action,
            extra={
                "number": instance.number,
                "message": "El radicado %s ha sido creado" % (instance.number)
            }
        )

    @classmethod
    def fill_from_parent(cls, instance, radicate):
        instance.type = radicate.type
        instance.record = radicate.record
        instance.person = radicate.person
        instance.email_user_email = radicate.email_user_email
        instance.email_user_name = radicate.email_user_name
        instance.reception_mode = radicate.reception_mode
        instance.office = radicate.office
        instance.doctype = radicate.doctype
        instance.parent = radicate
        instance.subject = radicate.subject

    @classmethod
    def create_pqr_from_email(cls, message):
        pqrs_type = get_object_or_404(Type, name='EMAIL')
        pqrs_object=PQRS(pqr_type = pqrs_type)
        pqrs_object.status = PQRS.Status.EMAIL
        pqrs_object.save()

        instance = PqrsContent()
        instance.subject = message.subject
        instance.data = message.html
        instance.email_user_email = message.from_address[0]
        instance.email_user_name = message.from_header.replace(('<%s>' % instance.email_user_email), '')
        instance.reception_mode = get_object_or_404(ReceptionMode, abbr='EMAIL')
        instance.type = get_object_or_404(RadicateTypes, abbr='PQR')
        instance.subtype = get_object_or_404(SubType, name='EMAIL')
        instance.number = 'Por asignar'
        instance.response_mode = get_object_or_404(RequestResponse, abbr='CE')
        instance.pqrsobject = pqrs_object
        instance.folder_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
        instance.agreement_personal_data = False

        instance.save()
        consecutive = 0
        for att in message.attachments.all():
            consecutive += 1
            idx = att.headers.find('name="') + len('name="')
            name = att.headers[idx:att.headers.find('"', idx)]
            node_id = ECMService.upload(att.document, instance.folder_id, name)
            alfrescoFile = AlfrescoFile(cmis_id=node_id, radicate=instance,
                                        name=name.split('.')[-2],
                                        extension='.' + name.split('.')[-1],
                                        size=int(att.document.size/1000))
            alfrescoFile.save()

        instance.attachment_quantity = consecutive
        instance.save()

        action = ProcessActionStep()
        action.action = ProcessActionStep.ActionTypes.MAIL_IMPORT
        action.detail = 'Un nuevo radicado ha sido importado'
        action.radicate = instance
        action.save()

        for user in UserHelper.list_by_permission_name('receive_from_email'):
            alert = Alert()
            alert.info = 'Un nuevo radicado ha sido importado'
            alert.assigned_user = user
            alert.href = reverse('pqrs:email_detail_pqr', kwargs={'pk': instance.pk})
            alert.save()

    @classmethod
    def process_pqr_creation(cls, pqrsoparent, form, request, person):
        instance = form.save(commit=False)
        instance.reception_mode = get_object_or_404(ReceptionMode, abbr='VIR')
        instance.type = get_object_or_404(RadicateTypes, abbr='PQR')
        instance.number = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
        instance.response_mode = person.request_response
        instance.person = person
        instance.pqrsobject = pqrsoparent
        radicate =  form.save()
        cmis_id = AppParameter.objects.get(name='ECM_TEMP_FOLDER_ID').value
        folder_id = ECMService.create_folder(cmis_id, radicate.number)
        radicate.folder_id = folder_id
        
        cls.process_files(request.FILES.getlist('pqrs_creation_uploaded_files'), instance, request)
        radicate.save()
        formatted_data = Template.objects.get(type=Template.Types.PQR_CREATION).file.read().decode("utf-8") 
        formatted_data = FormatHelper.replace_data_preparing_html(formatted_data, radicate)
        radicate.data = formatted_data

        cls.create_action_creation(instance)

        query_url = "{0}://{1}/pqrs/consultation/result/{2}".format(request.scheme, request.get_host(), radicate.pk)
        instance.url = query_url
        NotificationsHandler.send_notification('EMAIL_PQR_CREATE', instance,  Recipients(instance.person.email, None, instance.person.phone_number))
        ### TODO eval in intern creation
        # PdfCreationService.create_pqrs_confirmation_label(radicate)
        cls.process_next_action(instance)
        cls.create_record(instance)

        HtmlPdfCreationService.generate_pdf(Template.Types.PQR_CREATION, instance.data, instance)
        return instance
        
    @classmethod
    def create_action(cls, current_user, user, area, type, detail, radicate, observation, alert_info, destination_users=None, url=None):
    
        action = ProcessActionStep()
        action.user = current_user
        action.destination_user = user
        action.action = type
        action.detail = detail
        action.radicate = radicate
        action.functional_area = area
        action.observation = observation
        action.save()
        if destination_users:
            action.destination_users.set(destination_users)
            action.save()

        if url:
            alert = Alert()
            alert.info = alert_info
            alert.assigned_user = user
            alert.href = url
            alert.save()

        log(
            user=current_user,
            action=type,
            obj=action,
            extra={
                "number": radicate.number,
                "message": detail
            }
        )
    
    @classmethod
    def assign_to_user_service(cls, pqrs, user, area, observation, url, current_user, status):
        pqrs.last_user = current_user
        pqrs.current_user = user
        pqrs.current_functional_area = area
        pqrs.pqrsobject.status = status

        detail = "El radicado %s ha sido asignado a %s" % (pqrs.number, user.username)
        alert_info = 'Te han asignado el radicado %s' % pqrs.number
        cls.create_action(current_user, user, area, ProcessActionStep.ActionTypes.ASSIGNATION, detail, pqrs, observation, alert_info, None, url)


    @classmethod
    def report_to_users_service(cls, pqrs, users_to_report, observation, url, current_user):
        users=''
        destination_users = []
        for userPK in users_to_report:
            user = User.objects.get(pk=userPK)

            pqrs.reported_people.add(user)
            users += user.username + ', '
            destination_users.append(user)

        detail = "El radicado %s ha sido informado a los usuarios %s" % (pqrs.number, users)
        alert_info = 'Te han informado del radicado %s' % pqrs.number
        cls.create_action(current_user, user, pqrs.current_functional_area, ProcessActionStep.ActionTypes.REPORT, \
            detail, pqrs, observation, alert_info, destination_users, url)
