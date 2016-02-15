from string import Template
from event_source_client import EventSourceClient
from marathon import MarathonClient



def run(marathon, nginx, domain_map= None):
    urls = marathon.values()
    m_c = MarathonClient(urls)
    import ipdb
    ipdb.set_trace()
    conf_tpl = open(nginx['tpl'], "r")
    conf_tpl_string = conf_tpl.read()
    conf_tpl.close()
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
        if domain_map and domain_map.get('host'):
            host = domain_map.get('host')
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
    cl = EventSourceClient(urls[0]+"/v2/events", callback=callback_func)
    cl.poll()
