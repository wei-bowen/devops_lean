#!/usr/bin/env python
# encoding: utf-8

import argparse

def _argparse():
    parser = argparse.ArgumentParser(description = 'Python-MySQL-client')
    parser.add_argument('--host',action='store',dest='host',required=True,help='connect_to _host')
    parser.add_argument('-u','--user',action='store',dest='user',required=True,help='')
    parser.add_argument('-p','--password',action='store',dest='password',required=True,help='passwordtouserconnectingtoserver')
    parser.add_argument('-P','--port',action='store',dest='port',default=3306,type=int,help='portnumbertoconnect')
    parser.add_argument('-v','--version',action='version',version='%(prog)s0.1')
    return parser.parse_args()

if __name__=='__main__':
    parser = _argparse()
    conn_args = dict(host=parser.host,user=parser.user,paspassword=parser.password,port=parser.port)
    print(conn_args)
