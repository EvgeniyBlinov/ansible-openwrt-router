[![MIT License][license-image]][license-url]

# Ansible for simple openwrt router configuration (linux only)

## Install

```sh
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv

python3 -m venv .python &&
source .python/bin/activate &&
pip3 install --upgrade pip &&
pip3 install -r ./requirements.txt
```

## Configure

```sh
make
```

## Usage

```
## Create inventory config file
cp -r envs/local envs/myrouter
mkdir -p envs/myrouter
cat >  envs/myrouter/localhost.yml <<EOF
#  vim: set et fenc=utf-8 ff=unix sts=2 sw=2 ts=2 :
---
#############################  common  #################################
openwrt__router:
  id: myrouter
  ip: 192.168.1.1
  domain: myrouter.lo
  ssid: 'MY-NETWORK'
  pass: 'password'
#############################  common  #################################
openwrt__network_override:
  interface:
    lan:
      options:
        - ipaddr: 192.168.1.1
    wan:
      options:
        - reqopts: routes msstaticroutes
        - proto: dhcp
        - dns: 1.1.1.1
EOF

## Get origin configs
bin/run fetch-configs.yml

## Generate new configs
bin/run deploy.yml --skip-tags apply

## Diff configs
bin/diff
```

Deploy new configs

```
bin/run deploy.yml
```

Deploy with commit and without restart

```
bin/run deploy.yml -e "openwrt__apply__restart=no"
```


### @TODO

- add docker container for ansible
- openwrt: get configs from machine
- move openwrt to openwrt/config

## License

[![MIT License][license-image]][license-url]


[license-image]: http://img.shields.io/badge/license-MIT-blue.svg?style=flat
[license-url]: LICENSE
