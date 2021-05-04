FROM tobix/pywine:latest

RUN pip3 install flask mongoengine

RUN mkdir /run

COPY ./* /run

ENTRYPOINT ["python", "/run/commander.py"]
