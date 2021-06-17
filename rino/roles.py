from rolepermissions.roles import AbstractUserRole

class ContactUs(AbstractUserRole):
    available_permissions = {
        'edition': True,
        'query': True,
        'answer': True,
        'assign_in_group': True,
        'receive_in_group': True,
        'assign_to_anyone': True,
        'receive_from_anyone': True,
        'assign_in_dependency': True,
        'receive_in_dependency_or_group': True,
        'report': True,
        'delete_reported': True,
        'modify_classification': True
    }

class BossUser(AbstractUserRole):
    available_permissions = {
        'edition': True,
        'query': True,
        'answer': True,
        'assign_in_group': True,
        'receive_in_group': True,
        'assign_to_anyone': True,
        'receive_from_anyone': True,
        'assign_in_dependency': True,
        'receive_in_dependency_or_group': True,
        'report': True,
        'delete_reported': True,
        'modify_classification': False
    }

class DistributionChannelUser(AbstractUserRole):
    available_permissions = {
        'edition': True,
        'query': True,
        'answer': True,
        'assign_in_group': True,
        'receive_in_group': True,
        'assign_to_anyone': True,
        'receive_from_anyone': True,
        'assign_in_dependency': True,
        'receive_in_dependency_or_group': True,
        'report': True,
        'delete_reported': True,
        'modify_classification': False
    }

class NormalUser(AbstractUserRole):
    available_permissions = {
        'edition': True,
        'query': True,
        'answer': True,
        'assign_in_group': True,
        'receive_in_group': True,
        'assign_to_anyone': False,
        'receive_from_anyone': True,
        'assign_in_dependency': False,
        'receive_in_dependency_or_group': False,
        'report': True,
        'delete_reported': True,
        'modify_classification': False
    }