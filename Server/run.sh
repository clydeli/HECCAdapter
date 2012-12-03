#!/bin/bash

mkdir config > /dev/null 2>&1
chmod 775 config
mkdir done > /dev/null 2>&1
mkdir job_queue > /dev/null 2>&1
chmod 775 job_queue
mkdir results > /dev/null 2>&1
mkdir running > /dev/null 2>&1

./scheduler.py /home/hecc/job_queue /home/hecc/config /home/hecc/running /home/hecc/done /home/hecc/results
