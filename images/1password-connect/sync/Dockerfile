FROM ubuntu:latest

# Set the workdir to be root
WORKDIR /

USER root

RUN apt-get update && apt-get install ca-certificates -y && update-ca-certificates

COPY --from=1password/connect-sync:latest /bin/connect-sync /usr/local/bin/connect-sync

USER root

COPY entrypoint-sync.sh /usr/local/bin
RUN chmod -R a+rwx /usr/local/bin

# Important - Reset to the base image's user account.
USER 10001

# Set the default CMD.
CMD ["entrypoint-sync.sh"]
