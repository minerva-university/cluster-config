# Docker

## Installation docker (for all machines)

```bash
apt install apt-transport-https ca-certificates curl gnupg lsb-release -y

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update

apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl status docker
```

## Create a user to run docker

Go to LDAP Account Manager and log in:

- Create a new user called `docker_runner`
- Set the password to `docker_runner`

```bash
usermod -aG docker docker_runner
su - docker_runner
sudo docker run hello-world
```

## Create docker swarm

```bash
docker swarm init --advertise-addr 192.168.86.31
```

Then copy and paste the command to join the swarm on the other machines.

## Get traefic up and running

```bash
docker network create -d overlay general_overlay_network

git clone git@github.com:minerva-university/cluster-config.git
cd cluster-config/traefik-prometheus
docker stack deploy -c docker-compose.yml traefik
```
