ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

COPY run.sh /
COPY mqtt.py /
RUN apk add python3 \
	py3-pip \
<<<<<<< HEAD
    && pip3 install paho-mqtt requests \
=======
    && pip3 install paho-mqtt \
>>>>>>> 0eea89bfdfb0be16dc7955675f5893da363331d8
	&& chmod a+x /run.sh

CMD [ "/run.sh" ]