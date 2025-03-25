"""
from basyx.aas.adapter.resolver import *
if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8084, ResolverAPI(create_full_example()),
               use_debugger=True, use_reloader=True)

from basyx.aas.adapter.registry import *
if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8083, RegistryAPI(create_full_example()),
               use_debugger=True, use_reloader=True)


from basyx.aas.adapter.http import *
if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from basyx.aas.examples.data.example_aas import create_full_example

    run_simple("localhost", 8080, WSGIApp(create_full_example(), aasx.DictSupplementaryFileContainer()),
               use_debugger=True, use_reloader=True)
"""

import multiprocessing
from werkzeug.serving import run_simple
from basyx.aas.examples.data.example_aas import create_full_example
from basyx.aas.adapter.resolver import ResolverAPI
from basyx.aas.adapter.registry import RegistryAPI
from basyx.aas.adapter.http import *
import basyx.aas.adapter.aasx as aasx

def run_resolver_api():
    run_simple("localhost", 8084, ResolverAPI(create_full_example()),
               use_debugger=True,
               use_reloader=False)

def run_server_api():
    run_simple("localhost", 8080, WSGIApp(create_full_example(), aasx.DictSupplementaryFileContainer()),
               use_debugger=True,
               use_reloader=False)

def run_registry_api():
    run_simple("localhost", 8083, RegistryAPI(create_full_example()),
               use_debugger=True,
               use_reloader=False)

if __name__ == "__main__":
    resolver_process = multiprocessing.Process(target=run_resolver_api)
    registry_process = multiprocessing.Process(target=run_registry_api)
    server_process = multiprocessing.Process(target=run_server_api)

    # Starten der Prozesse
    resolver_process.start()
    registry_process.start()
    server_process.start()

    # Warten auf Prozesse
    resolver_process.join()
    registry_process.join()
    server_process.join()



