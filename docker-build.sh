rm -Rf ./docker_output
mkdir -p ./docker_output
sudo chmod 777 -R ./docker_output
echo "building linux amd64"
sudo docker build . -t ps3gud-linux-amd64 -f dockerfiles/dockerfile-linux-amd64
sudo docker run -it --rm -v ${PWD}/docker_output:/code/docker_output ps3gud-linux-amd64
echo "building windows amd64"
sudo docker build . -t ps3gud-windows-amd64 -f dockerfiles/dockerfile-windows-amd64
sudo docker run -it --rm -v ${PWD}/docker_output:/code/docker_output ps3gud-windows-amd64
#fix up permisions
sudo chown -hR $(whoami) docker_output
