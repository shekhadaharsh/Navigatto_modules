from celery import Celery

# Initialize Celery app
# Assuming Redis is running locally on default port 6379
redis_url = 'redis://127.0.0.1:6379/0'

celery_app = Celery(
    "maintenance_tasks",
    broker=redis_url,
    backend=redis_url,
    include=['maintenance_module.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
