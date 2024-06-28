# Common actions for all machines:

Install useful packages:

```bash
apt install -y micro htop mosh qemu-guest-agent
```

Enable guest agent in the proxmox environment, and shutdown the machine, then start it up again:
```bash
systemctl enable qemu-guest-agent
systemctl status qemu-guest-agent
```
