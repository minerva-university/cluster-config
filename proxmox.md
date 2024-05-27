# Proxmox hosts


## Configuring proxmox0
proxmox0 is a beefier machine, and will run most of the cluster wide services. It also runs some personal services (eg. home assistant, convenient computer for printing/scanning).

First let's run the post-install scripts (make sure to keep cluster services **enabled**):
```bash
bash -c "$(wget -qLO - https://github.com/tteck/Proxmox/raw/main/misc/post-pve-install.sh)"
```

There is a 4TB SSD that has been partitioned into 2. The first partition is for a shared home directory. The second partition is for data. Let's mount them, and confirm that everything is ok:
```bash
mkdir /data

cat <<EOF >> /etc/fstab
/dev/sda1 /home ext4 defaults 0 2
/dev/sda2 /data ext4 defaults 0 2
EOF

mount -a
cd /home
ls -la
cd /data
ls -la
```
If everything looks ok, go ahead and make the changes permanent. After which we can add a user and a desktop. (This allows me dual use of the machine.)
```bash
systemctl daemon-reload

adduser philip
usermod -aG sudo philip
groups philip

apt update
apt install sudo
apt install gnome chromium cups
systemctl start gdm3
```
Configure a media server:
```
bash -c "$(wget -qLO - https://github.com/tteck/Proxmox/raw/main/ct/plex.sh)"
```
Now you need to manually work through the options. Choose defaults for everrything, **except** that you want a **privileged container**, and allow root ssh. This allows us to easily run the following:
```
cat <<EOF >> /etc/hosts
192.168.86.42 minerva0
EOF

apt install -y nfs-common autofs

cat <<EOF > /etc/auto.home
*   minerva0:/home/&
EOF

cat <<EOF >> /etc/auto.master
/home   /etc/auto.home
EOF

systemctl reload autofs
systemctl restart autofs

```

Quickly grab an LXC image of the latest (headless) ubuntu server. This will form the basis of our LDAP server:
```
pveam update
pveam available
pveam download local ubuntu-24.04-standard_24.04-2_amd64.tar.zst
```



