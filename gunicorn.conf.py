"""Gunicorn config for Jobper production deployment."""

bind = "0.0.0.0:5001"
workers = 2
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
preload_app = True
