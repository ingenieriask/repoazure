from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import logging
import json
from enum import Enum
from workflow.models import SignatureFlow, SignatureNode, FilingFlow, FilingNode

logger = logging.getLogger(__name__)

class FlowService(object):

    class FlowType(Enum):
        FILING = 'Filing'
        SIGNATURE = 'Signature'
         
    class NodeType(Enum):
        INPUT = 'Inicio'
        OUTPUT = 'Fin'
        GUARANTORUSER = 'Visto Bueno'
        SIGNINGUSER = 'Firma Personal'
        LEGALSIGNINGUSER = 'Firma Jurídica'
        ASSIGNEDUSER = 'Asignar'
        INFORMEDUSER = 'Notificar'

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
            end_node = SignatureNode.objects.filter(signature_flow__id=pk, type=cls.NodeType.OUTPUT.value).first()
        else:
            end_node = FilingNode.objects.filter(filing_flow__id=pk, type=cls.NodeType.OUTPUT.value).first()

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
                for user in node.users.all():
                    users.append(
                        {
                            'id': user.id,
                            'username': user.username, 
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                        }
                    )
            else:
                user = {
                    'id': node.user.id,
                    'username': node.user.username, 
                    'first_name': node.user.first_name,
                    'last_name': node.user.last_name,
                } if node.user else {}            

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
            FlowService.NodeType.SIGNINGUSER.value: 0,
            FlowService.NodeType.LEGALSIGNINGUSER.value: 0,
            FlowService.NodeType.GUARANTORUSER.value: 0,
            FlowService.NodeType.ASSIGNEDUSER.value: 0,
            FlowService.NodeType.INFORMEDUSER.value: 0,
            FlowService.NodeType.INPUT.value: 0,
            FlowService.NodeType.OUTPUT.value: 0
        }

        if flow_id:
            sf = FilingFlow(pk=int(flow_id)) if flow_type == cls.FlowType.FILING else SignatureFlow(pk=int(flow_id)) 
        else:
            sf = FilingFlow() if flow_type == cls.FlowType.FILING else SignatureFlow(name='', description='')

        for key, n in graph['nodes'].items():
            properties = {'position': n['position']}
            time = 2

            if n['name'] != FlowService.NodeType.INPUT.value:
                if not n['inputs']['in']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")

            if n['name'] != FlowService.NodeType.OUTPUT.value:  
                if not n['outputs']['out']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")
                                
            acc[n['name']] += 1

            if flow_type == cls.FlowType.FILING:
                users = []
                if n['name'] in [FlowService.NodeType.ASSIGNEDUSER.value,  
                                FlowService.NodeType.INFORMEDUSER.value]:
                    if n['data'] and n['data']['users']:
                        for user_id in n['data']['users']:
                            user = User.objects.get(pk=int(user_id['id']))
                            users.append(user)
                        n['data']['users'] = [{
                            'id': user.id,
                            'username': user.username, 
                            'first_name': user.first_name,
                            'last_name': user.last_name,
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
                if n['name'] in [FlowService.NodeType.SIGNINGUSER.value,  
                            FlowService.NodeType.GUARANTORUSER.value,
                            FlowService.NodeType.LEGALSIGNINGUSER.value]:
                    if n['data'] and n['data']['user']['id'] and n['data']['user']['id'] != '-1':
                        user = User.objects.get(pk=int(n['data']['user']['id']))
                        n['data']['user'] = {
                            'id': user.id,
                            'username': user.username, 
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                        }
                        time = n['data']['time']
                    else:
                        raise ValidationError("Debe seleccionar un usuario para cada estado")

                node = SignatureNode(
                    type=n['name'], 
                    index=n['id'],
                    user=user,
                    properties=json.dumps(properties),
                    signature_flow=sf,
                    time=time)

            node_list.append(node)

        if acc[FlowService.NodeType.INPUT.value] > 1 or acc[FlowService.NodeType.OUTPUT.value] > 1:
            raise ValidationError("Solo se permiten un nodo de entrada y un nodo de salida")
        if acc[FlowService.NodeType.INPUT.value] == 0 or acc[FlowService.NodeType.OUTPUT.value] == 0:
            raise ValidationError("Se requiere un nodo de entrada y un nodo de salida")

        if flow_id:
            if flow_type == cls.FlowType.FILING:
                FilingNode.objects.filter(filing_flow__id=flow_id).delete()
            else:
                SignatureNode.objects.filter(signature_flow__id=flow_id).delete()
        else:
            sf.save()

        if flow_type == cls.FlowType.FILING:
            node_list = FilingNode.objects.bulk_create(node_list)
        else:
            node_list = SignatureNode.objects.bulk_create(node_list)

        print('user_list:', user_list)

        if flow_type == cls.FlowType.FILING:
            for i, n in enumerate(node_list):
                if user_list[i]:
                    n.users.add(*user_list[i])

        for n in node_list:
            nodes[n.index] = n
        
        for key, n in nodes.items():
            if graph['nodes'][str(key)]['inputs']:
                previous = [nodes[c['node']] for c in graph['nodes'][str(key)]['inputs']['in']['connections']]
                n.previous.set(previous)
        return sf
