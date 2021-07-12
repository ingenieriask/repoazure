from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import logging
import json
from enum import Enum
from workflow.models import SignatureFlow, SignatureNode

logger = logging.getLogger(__name__)

class SignatureFlowService(object):

    class Type(Enum):
        INPUT = 'Inicio'
        OUTPUT = 'Fin'
        GUARANTORUSER = 'Avalador'
        SIGNINGUSER = 'Firmante'

    @classmethod
    def to_json(cls, pk):
        end_node = SignatureNode.objects.filter(signature_flow__id=pk, type=cls.Type.OUTPUT.value).first()
        if end_node:
            formated_nodes = {}
            cls._format_node(end_node, formated_nodes)
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
    def _format_node(cls, node, formated_nodes, next_node=None):
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
            

            user = {
                'id': node.user.id,
                'username': node.user.username, 
                'first_name': node.user.first_name,
                'last_name': node.user.last_name,
            } if node.user else {}

            formated_node = {
                'id': node.index,
                'data': {
                    'user': user
                },
                'inputs': inputs,
                'outputs': outputs,
                **properties,
                'name': node.type
            }
            formated_nodes[node.index] = formated_node

            for previous_node in previous_nodes:
                cls._format_node(previous_node, formated_nodes, node.index)

        return 

    @classmethod
    def from_json(cls, graph, signature_flow_id=None):

        print('graph:', graph)

        nodes = {}
        node_list = []

        acc = {
            SignatureFlowService.Type.SIGNINGUSER.value: 0,
            SignatureFlowService.Type.GUARANTORUSER.value: 0,
            SignatureFlowService.Type.INPUT.value: 0,
            SignatureFlowService.Type.OUTPUT.value: 0
        }

        if signature_flow_id:
            sf = SignatureFlow(pk=int(signature_flow_id))
        else:
            sf = SignatureFlow(name='', description='')

        for key, n in graph['nodes'].items():
            properties = {'position': n['position']}
            user = None
            if n['name'] in [SignatureFlowService.Type.SIGNINGUSER.value,  
                            SignatureFlowService.Type.GUARANTORUSER.value]:
                if n['data'] and n['data']['user_id'] and n['data']['user_id'] != '-1':
                    user = User(int(n['data']['user_id']))
                else:
                    raise ValidationError("Debe seleccionar un usuario para cada estado")

            if n['name'] != SignatureFlowService.Type.INPUT.value:
                if not n['inputs']['in']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")

            if n['name'] != SignatureFlowService.Type.OUTPUT.value:  
                if not n['outputs']['out']['connections']:
                    raise ValidationError("Todas las entradas y salidas deben estar interconectadas")
                
            acc[n['name']] += 1
            node = SignatureNode(
                type=n['name'], 
                index=n['id'],
                user=user,
                properties=json.dumps(properties),
                signature_flow=sf)
            node_list.append(node)

        if acc[SignatureFlowService.Type.INPUT.value] > 1 or acc[SignatureFlowService.Type.OUTPUT.value] > 1:
            raise ValidationError("Solo se permiten un nodo de entrada y un nodo de salida")
        if acc[SignatureFlowService.Type.INPUT.value] == 0 or acc[SignatureFlowService.Type.OUTPUT.value] == 0:
            raise ValidationError("Se requiere un nodo de entrada y un nodo de salida")

        if signature_flow_id:
            SignatureNode.objects.filter(signature_flow__id=signature_flow_id).delete()
        else:
            sf.save()
        node_list = SignatureNode.objects.bulk_create(node_list)

        for n in node_list:
            nodes[n.index] = n
        
        for key, n in nodes.items():
            if graph['nodes'][str(key)]['inputs']:
                previous = [nodes[c['node']] for c in graph['nodes'][str(key)]['inputs']['in']['connections']]
                n.previous.set(previous)
        return sf

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
