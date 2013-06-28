#!/bin/sh
# DSVR (Domain Specific VPN Router)
# Copyright 2013 Darran Boyd
#
# Licensed under the "Attribution-NonCommercial-ShareAlike" Vizsage
# Public License (the "License"). You may not use this file except
# in compliance with the License. Roughly speaking, non-commercial
# users may share and modify this code, but must give credit and 
# share improvements. However, for proper details please 
# read the full License, available at
#     http://vizsage.com/license/Vizsage-License-BY-NC-SA.html 
# and the handy reference for understanding the full license at 
#     http://vizsage.com/license/Vizsage-Deed-BY-NC-SA.html
#
# Unless required by applicable law or agreed to in writing, any
# software distributed under the License is distributed on an 
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, 
# either express or implied. See the License for the specific 
# language governing permissions and limitations under the License.

if [ -z "$1" ]
  then
  echo "no table name supplied"
else
 ip rule | grep "lookup $1" | cut -d: -f1 >tmp.txt
 for line in `cat tmp.txt`;do 
   ip rule del prio $line
 done
 rm tmp.txt
fi
