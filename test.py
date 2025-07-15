
from server.app.interfaces.registry import *
if __name__ == "__main__":
     from werkzeug.serving import run_simple
     from basyx.aas.examples.data.example_aas import create_full_example

     run_simple("localhost", 8083, RegistryAPI(create_full_example()),
               use_debugger=True, use_reloader=True)

#from server.app.interfaces.discovery import *
#if __name__ == "__main__":
#   from werkzeug.serving import run_simple

 #  run_simple("localhost", 8084, DiscoveryAPI(InMemoryDiscoveryStore()),
 #             use_debugger=True, use_reloader=True)
# from server.app.interfaces.repository import *
# if __name__ == "__main__":
#     from werkzeug.serving import run_simple
#     from basyx.aas.examples.data.example_aas import create_full_example
#
#     run_simple("localhost", 8080, WSGIApp(create_full_example(), aasx.DictSupplementaryFileContainer()),
#                use_debugger=True, use_reloader=True)




