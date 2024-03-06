# install everything based on image "python:3.9"

FROM python:3.9
ENV DEBIAN_FRONTEND=noninteractive

#========== create the technical user "idp" with sudo-right  =======
RUN adduser idp --gecos ""
RUN usermod -aG sudo idp
WORKDIR /home/idp

#=========== copy some files from the host server =======
COPY manage.py .
COPY docker-entrypoint.sh .
COPY requirements.txt .
COPY wait-for-it.sh .

#======================== install tools ================================
RUN apt-get update && apt-get -y install graphviz libgraphviz-dev pkg-config wget libffi-dev libssl-dev curl vim tree python3-dev sudo 
RUN pip install -U setuptools
#RUN pip install pyopenssl ndg-httpsclient pyasn1 mysqlclient ptvsd pygraphviz pymysql djangorestframework   ### put into requirements.txt

#===================== install requirements ============================
RUN pip install -r requirements.txt

#=========== copy configured repository from host server =======
COPY idp3_async_api_djproj idp3_async_api_djproj
COPY api_app api_app
COPY idp_scripts idp_scripts
COPY idp3-3.7.1_LinuxBinaries/usr /usr

#============ create the log directory and set owner ===============
RUN mkdir /home/idp/logs 
WORKDIR /home/idp/
RUN chown -R idp:idp .
### the idp calculations will be started from this directory:
#WORKDIR /home/idp/idp_scripts
### set read + execute right for the idp-scripts:
RUN chmod 555 ./idp_scripts/*.idp

#====================== start the server ===============================
# EXPOSE port 3000 for debugging access from outside of the docker container,
# EXPOSE port 8000 for the web site
EXPOSE 3000 8000
#EXPOSE 8000
USER idp 
ENTRYPOINT ["./docker-entrypoint.sh"]
