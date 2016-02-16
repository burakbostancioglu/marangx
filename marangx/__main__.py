import sys, getopt
from marangx import run
import jsoncfg
def main(argv):
    conf = {}
    try:
        opts, args = getopt.getopt(argv, "hc:", ["conf="])
    except getopt.GetoptError:
        print('missing params')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("--conf", '-c'):
            conf['conf'] = arg
    if not(conf.get('conf')):
        print('missing params')
        sys.exit(1)
    config = jsoncfg.load_config(conf['conf'])

    run(config.marathon, config.nginx, config.domain_map)

if __name__ == "__main__":
    main(sys.argv[1:])