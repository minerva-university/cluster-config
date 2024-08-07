# cs* guests

## cs0
There is a 4TB SSD that has been partitioned into 2. The first partition is for a shared home directory. The second partition is for data. Let's mount them, and confirm that everything is ok:
```bash

mv /home /oldhome
mkdir /data
mkdir /home

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

If this all executes without issue, then you're done!

### NFS mounting home

On the nfs server, run the following:

```bash
apt install -y nfs-kernel-server 

cat <<EOF >> /etc/exports
/home    *(rw,sync,no_root_squash,no_subtree_check,insecure)
EOF
exportfs -a
```

## cs1
Make the disk availbe to the VM:
```bash
export VMID=102
qm set $VMID -scsi2 /dev/disk/by-id/wwn-0x5000c500eda1874e-part1

```

Mount /data
```bash
mkdir /data
cat <<EOF >> /etc/fstab
/dev/sdb /data ext4 defaults 0 2
EOF

mount -a
cd /data
ls -la

```
Make sure that /home is automounted
```bash
cat <<EOF >> /etc/hosts
192.168.86.21 minervaldap ldap ldap.minerva.local
192.168.86.31 cs0 cs0.minerva.local nfs nfs.minerva.local
192.168.86.48 cs2 cs2.minerva.local
EOF

apt install -y nfs-common autofs

cat <<EOF > /etc/auto.home
*   cs0.minerva.local:/home/&
EOF

cat <<EOF >> /etc/auto.master
/home   /etc/auto.home
EOF

mv /home /oldhome
mkdir /home

systemctl reload autofs
systemctl restart autofs

cd /home
ls -la
```
