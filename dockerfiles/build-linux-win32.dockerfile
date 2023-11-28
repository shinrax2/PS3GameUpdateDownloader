# setup
FROM tobix/pywine:3.12
ENV WINEARCH=win64
# python version to install
ENV PYVER=3.12.0
WORKDIR /code
VOLUME /code/docker_output
# installing depencies
RUN apt update -y && apt install wget xvfb git -y
# installing python
RUN wget -O /tmp/python-$PYVER.exe https://www.python.org/ftp/python/$PYVER/python-$PYVER.exe
RUN xvfb-run wine /tmp/python-$PYVER.exe /quiet InstallAllUsers=1 TargetDir=C:\\py32 Include_doc=0 Include_launcher=0 Include_test=0 PrependPath=1
# hack to bypass missing implementation of CopyFile2 in Wine(needed for python 3.12.0 and above)
RUN sed -i 's/"CopyFile2"/"CopyFile2_xx_invalid_disabled"/' /opt/wineprefix/drive_c/py32/Lib/shutil.py
# copying code
COPY . /code
# installing pip depencies
RUN wine C:\\py32\\python.exe -m pip install --disable-pip-version-check --no-cache-dir -U wheel pip
RUN wine C:\\py32\\python.exe -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt -r buildrequirements.txt
# build
CMD ["sh", "-c", "wine 'C://py32//python.exe' build.py --compiled --release --zip --docker --githash $(git rev-parse --short HEAD)"]
