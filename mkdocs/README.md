# The documentation
The documentation is built using mkDocs. This separate folder structure has been created to
provide a clean separation of the code and the documentation. However, that does mean that
you have to create symoblic links to the source code in the approprate folders.
Two scripts have been created to aide in the creation and maintenance of the documentation.
## mkDocsServe.sh
This script generates the documentation and serves it up using a local webserver.
It can be viewed by pointing a browser at http://localhost:8000/
## mkDocsBuild.sh
This scripts creates a website in the 'site' folder which can then be deployed to a web server.

