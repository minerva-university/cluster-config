# OpenLDAP
This talks you through the installation and configuration of an LDAP server. 
This will allow us to authenticate users, and ensure that all user ids are consistent across the cluster.

## Initial confguration of the LDAP server
Run the following
```bash
apt update
apt upgrade
apt install -y apache2 php php-cgi libapache2-mod-php php-mbstring php-common php-pear slapd ldap-utils ldap-account-manager 

hostnamectl set-hostname ldap

cat <<EOF >> /etc/hosts
127.0.1.1 ldap.minerva.local ldap
EOF
cat /etc/hosts

dpkg-reconfigure slapd
```
Our root will be "minerva.local", or "dc=minerva,dc=local", depending on the needed format.


Now let's add some groups and users:
```bash
cat <<EOF >> /root/local_users.ldif
dn: ou=People,dc=minerva,dc=local
objectClass: organizationalUnit
ou: People

dn: ou=group,dc=minerva,dc=local
objectClass: organizationalUnit
ou: group

dn: cn=admin,ou=group,dc=minerva,dc=local
objectClass: posixGroup
gidNumber: 10000
cn: admin

dn: cn=students,ou=group,dc=minerva,dc=local
objectClass: posixGroup
gidNumber: 10001
cn: students

dn: cn=Philip Sterne,ou=People,dc=minerva,dc=local
objectClass: posixAccount
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
loginShell: /bin/bash
homeDirectory: /home/psterne
uid: psterne
cn: Philip Sterne
uidNumber: 10000
gidNumber: 10000
sn: Sterne
givenName: Philip

dn: cn=Perl Daniels,ou=People,dc=minerva,dc=local
objectClass: posixAccount
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
loginShell: /bin/bash
homeDirectory: /home/pdaniels
uid: pdaniels
cn: Perl Daniels
uidNumber: 10001
gidNumber: 10000
sn: Daniels
givenName: Perl
```

Check the status of the slapd service and import the LDIF file.
```bash
ldapadd -x -D cn=admin,dc=minerva,dc=local -W -f /root/local_users.ldif

systemctl status slapd
slapcat
```

This is also a good time to do a quick that everything works:
```bash
ldapsearch -x -H ldap:/// -b dc=minerva,dc=local
```

(Optional) Enable the firewall and check the status.
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 389
ufw allow 5432
ufw allow 3306
ufw deny out 25
ufw enable
ufw status verbose
```


## Configure the LDAP server to use SSL/TLS
This was a long set of steps which created our own CA, and then various keys which authenticate against it. 
In the end I ran it as one long script, and everything worked. 😅

```bash
apt install -y gnutls-bin ssl-cert
certtool --generate-privkey --bits 4096 --outfile /etc/ssl/private/mycakey.pem

cat <<EOF > /etc/ssl/ca.info
cn = Minerva
ca
cert_signing_key
expiration_days = 3650
EOF

certtool --generate-self-signed --load-privkey /etc/ssl/private/mycakey.pem --template /etc/ssl/ca.info --outfile /usr/local/share/ca-certificates/mycacert.crt
update-ca-certificates
certtool --generate-privkey --bits 2048 --outfile /etc/ldap/minervaldap_slapd_key.pem

cat <<EOF > /etc/ssl/minervaldap.info
organization = Minerva
cn = ldap.minerva.local
tls_www_server
encryption_key
signing_key
expiration_days = 3650
EOF

certtool --generate-certificate --load-privkey /etc/ldap/minervaldap_slapd_key.pem --load-ca-certificate /etc/ssl/certs/mycacert.pem --load-ca-privkey /etc/ssl/private/mycakey.pem --template /etc/ssl/minervaldap.info --outfile /etc/ldap/minervaldap_slapd_cert.pem 
sudo chgrp openldap /etc/ldap/minervaldap_slapd_key.pem 
sudo chmod 0640 /etc/ldap/minervaldap_slapd_key.pem 

cat <<EOF > /root/certinfo.ldif
dn: cn=config
add: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ssl/certs/mycacert.pem
-
add: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ldap/minervaldap_slapd_cert.pem
-
add: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ldap/minervaldap_slapd_key.pem
EOF

ldapmodify -Y EXTERNAL -H ldapi:/// -f /root/certinfo.ldif
```

## Updating LDAP from Google Spreadsheet
```bash
apt install python3.12-venv
mkdir /root/ldap_sync
cd /root/ldap_sync
wget https://raw.githubusercontent.com/minerva-university/cluster-config/main/ldap/requirements.txt
wget https://raw.githubusercontent.com/minerva-university/cluster-config/main/ldap/ldap_sync.py
wget https://raw.githubusercontent.com/minerva-university/cluster-config/main/ldap/ldap_sync.service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mv ldap_sync.service /etc/systemd/system/ldap_sync.service
```

Now create and edit the `/etc/ldap_sync/service.conf` file to contain the various sensitive bits of information.

Once that's done, then start everything up!

```bash
systemctl daemon-reload
systemctl enable ldap_sync
systemctl start ldap_sync
systemctl status ldap_sync
```

## LDAP clients

Make sure that the hosts file contains the ldap server (`ldap.minerva.local`):

```bash
cat /etc/hosts
```

Now run the following to install utilities:

```bash
apt install ldap-utils
cat <<EOF >> /etc/ldap/ldap.conf
BASE    dc=minerva,dc=local
URI     ldap://ldap.minerva.local
EOF
ldapsearch -x -H ldap://ldap.minerva.local -b "dc=minerva,dc=local"
```

Now we need to authenticate against LDAP. This requires us to add the certificate we created on the server:

```bash
wget https://raw.githubusercontent.com/minerva-university/cluster-config/main/mycacert.crt
mv mycacert.crt /usr/local/share/ca-certificates/
update-ca-certificates
```

Get sssd up and running:

```bash
apt install -y sssd-ldap ldap-utils sssd-tools

cat <<EOF > /etc/sssd/sssd.conf
[sssd]
config_file_version = 2
domains = minerva.local

[domain/minerva.local]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldap://ldap.minerva.local
cache_credentials = True
ldap_search_base = dc=minerva,dc=local
EOF

chmod 0600 /etc/sssd/sssd.conf
chown root:root /etc/sssd/sssd.conf
pam-auth-update --enable mkhomedir

systemctl start sssd
```
If you want to enable password ssh login, you need to add the following lines to `/etc/ssh/sshd_config`:

```bash
cat <<EOF > /etc/ssh/sshd_config.d/50-cloud-init.conf
PasswordAuthentication yes
AllowAgentForwarding yes
EOF
systemctl restart ssh
```

Now is a good time to confirm that you can do a normal LDAP search:

```bash
ldapwhoami -x -ZZ -H ldap://ldap.minerva.local
```

It is also a good time to check that you can log in as an LDAP user!
