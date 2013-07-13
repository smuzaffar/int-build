#!/bin/sh -ex

WORKDIR=/build/ge/git-stress-test
rm -rf $WORKDIR
mkdir -p $WORKDIR
cd $WORKDIR
time git clone https://:@git.cern.ch/kerberos/CMSSW.git
