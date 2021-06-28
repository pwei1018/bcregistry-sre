
FROM ubuntu:20.04

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"

ENV VCS_REF=${VCS_REF}
ENV BUILD_DATE=${BUILD_DATE}

LABEL org.label-schema.vcs-ref=${VCS_REF} \
    org.label-schema.build-date=${BUILD_DATE}

ARG OP_VERSION=1.10.3
ARG OC_VERSION=4.6

RUN apt-get update && apt-get install -y curl unzip jq && \
    curl -o 1password.zip https://cache.agilebits.com/dist/1P/op/pkg/v$OP_VERSION/op_linux_amd64_v$OP_VERSION.zip && \
    unzip 1password.zip -d /usr/local/bin && \
    rm 1password.zip

RUN curl -sLo /tmp/oc.tar.gz https://mirror.openshift.com/pub/openshift-v$(echo $OC_VERSION | cut -d'.' -f 1)/clients/oc/$OC_VERSION/linux/oc.tar.gz && \
    tar xzvf /tmp/oc.tar.gz -C /usr/local/bin/ && \
    rm -rf /tmp/oc.tar.gz

RUN apt-get install -y ca-certificates git

### Setup user for build execution and application runtime
ENV APP_ROOT=/opt/app-root
ENV PATH=/usr/local/bin:${APP_ROOT}/.local/bin:${PATH} HOME=${APP_ROOT}

RUN mkdir -p ${APP_ROOT} && \
    mkdir -p ${APP_ROOT}/scripts && \
    chmod -R u+x /usr/local/bin

COPY ./scripts/1pass.sh ${APP_ROOT}/scripts

RUN chmod -R u+x /usr/local/bin && \
    chmod -R u+x ${APP_ROOT}/scripts && \
    chgrp -R 0 ${APP_ROOT} && \
    chmod -R g=u ${APP_ROOT}

### Containers should NOT run as root as a good practice
USER 1001

WORKDIR ${APP_ROOT}

CMD ["bash"]

