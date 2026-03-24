#!/bin/bash
cd /Users/francoisrostaing/Documents/CODE/LBO/lbo-engine
git add .
git commit -m "${1:-auto: update}"
git push
