FROM ubuntu:latest

# Set the workdir to be root
WORKDIR /

USER root

RUN apt-get update && apt-get install ca-certificates -y && update-ca-certificates

COPY --from=1password/connect-api:latest /bin/connect-api /usr/local/bin/connect-api

USER root

COPY entrypoint.sh /usr/local/bin
RUN chmod -R a+rwx /usr/local/bin

ENV APP_ROOT=/home/opuser
ENV PATH=/usr/local/bin:${PATH} HOME=${APP_ROOT}

RUN mkdir -p ${APP_ROOT}/.op && \
    mkdir -p ${APP_ROOT}/.op/data && \
    chmod -R g=u ${APP_ROOT} /etc/passwd

# Important - Reset to the base image's user account.
USER 10001

# Set the default CMD.
CMD ["entrypoint.sh"]
