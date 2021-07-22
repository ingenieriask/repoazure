from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from core.services import Scheduler
        Scheduler.start()

