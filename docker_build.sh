echo "building linux amd64"
sudo docker build . -t ps3gud-linux-amd64 -f dockerfiles/dockerfile-linux-amd64
sudo docker run -it --rm -v ${PWD}/docker_output:/docker_output -u $(id -u) ps3gud-linux-amd64
#fix up permisions
sudo chown -hR $(whoami) docker_output
