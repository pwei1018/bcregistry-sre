FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine

RUN apk update

RUN apk add --no-cache --upgrade bash zip unzip wget curl gnupg jq

RUN mkdir /app

WORKDIR /app

RUN curl -sS https://downloads.1password.com/linux/keys/1password.asc | gpg --import  &&\
    curl -O https://cache.agilebits.com/dist/1P/op2/pkg/v2.21.0/op_linux_386_v2.21.0.zip  &&\
    unzip op_linux_386_v2.21.0.zip && rm op_linux_386_v2.21.0.zip  &&\
    mv op /usr/local/bin/ &&\
    chmod +x /usr/local/bin/op  &&\
    op --version

RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq &&\
    chmod +x /usr/local/bin/yq  &&\
    yq --version

CMD ["bash"]