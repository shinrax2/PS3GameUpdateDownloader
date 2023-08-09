echo "building amd64"
sudo docker build . -t ps3gud-amd64 -f dockerfile-amd64
sudo docker run -it --rm -v ${PWD}/docker_output:/dist -u $(id -u) ps3gud-amd64
#fix up permisions
sudo chown -hR $(whoami) docker_output
