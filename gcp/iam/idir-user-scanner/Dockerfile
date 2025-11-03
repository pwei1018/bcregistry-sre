FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:slim

COPY run.sh /run.sh

RUN sed -i 's/\r$//' /run.sh && \
    chmod +x /run.sh

ENTRYPOINT ["/bin/bash", "/run.sh"]
