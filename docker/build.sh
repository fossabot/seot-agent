#!/bin/bash

cp ../seot/agent/dpp.py .
docker build -t keichi/seot-base .
rm dpp.py
