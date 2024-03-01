from timeflux import timeflux
import sys

def run_timeflux(path_graph, path_config):

        # provide arguments
        sys.argv[1:] = ["-e", "CONFIG_PATH="+path_config, path_graph]

        # run timeflux
        timeflux.main()