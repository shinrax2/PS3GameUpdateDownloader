# setup
FROM tobix/pywine:3.12
ENV WINEARCH=win64
WORKDIR /code
VOLUME /code/docker_output
# installing depencies
RUN apt update -y && apt install git -y
# copying code
COPY . /code
# installing pip depencies
RUN wine python -m pip install --disable-pip-version-check --no-cache-dir -U wheel pip
RUN wine python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt -r buildrequirements.txt
# build
CMD ["sh", "-c", "wine python build.py --compiled --release --zip --docker --githash $(git rev-parse --short HEAD)"]
