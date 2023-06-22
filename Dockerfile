# syntax=docker/dockerfile:experimental
FROM quay.io/unstructured-io/base-images:rocky8.7-2 as base

RUN yum install -y make

ARG PIP_VERSION

# Set up environment
ENV HOME /home/
WORKDIR ${HOME}
RUN mkdir ${HOME}/.ssh && chmod go-rwx ${HOME}/.ssh \
  &&  ssh-keyscan -t rsa github.com >> /home/.ssh/known_hosts
ENV PYTHONPATH="${PYTHONPATH}:${HOME}"
ENV PATH="/home/usr/.local/bin:${PATH}"

FROM base as deps
# Copy and install Unstructured
COPY requirements requirements

RUN python3.8 -m pip install pip==${PIP_VERSION} && \
  dnf -y groupinstall "Development Tools" && \
  pip install --no-cache -r requirements/base.txt && \
  pip install --no-cache -r requirements/test.txt && \
  dnf -y groupremove "Development Tools" && \
  dnf clean all

FROM deps as code
COPY Makefile Makefile

CMD ["/bin/bash"]
