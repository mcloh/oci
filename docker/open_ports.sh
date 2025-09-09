#!/bin/bash

sudo iptables -I INPUT -p tcp --dport 5678 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 1880 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
