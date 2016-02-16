from string import Template
from event_source_client import EventSourceClient
from marathon import MarathonClient
import json
import jsoncfg
from multiprocessing import Process

def run(marathon, nginx, domain_map= None):
    urls = []
    for url in marathon:
        urls.append(url.value)
    m_c = MarathonClient(urls)
    conf_tpl = open(nginx.tpl(), "r")
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
        p = Process(target=save_nginx_conf_and_restart_nginx, args=(nginx.conf(),
                                                                    conf_string,
                                                                    m_c,
                                                                    nginx.app()
                                                                    ))
        p.start()

    def get_server(host, port):
        if domain_map:
            try:
                host = domain_map[host].value
            except jsoncfg.config_classes.JSONConfigValueNotFoundError:
                pass
        return 'server {host}:{port};'.format(
            host=host,
            port=port
        )

    def load_apps():
        apps = m_c.list_apps()
        for app in apps:
            app.tasks = m_c.list_tasks(app.id)
        prepare_upstreams(apps)

    def callback_func(event):
        if event.name == 'status_update_event':
            data = event.data.split("\n")
            for datum in data:
                event_dict = json.loads(datum)
                if event_dict.get('eventType') and event_dict.get('eventType') == "status_update_event":
                    break

            if not(nginx.app() == event_dict['appId']):
                load_apps()

    cl = EventSourceClient(urls[0]+"/v2/events", callback=callback_func)
    cl.poll()

def save_nginx_conf_and_restart_nginx(conf_path, conf_string, marathon_client, nginx_app_name):
    try:
        file_ = open(conf_path, 'w')
        file_.write(conf_string)
        file_.close()
        print(marathon_client.restart_app(nginx_app_name, force=True))
    except:
        print("we couldn't save nginx conf.check permissions")
