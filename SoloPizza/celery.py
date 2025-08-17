import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoloPizza.settings')

app = Celery('SoloPizza')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Set broker_connection_retry_on_startup to True to maintain existing retry behavior
app.conf.broker_connection_retry_on_startup = True

# Использование Django DB scheduler для хранения задач
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Настройка периодических задач при запуске Celery
    """
    # Импортируем функцию создания начальных задач
    from SoloPizza.celerybeat_schedule import create_initial_tasks
    
    # Создаем начальные задачи в базе данных
    create_initial_tasks()