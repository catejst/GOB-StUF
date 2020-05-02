#!/bin/bash

source .env

LOCAL_API="http://localhost:8165"
RESULTS_DIR="./results"

get_data() {
  _ID=$1
  _API=$2

  BSN_PATH="brp/ingeschrevenpersonen/$BSN"
  CURL="curl -s -H MKS_APPLICATIE:${MKS_APPLICATIE} -H MKS_GEBRUIKER:${MKS_GEBRUIKER}"
  PRETTY_JSON="python -m json.tool --sort-keys"
  SKIP_OWN_REF="grep -v $BSN_PATH"
  $CURL "${_API}/${BSN_PATH}" | $PRETTY_JSON | $SKIP_OWN_REF > $RESULTS_DIR/$_ID/$BSN.out
}

compare_results() {
  _SIDE1=$1
  _SIDE2=$2

  diff $RESULTS_DIR/$_SIDE1/$BSN.out $RESULTS_DIR/$_SIDE2/$BSN.out
  if [ $? = 0 ]; then
    echo "$BSN OK"
  else
    echo "$BSN FAILED"
  fi
}

for BSN in $BSNS; do
  echo Check $BSN
  get_data local $LOCAL_API
  get_data acc $ACC_API
  compare_results local acc
done