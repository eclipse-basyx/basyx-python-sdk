from basyx.aas.backend.local_file import LocalFileObjectStore
from basyx.aas.adapter.http import WSGIApp

application = WSGIApp(LocalFileObjectStore("/storage"))
