from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import logging
import json
from enum import Enum
from workflow.models import SignatureFlow, SignatureNode, FilingFlow, FilingNode, SignatureAreaUser, FilingAreaUser
from core.models import FunctionalArea

logger = logging.getLogger(__name__)

class FlowService(object):

    class FlowType(Enum):
        FILING = 'Filing'
        SIGNATURE = 'Signature'

    @classmethod
    def get_initial_json(cls):
        graph = {
            "id": "demo@0.1.0",
            "nodes": {
                "1": {
                "id": 1,
                "data": {},
                "inputs": {},
                "outputs": {
                    "out": {
                    "connections": []
                    }
                },
                "position": [
                    0,
                    100
                ],
                "name": "Inicio"
                },
                "2": {
                "id": 2,
                "data": {},
                "inputs": {
                    "in": {
                    "connections": []
                    }
                },
                "outputs": {},
                "position": [
                    800,
                    100
                ],
                "name": "Fin"
                },
            }
        }
        return graph

    @classmethod
    def to_json(cls, pk, flow_type=None):
        if not flow_type:
            flow_type = cls.FlowType.FILING

        end_node = None
        if flow_type == cls.FlowType.SIGNATURE:
            end_node = SignatureNode.objects.filter(signature_flow__id=pk, type=SignatureNode.Types.OUTPUT).first()
        else:
            end_node = FilingNode.objects.filter(filing_flow__id=pk, type=FilingNode.Types.OUTPUT).first()

        if end_node:
            formated_nodes = {}
            cls._format_node(end_node, formated_nodes, flow_type)
            return {
                "id": "demo@0.1.0",
                "nodes": formated_nodes
            }
        return cls.get_initial_json()

    @classmethod
    def _append_output(cls, outputs, next_node):
        if next_node:
            outputs['out']['connections'].append(
                {
                    "node": next_node,
                    "input": "in",
                    "data": {}
                }
            )

    @classmethod
    def _format_node(cls, node, formated_nodes, flow_type, next_node=None):
        if node.index in formated_nodes:
            cls._append_output(formated_nodes[node.index]['outputs'], next_node)
        else:
            outputs = {
                "out": {
                    "connections": []
                }
            }
            cls._append_output(outputs, next_node)
            properties = json.loads(node.properties)
            previous_nodes = node.previous.all()
            inputs = {}
            if previous_nodes:
                inputs = {
                    "in": {
                        "connections": [
                            {
                                "node": n.index,
                                "output": "out",
                            }
                            for n in previous_nodes
                        ]
                    }
                }

            if flow_type == cls.FlowType.FILING:
                users = []
                for user in node.area_users.all():
                    users.append(
                        {
                            'id': user.user.id,
                            'username': user.user.username, 
                            'first_name': user.user.first_name,
                            'last_name': user.user.last_name,
                            'area_id': user.area.id
                        }
                    )
            else:
                user = {
                    'id': node.area_user.user.id,
                    'username': node.area_user.user.username, 
                    'first_name': node.area_user.user.first_name,
                    'last_name': node.area_user.user.last_name,
                    'area_id': node.area_user.area.id,
                } if node.area_user else {}            

            formated_node = {
                'id': node.index,
                'data': {
                    **({'users': users} if flow_type == cls.FlowType.FILING else {'user': user}), 
                    'time': node.time
                },
                'inputs': inputs,
                'outputs': outputs,
                **properties,
                'name': node.type
            }
            formated_nodes[node.index] = formated_node

            for previous_node in previous_nodes:
                cls._format_node(previous_node, formated_nodes, flow_type, node.index)

        return 

    @classmethod
    def from_json(cls, graph, flow_type=None, flow_id=None):

        if not flow_type:
            flow_type = cls.FlowType.FILING

        nodes = {}
        node_list = []
        user_list = []

        acc = {
            SignatureNode.Types.SIGNINGUSER: 0,
            SignatureNode.Types.LEGALSIGNINGUSER: 0,
            SignatureNode.Types.GUARANTORUSER: 0,
            FilingNode.Types.ASSIGNEDUSER: 0,
            FilingNode.Types.INFORMEDUSER: 0,
            FilingNode.Types.INPUT: 0,
            FilingNode.Types.OUTPUT: 0
        }

        if flow_id:
            sf = FilingFlow(pk=int(flow_id)) if flow_type == cls.FlowType.FILING else SignatureFlow(pk=int(flow_id)) 
        else:
            sf = FilingFlow() if flow_type == cls.FlowType.FILING else SignatureFlow(name='', description='')

        for key, n in graph['nodes'].items():
            properties = {'position': n['position']}
            time = 2

            if n['name'] != FilingNode.Types.INPUT:
                if not n['inputs']['in']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")

            if n['name'] != FilingNode.Types.OUTPUT:  
                if not n['outputs']['out']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")
                                
            acc[n['name']] += 1

            if flow_type == cls.FlowType.FILING:
                users = []
                if n['name'] in [FilingNode.Types.ASSIGNEDUSER,  
                                FilingNode.Types.INFORMEDUSER]:
                    if n['data'] and n['data']['users']:
                        for user_id in n['data']['users']:
                            print('user_id:', user_id)
                            user = User.objects.get(pk=int(user_id['id']))
                            area = FunctionalArea.objects.get(pk=int(user_id['area_id']))
                            areaUser = FilingAreaUser(user=user, area=area) 
                            users.append(areaUser)
                        n['data']['users'] = [{
                            'id': user.user.id,
                            'username': user.user.username, 
                            'first_name': user.user.first_name,
                            'last_name': user.user.last_name,
                            'area_id': user.area.id
                        } for user in users]
                        time = n['data']['time']
                    else:
                        raise ValidationError("Debe seleccionar un usuario para cada estado")

                node = FilingNode(
                    type=n['name'], 
                    index=n['id'],
                    properties=json.dumps(properties),
                    filing_flow=sf,
                    time=time)

                user_list.append(users)
            else:
                user = None
                if n['name'] in [SignatureNode.Types.SIGNINGUSER,  
                                SignatureNode.Types.GUARANTORUSER,
                                SignatureNode.Types.LEGALSIGNINGUSER]:
                    if n['data'] and n['data']['user']['id'] and n['data']['user']['id'] != '-1':
                        u = User.objects.get(pk=int(n['data']['user']['id']))
                        area = FunctionalArea.objects.get(pk=int(n['data']['user']['area_id']))
                        user = SignatureAreaUser(user=u, area=area)
                        n['data']['user'] = {
                            'id': user.user.id,
                            'username': user.user.username, 
                            'first_name': user.user.first_name,
                            'last_name': user.user.last_name,
                            'area_id': user.area.id
                        }
                        time = n['data']['time']
                    else:
                        raise ValidationError("Debe seleccionar un usuario para cada estado")

                node = SignatureNode(
                    type=n['name'], 
                    index=n['id'],
                    area_user=user,
                    properties=json.dumps(properties),
                    signature_flow=sf,
                    time=time)

            node_list.append(node)

        if acc[FilingNode.Types.INPUT] > 1 or acc[FilingNode.Types.OUTPUT] > 1:
            raise ValidationError("Solo se permiten un nodo de entrada y un nodo de salida")
        if acc[FilingNode.Types.INPUT] == 0 or acc[FilingNode.Types.OUTPUT] == 0:
            raise ValidationError("Se requiere un nodo de entrada y un nodo de salida")
        if acc[FilingNode.Types.ASSIGNEDUSER] > 1 or acc[FilingNode.Types.INFORMEDUSER] > 1:
            raise ValidationError("Solo se permiten un nodo de asignación  y un nodo de notificación")

        if flow_id:
            if flow_type == cls.FlowType.FILING:
                FilingNode.objects.filter(filing_flow__id=flow_id).delete()
                FilingAreaUser.objects.filter(filing_flow_id=flow_id).delete()
            else:
                SignatureNode.objects.filter(signature_flow__id=flow_id).delete()
                SignatureAreaUser.objects.filter(signature_flow_id=flow_id).delete()
        else:
            sf.save()

        if flow_type == cls.FlowType.FILING:
            node_list = FilingNode.objects.bulk_create(node_list)
        else:
            for n in node_list:
                if n.area_user is not None:
                    print('n.area_user--', n.area_user)
                    n.area_user.save()
            node_list = SignatureNode.objects.bulk_create(node_list)

        for n in node_list:
            nodes[n.index] = n
        
        for key, n in nodes.items():
            if graph['nodes'][str(key)]['inputs']:
                previous = [nodes[c['node']] for c in graph['nodes'][str(key)]['inputs']['in']['connections']]
                n.previous.set(previous)

        if flow_type == cls.FlowType.FILING:
            for i, n in enumerate(node_list):
                if user_list[i]:
                    for u in user_list[i]:
                        u.filing_flow_id = sf.id
                    if (user_list[i]):
                        n.area_users.set(FilingAreaUser.objects.bulk_create(user_list[i]))
        
        return sf
