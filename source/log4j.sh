#!/bin/bash

# This script will find out all the points....

IMP_LOG4J="import org.apache.log4j.Logger"
SRC_ROOT="${HOME}/Downloads/apache-cloudstack-4.4.0-src"
GET_LOGGER="\S+\ *\=\ *Logger.getLogger"

function find_log_point {
    logger_name=`pcregrep -o "${GET_LOGGER}" ${1}`;
    if [ -n "$logger_name" ]; then
        pcregrep -HoMn "${logger_name%%\ *}\.[a-z]{4,5}\(.*\);" ${1};
    fi
}

function find_log_points {
    file_using_log4j=`grep -Erl "${IMP_LOG4J}" ${SRC_ROOT}`
    for file in ${file_using_log4j};
    do
        find_log_point ${file};
    done;
}

function main {
    find_log_points # | awk -f log4j.awk;
}

main;