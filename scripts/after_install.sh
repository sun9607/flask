#!/bin/bash
PROJECT_HOME=/home/ec2-user/heliumgas
VENV_PATH="$PROJECT_HOME"/venv_flask
UPLOAD_PATH="$PROJECT_HOME"/flask/uploads

python3 -m venv "$VENV_PATH"
source "$VENV_PATH"/bin/activate
pip install -r "$PROJECT_HOME"/flask/requirements.txt

if [ ! -L "$UPLOAD_PATH" ]; then
    ln -s /mnt/efs/fs1/uploads "$UPLOAD_PATH"
fi
