# gunicorn.conf.py
bind = "0.0.0.0:62159"
#workers = 4
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 50
