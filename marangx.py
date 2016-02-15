import logging
from string import Template
from event_source_client import EventSourceClient
from marathon import MarathonClient

log = logging.getLogger("eventsource.client")



m_c = MarathonClient('http://ec2-52-90-131-95.compute-1.amazonaws.com:8080')

conf_tpl = open("nginx.conf.tpl", "r")
conf_tpl_string = conf_tpl.read()
conf_tpl.close()
print(conf_tpl_string)
conf = Template(conf_tpl_string)

def prepare_upstreams(apps):
    upstreams_dict = {}
    for app in apps:
        nginx_sett = app.labels.get('nginx')
        if nginx_sett:
            upstream_name = app.labels.get('nginx_upstream')
            upstreams_dict[upstream_name] = []
            for task in app.tasks:
                upstreams_dict[upstream_name].append(get_server(task.host, task.ports[0]))
    compile_nginx_tmp(upstreams_dict)


def compile_nginx_tmp(upstreams_dict):
    upstream_string_dict = {}
    for upstreams in upstreams_dict:
        upstream_string_dict[upstreams] = '\n'.join(upstreams_dict[upstreams])
    conf_string = conf.safe_substitute(**upstream_string_dict)
    print(conf_string)

def get_server(host, port):
    return 'server {host}:{port}'.format(
        host=host,
        port=port
    )

def load_apps():
    apps = m_c.list_apps()
    for app in apps:
        app.tasks = m_c.list_tasks(app.id)
    prepare_upstreams(apps)

def callback_func(event):
    if event.name == 'deployment_success':
        load_apps()



cl = EventSourceClient('ec2-52-90-131-95.compute-1.amazonaws.com:8080',
                              action='v2',
                              target='events', callback=callback_func)


cl.poll()