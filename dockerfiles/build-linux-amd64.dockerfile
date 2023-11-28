# setup
FROM amd64/python:3.12-bookworm
WORKDIR /code
VOLUME /code/docker_output
# installing depencies
RUN apt update -y && apt install -y binutils git
# copying code
COPY . /code
# installing pip depencies
RUN pip install --disable-pip-version-check --no-cache-dir -U wheel pip
RUN pip install --disable-pip-version-check --no-cache-dir -r requirements.txt -r buildrequirements.txt
# build
CMD ["sh", "-c", "python build.py --compiled --release --zip --docker"]
