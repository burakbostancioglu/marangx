import sys, getopt
from marangx import run
import staticconf
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
    config = staticconf.JSONConfiguration(conf['conf'])
    import ipdb
    ipdb.set_trace()
    run(**config)

if __name__ == "__main__":
    main(sys.argv[1:])