# add arguments when running commands, e.g. make upload_config REMOTE="user@host" KEY="~/.ssh/your_key"
REMOTE :=
KEY :=
PY := python3.12
PROJECT_DIR := src/crypto_telegram_bot
PROJECT_NAME := tgbot
ENV_DIR := .venv
ENV := ./$(ENV_DIR)/bin/$(PY)
PIP := ./$(ENV_DIR)/bin/pip
RUFF := ./$(ENV_DIR)/bin/ruff
ISORT := ./$(ENV_DIR)/bin/isort
LOCAL := ~/Projects/$(PROJECT_NAME)
CFG_FILE := config.json

install:
	${PY} -m venv ${ENV_DIR};
	${PIP} install --upgrade pip;
	${PIP} install  .

install_dev:
	${PY} -m venv ${ENV_DIR};
	${PIP} install --upgrade pip;
	${PIP} install -e '.[dev]'

lint:
	${RUFF} format ${PROJECT_DIR}/*.py && ${ISORT} ${PROJECT_DIR}/*.py

clean:
	rm -rf ${ENV_DIR}

# REMOTE COMMANDS ----------------------------------------------------------------------
get_config:
	scp -i ${KEY} ${REMOTE}:~/${PROJECT_NAME}/${CFG_FILE} ${LOCAL}/${CFG_FILE}

get_log:
	scp -i ${KEY} ${REMOTE}:~/${PROJECT_NAME}/${PROJECT_NAME}.log ${LOCAL}

update_config:
	scp -i ${KEY} ${LOCAL}/${CFG_FILE} ${REMOTE}:~/${PROJECT_NAME}/${CFG_FILE}

update_remote:
	ssh -i ${KEY} ${REMOTE} "cd ~/${PROJECT_NAME} && git pull && systemctl --user restart ${PROJECT_NAME}.service"
