#!/bin/bash
PROJECT_HOME=/home/ec2-user/heliumgas/flask
rm -rf "$PROJECT_HOME"/*
rm -rf "$PROJECT_HOME"/.[^.]* "$PROJECT_HOME"/..?*
