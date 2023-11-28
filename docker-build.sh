rm -Rf ./docker_output
mkdir -p ./docker_output
sudo chmod 777 -R ./docker_output
echo "building linux amd64"
sudo docker build . -t ps3gud-linux-amd64 -f dockerfiles/build-linux-amd64.dockerfile
sudo docker run -it --rm -v ${PWD}/docker_output:/code/docker_output ps3gud-linux-amd64
echo "building windows amd64"
sudo docker build . -t ps3gud-linux-win64 -f dockerfiles/build-linux-win64.dockerfile
sudo docker run -it --rm -v ${PWD}/docker_output:/code/docker_output ps3gud-linux-win64
echo "building windows i386"
sudo docker build . -t ps3gud-linux-win32 -f dockerfiles/build-linux-win32.dockerfile
sudo docker run -it --rm -v ${PWD}/docker_output:/code/docker_output ps3gud-linux-win32
#fix up permisions
sudo chown -hR $(whoami) ./docker_output
