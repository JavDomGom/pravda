FROM python:3.9.9-bullseye@sha256:45e88e32518da8b8c551443510c7859e49938ee4d416fced6fb87f5b0a238ac1

LABEL name="pravda" \
      license="GPLv3" \
      maintainer="Javier Domínguez Gómez"

ENV USER="pravda" \
    BASEDIR="/app"

RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg=7:4.3.3-0+deb11u1

ADD src ${BASEDIR}/src
ADD tests ${BASEDIR}/tests
ADD mp4 ${BASEDIR}/mp4
ADD srt ${BASEDIR}/srt

RUN groupadd -g 1000 ${USER} \
    && useradd -u 1000 -g 1000 ${USER} \
    && chown -R ${USER}:${USER} ${BASEDIR}

COPY requirements.txt requirements_test.txt /tmp/
COPY .coveragerc ${BASEDIR}/.coveragerc

RUN pip install --upgrade pip\
    && pip install -r /tmp/requirements.txt \
    && pip install -r /tmp/requirements_test.txt \
    && rm -f /tmp/requirements.txt /tmp/requirements_test.txt

USER ${USER}

WORKDIR ${BASEDIR}

CMD ["python"]
