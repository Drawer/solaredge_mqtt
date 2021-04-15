ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

COPY run.sh /
COPY mqtt.py /
RUN apk add python3 \
	py3-pip \
    && pip3 install paho-mqtt requests \
	&& chmod a+x /run.sh

CMD [ "/run.sh" ]