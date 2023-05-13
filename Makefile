# vim: set noet ci pi sts=0 sw=4 ts=4 :
# http://www.gnu.org/software/make/manual/make.html
# http://linuxlib.ru/prog/make_379_manual.html
SHELL:=/bin/bash
DEBUG ?= 0

CURRENT_DIR := $(shell dirname "$(realpath "$(lastword $(MAKEFILE_LIST))")")
########################################################################
-include .env
export
########################################################################

INVENTORY_PATH ?= envs
DOTENV_DIST ?= .env.dist
ANSIBLE_VAULT_PASSWORD_FILE ?= ~/.ssh/.ansible-vault-token
########################################################################

all:  build

.PHONY: build
build:                       \
		.env-include         \
		requirements         \
		.python/bin/activate \
		$(ANSIBLE_VAULT_PASSWORD_FILE)

.env:
	@echo "Edit .env params" && \
	cat $(DOTENV_DIST)| \
		sed '/^\s*$$/d;/^\s*#/d'| \
		while read line; do \
			param=$${line%=*}; \
			def=$${line#*=}; \
			read -ei "$$def" -p "$$param:" val < /dev/tty; \
			echo $$param=$$val; \
		done > .env
	@$(MAKE) -s $(MAKEFLAGS) change-inventory

.PHONY: .env-update
.env-update: .env
	@diff \
		<(cat $(DOTENV_DIST) |grep '^[^#]'|awk -F= '{print $$1}'|sort) \
		<(cat .env         |grep '^[^#]'|awk -F= '{print $$1}'|sort) |\
		sed '/<\ /!d;s/^< //' |\
		while read line; do \
			line=$$(cat $(DOTENV_DIST)|grep "^$$line="); \
			param=$${line%=*}; \
			def=$${line#*=}; \
			[ -z "$def" ] && def=''; \
			read -ei "$$def" -p "$$param:" val < /dev/tty; \
			echo $$param=$$val; \
		done >> .env

.PHONY: .env-include
.env-include: .env-update
	$(eval INVENTORY_NAME := $(shell awk -F= '/INVENTORY_NAME/ {print $$2}' .env))
	@echo "INVENTORY_NAME=$(INVENTORY_NAME)" ;

.PHONY: change-inventory
change-inventory:
	export INVENTORY_NAMES="$$(ls -1 $(INVENTORY_PATH) | xargs -n 1 basename)" ; \
	if [ 1 -lt "$$(echo $$INVENTORY_NAMES | awk '{print NF; exit}')" ]; then      \
		select INVENTORY_NAME in $$INVENTORY_NAMES; do                            \
			export INVENTORY_NAME=$$INVENTORY_NAME ;                              \
			break ;                                                               \
		done ;                                                                    \
	else                                                                          \
		export INVENTORY_NAME=$$INVENTORY_NAMES ;                                 \
	fi ;                                                                          \
	sed s#INVENTORY_NAME=.*#INVENTORY_NAME=$$INVENTORY_NAME# -i .env;              \
	sed s#ANSIBLE_VAULT_PASSWORD_FILE=.*#ANSIBLE_VAULT_PASSWORD_FILE=$(ANSIBLE_VAULT_PASSWORD_FILE)# -i .env;

.python/bin/activate:
	python3 -m venv .python

.PHONY: requirements
requirements: \
		.python/bin/activate
	source .python/bin/activate && \
	pip3 install --upgrade pip && \
	pip3 install $$(cat ./requirements.txt*)

$(ANSIBLE_VAULT_PASSWORD_FILE):
	cat /dev/urandom |head|base64 -w0|tr -dc _A-Z-a-z-0-9|head -c 64 > $@
	chmod 600 $@
