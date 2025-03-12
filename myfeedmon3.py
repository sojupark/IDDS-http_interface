#-*-encoding:utf8-*-
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
#from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import forget
from pyramid.view import forbidden_view_config
from pyramid.view import view_config
#from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.response import FileResponse

#import HTMLParser
import logging
import logging.handlers
import os,sys,socket
sys.path.append("/home/infomax/svc/lib")
import mydbapi3 as mydbapi
import myutil3 as myutil
import json
import re
from decimal import *
import datetime
import websocket

from html.parser import HTMLParser



#reload(sys)
#sys.setdefaultencoding("euckr")

# set the log
logger = logging.getLogger('myfeedmon')
logger.setLevel(logging.INFO)
FMTER = logging.Formatter('%(asctime)s|%(message)s')
fileMaxByte = 1024 * 1024 * 110 #110MB
FH = logging.handlers.RotatingFileHandler(os.getcwd()+'/log/myfeedmon.log', maxBytes=fileMaxByte, backupCount=10)
#FH.setLevel(logging.INFO)
FH.setFormatter(FMTER)
logger.addHandler(FH)
#myPort=""
#myServ=""

#myPort="7789"
#myServ=socket.gethostbyname(socket.gethostname())+":"+myPort
#
#myServ="myfeed.einfomax.co.kr"
#myServ="https://"+myServ

mysys = myutil.MyMultiCast('mysys',isSend=True)

class LoggerWriter:
	def __init__(self, logger, level):
		self.logger = logger
		self.level = level

	def write(self, msg):
		if msg != '\n':
			self.logger.log(self.level, msg)



mydic = {"act_package_master":[1, "API패키지항목",["act_package","act_package_seq"]]
, "act_package_qry":[2,"API패키지",['act_package']]
, "client_info":[6,"고객정보",['client_name','c_name']]
, "file_spec":[3,"서비스파일 세부스펙",['c_name','c_file','sel_act_package_idx', 'c_seq']]
, "mycrontab":[4,"서비스파일 스케줄",['c_name','c_job_num']]
, "re_schedule":[5,"서비스파일 재스케줄",['myname']]
, "end_job_info":[7,"처리후 작업",['end_job']]
, "client_dns":[8,"고객사이트정보",['c_url','c_host']]
, "ws_status":[9,"URL서비스서버",['name']]
, "mgr_host":[10,"매니저호스트",['hostname']]
, "watchmember":[11,"감시자",['name','alias']]
, "watchgroup":[12,"감시그룹",['name']]
}
	
	
#@view_config(route_name='myhome', renderer='json', permission='view')
#def home_view(request):
#	return {
#		'page': 'home',
#        'userid': request.authenticated_userid,
#        'principals': request.effective_principals,
#        'context_type': str(type(request.context)),
#	}


@forbidden_view_config()
def forbidden_view(request):
	if request.authenticated_userid is None:
		response = HTTPUnauthorized()
		response.headers.update(forget(request))
	else:
		response = HTTPForbidden()
	return response


def getUserInfo():
	userset = {}
	with mydbapi.Mydb("mysql", "myfeed", _myHost="ftp2", _myPort=3306, _myUser='myfeed') as mycon:
		for items in mycon.exeQry("G", "select * from myfeed.user_info", useDict=True):
			userset[items['id']] = items
	

	return userset

def check_credentials(username, password, request):
	userset = getUserInfo()
	if username in userset and userset[username]['passwd'] == password:
		return []


class Root:
	# dead simple, give everyone who is logged in any permission
	# (see the home_view for an example permission)
	 __acl__ = ((Allow, Authenticated, ALL_PERMISSIONS),)



def hello_world(request):
	userset = getUserInfo()
	logger.info("{},{}".format(request.client_addr, request.authenticated_userid))
	myReq = {}
	myReq = dict(request.GET)

	if len(myReq) == 0:
		#myReq['mysel'] = 'client_info'
		myReq['mysel'] = 'login'



	myHtml = """
<!DOCTYPE html>
<meta charset="UTF-8">
<html>
<title>인포맥스구독시스템IDSS(Infomax Data Subscription System)</title>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/x-icon" href="/tab/static/favicon.ico">
<link rel="stylesheet" type="text/css" href="/tab/css/myfeed.css?ver={myName}">
</head>
<body>

<script type="text/javascript" src="/tab/js/myfeed.js?ver={myName}"></script>
<div id="myh">
<div id="myhead">
	login : {myuser_id}({myuser_name})
</div>
<div class="mytab">""".format(myuser_id=request.authenticated_userid, myuser_name=userset[request.authenticated_userid]['name'], myName=myName)

	for mykey in sorted(mydic, key=lambda k:mydic[k][0]):
		myval = mydic[mykey][1]	
		#myHtml += """<button class="tablinks" onclick="openJob(event, '{0}')">{1}</button>""".format(mykey, myval)
		username = request.authenticated_userid
		if userset[username]['role1'] == 'G' and (userset[username]['role2'] == 'G' or userset[username]['role2'] == 'api'):
			if mykey == 'act_package_master':
				pass
			else:
				continue

		#if mykey == "client_info": # default
		if mykey == "act_package_master": # default
			myHtml += """<button class="tablinks active" onclick="setURL(event, '{0}', '{1}', '{2}')">{1}</button>\n""".format(mykey, myval, myServ)
		else:
			myHtml += """<button class="tablinks" onclick="setURL(event, '{0}', '{1}', '{2}')">{1}</button>\n""".format(mykey, myval, myServ)
	myHtml += """
	</div>
</div>
	<div id="myselbody">
		<iframe id='mysel' src='{myServ}/tab/act_package_master'/>
	</div>
    </body>
    </html>""".format(myServ=myServ)
	return Response(myHtml)


def wanttabprc(request):
	userset = getUserInfo()
	logger.info("wanttabprc, {}-{}-{}".format(request.client_addr, request.authenticated_userid, request.matchdict['name']))
	tabnm = request.matchdict['name']

	username = request.authenticated_userid
	if userset[username]['role1'] == 'G' and (userset[username]['role2'] == 'G' or userset[username]['role2'] == 'api'):
		tabnm = 'act_package_master'

	myHtml = ""
	mySearchStr = ""	

	try:
		mycmd = tabnm

		myReq = None
		if request.method == 'GET':
			myReq = dict(request.GET)
		else:	
			myReq = dict(request.POST)


		if mycmd == 'goExe': # never call
				print("here")
				print(myReq)
				tabnm = myReq['tabnm'] # real tabnm

				myCmd = "ssh "+myReq['mgr_host']+"-j "+myReq['c_name']+" "+myReq['c_job_num']
				logger.info("{}-".format(myReq))

		else:
			with mydbapi.Mydb("mysql", "myfeed", _myHost="ftp2", _myPort=3306, _myUser='myfeed') as mycon:
				# insert or update
				myerror = ""
				mycmddic = {'myinsert':'I', 'mydel':'D'}

				if mycmd == 'myinsert' or mycmd == 'mydel':
					tabnm = myReq['tabnm'] # real tabnm
					if len(myReq) == 0:
						pass
					else:
						mySearchStr = myReq['mysearchstr'] # search String

						del myReq['tabnm']
						del myReq['mysearchstr']

						myOriURL = {}
						print("----------->tabnm", tabnm)
						try:
							#for key,val in myReq.itertiems():
							#	tmpval = HTMLParser.HTMLParser().unescape(val)
							#	myReq[key] = tmpval
							myReq = {HTMLParser().unescape(k):HTMLParser().unescape(myReq[k]).replace("<br>", "\n").replace("\n\n", "\n") for k in myReq}

							isSTREAM = False
							myQuote = "'"
							if 'c_file' in myReq:
								if myReq['c_file'].find("'") != -1:
									myQuote = '"'

							if 'c_name' in myReq and 'c_file' in myReq:
								sql = """select * 
									from myfeed.client_info ci, myfeed.act_package_qry apq
									where ci.sel_act_packages like concat('%', apq.act_package, '%')
									and apq.dbms in('stream','rio')
									and ci.c_name = '{c_name}' and ci.c_file = {myQuote}{c_file}{myQuote}""".format(c_name=myReq['c_name'], c_file=myReq['c_file'], myQuote=myQuote)
								items = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
								if items is not None and len(items) > 0:
									isSTREAM = True
							elif tabnm == 'act_package_master':
								isSTREAM = True
							elif tabnm == 'act_package_qry':
								if myReq['dbms'] in ['rio','stream']:
									isSTREAM = True
							elif tabnm == 'client_dns':
								isSTREAM = True
								

							print("next round!!!!!!!!!")
							if mycmddic[mycmd] == "D":
								for k,v in myReq.copy().items():
									if v == "None":
										del myReq[k]
								
								if tabnm == 'act_package_qry':
									mykey = myReq['act_package']
									myReq = {'act_package':mykey}

							#check mycrontab c_url list
							else:
								print("insert and update")
								if tabnm == 'mycrontab':
									myReq['c_url'] = myReq['c_url'].replace("\r","").replace("\n","").replace(" ", "")
									#if myReq['c_url'] != '':
									sql = """select distinct myc.job_status, ci.client_name, ci.sel_act_packages, ci.c_name, ci.c_file, myc.c_job_num, myc.c_url 
											, concat(ci.c_name, ci.c_file) as file_spec_name
											, myc.delimiter
                        								from myfeed.client_info ci, myfeed.act_package_qry apq, myfeed.mycrontab myc, myfeed.client_dns cdns, ws_status wss
                        								where ci.sel_act_packages like concat('%', apq.act_package, '%')
											and myc.c_name = '{c_name}' and myc.c_file = {myQuote}{c_file}{myQuote} and myc.c_job_num = {c_job_num}
											and myc.c_name = ci.c_name and ci.c_file = myc.c_file
                        								and myc.c_url like concat('%',cdns.c_url,'%') and wss.name = cdns.c_host""".format(myQuote=myQuote,c_name=myReq['c_name'], c_file=myReq['c_file'], c_job_num=myReq['c_job_num'])
									items = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
									if items is not None:
										items['c_url'] = items['c_url'].replace("\r","").replace("\n","").replace(" ", "")
										if items['c_url'] != '':
											myOriURL = {x.strip():False for x in items['c_url'].split(",")}
								elif tabnm == 'client_info':
									sql = """select * from myfeed.client_info where c_name = '{c_name}' and c_file = '{c_file}'""".format(c_name=myReq['c_name'], c_file=myReq['c_file'])
									items = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
									if items is not None:
										myOriURL = items
										
			
							if mycmddic[mycmd] == 'I':
								smsMsg = "{}-{}-{}-{}".format(request.client_addr, request.authenticated_userid, request.matchdict['name'], str(mycon.exeQry(mycmddic[mycmd], tabnm, myReq, useColFilter=True, IS_PRINT=True)[0]))
								#logger.info("{}-{}-{}-{}".format(request.client_addr, request.authenticated_userid, request.matchdict['name'], str(mycon.exeQry(mycmddic[mycmd], tabnm, myReq, useColFilter=True, IS_PRINT=True)[0])))

								logger.info("{}".format(smsMsg))
								myutil.sms("박상우", smsMsg)
							procTabnm = tabnm	

							print("isSTREAM-------->", isSTREAM)

							if isSTREAM or procTabnm == 'mycrontab':
								if procTabnm == 'act_package_qry':
									myDic = {"myJob":procTabnm, "myStat":mycmddic[mycmd]}

									myutil.rsleep(3,4)
									myDic.update(myReq)
									logger.info("send - {}".format(myDic))
									print("send - {}".format(myDic))
									mysys.send(json.dumps(myDic).encode("utf8"))

								elif procTabnm in ['client_dns','mycrontab','file_spec','client_info', 'act_package_master']:
									myDic = {"myJob":procTabnm, "myStat":mycmddic[mycmd]}
									if procTabnm == 'client_dns':
										if mycmddic[mycmd] == 'I':
											sql = """select
												case when cdns.c_proto = "REST_API_CLIENT" then 'restapi' else 'stream' end as type
												, cdns.*
												, wss.* 
												from client_dns cdns, ws_status wss
												where cdns.c_proto like '%_CLIENT'
												and cdns.c_host = wss.name
												and cdns.c_url = '{}'""".format(myReq['c_url'])
											print(sql)
											items = mycon.exeQry("G1", sql, useDict=True)
											print(items)
											myDic.update(items)
											# to system mc
											myutil.rsleep(3,4)
											mysys.send(json.dumps(myDic).encode("utf8"))

											# to websocket
											for items in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
												myurl = items[0]
												try:
													logger.info("{}".format(myurl))
													ws = websocket.create_connection(myurl)
													ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
													ws.close()
												except:
													logger.info("{}".format(myutil.getErrLine(sys)))


											# only change myToken of id,passwd of client_dns
											procTabnm = 'mycrontab'
											myDic = {"myJob":procTabnm, "myStat":mycmddic[mycmd]}
											#sql = """select * from mycrontab where c_url like '%{}%'""".format(myReq['c_url'])
											sql = """select myc.job_status, concat(cdns.c_id, '@', cdns.c_passwd, '@', myc.c_name,'@',myc.c_job_num,'@', cdns.c_host) as token
												, concat(ci.c_name, ci.c_file) as file_spec_name
												, concat(ci.c_name, '@', ci.c_file, '@', apq.act_package) as fsname
												, apq.act_package
												, case when myc.mgr_host = 'stream' then 'stream' else 'restapi' end as type
												, myc.delimiter, myc.use_cr_code
												, wss.ip, ci.client_name, ci.sel_act_packages, ci.c_name, ci.c_file, myc.c_job_num, cdns.c_url, cdns.c_proto, cdns.c_host, cdns.c_port, cdns.c_id, wss.url
                                                        	                                from myfeed.client_info ci, myfeed.act_package_qry apq, myfeed.mycrontab myc, myfeed.client_dns cdns, ws_status wss
                                                        	                                where ci.sel_act_packages like concat('%', apq.act_package, '%')
                                                        	                                and myc.c_name = ci.c_name and ci.c_file = myc.c_file
                                                        	                                and cdns.c_url = '{}'
                                                        	                                and myc.c_url like concat('%',cdns.c_url,'%') and wss.name = cdns.c_host""".format(myReq['c_url'])
											items = mycon.exeQry("G", sql, useDict=True)
											for item in items:
												myDic.update(item)
												myutil.rsleep(3,4)
												mysys.send(json.dumps(myDic).encode("utf8"))
												# to websocket
												for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
													myurl = sendWSL[0]
													try:
														logger.info("{}".format(myurl))
														ws = websocket.create_connection(myurl)
														ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
														ws.close()
													except:
														logger.info("{}".format(myutil.getErrLine(sys)))
										else:
											sql = """select ip
												from ws_status
												where name = '{}'""".format(myReq['c_host'])
											items = mycon.exeQry("G1", sql, useDict=True)
											myDic.update(myReq)
											myDic.update(items)
											print(myDic)
											logger.info("{}".format(myDic))
											# to websocket
											for items in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
												myurl = items[0]
												try:
													logger.info("{}".format(myurl))
													ws = websocket.create_connection(myurl)
													ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
													ws.close()
												except:
													logger.info("{}".format(myutil.getErrLine(sys)))


											# remove myToken of id,passwd of client_dns
											procTabnm = 'mycrontab'
											myDic = {"myJob":procTabnm, "myStat":mycmddic[mycmd]}
											#sql = """select * from mycrontab where c_url like '%{}%'""".format(myReq['c_url'])
											sql = """select myc.job_status, concat(cdns.c_id, '@', cdns.c_passwd, '@', myc.c_name,'@',myc.c_job_num,'@', cdns.c_host) as token
												, concat(ci.c_name, ci.c_file) as file_spec_name
												, concat(ci.c_name, '@', ci.c_file, '@', apq.act_package) as fsname
												, apq.act_package, myc.use_cr_code
												, case when myc.mgr_host = 'stream' then 'stream' else 'restapi' end as type
												, wss.ip, ci.client_name, ci.sel_act_packages, ci.c_name, ci.c_file, myc.c_job_num, myc.c_url, cdns.c_proto, cdns.c_host, cdns.c_port, cdns.c_id, wss.url
												, myc.delimiter
                                                        	                                from myfeed.client_info ci, myfeed.act_package_qry apq, myfeed.mycrontab myc, myfeed.client_dns cdns, ws_status wss
                                                        	                                where ci.sel_act_packages like concat('%', apq.act_package, '%')
                                                        	                                and myc.c_name = ci.c_name and ci.c_file = myc.c_file
                                                        	                                and cdns.c_url = '{}'
                                                        	                                and myc.c_url like concat('%',cdns.c_url,'%') and wss.name = cdns.c_host""".format(myReq['c_url'])
											items = mycon.exeQry("G", sql, useDict=True)
											for item in items:
												myDic.update(item)
												# to websocket
												for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
													myurl = sendWSL[0]
													try:
														logger.info("{}".format(myurl))
														ws = websocket.create_connection(myurl)
														ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
														ws.close()
													except:
														logger.info("{}".format(myutil.getErrLine(sys)))
									elif procTabnm == 'mycrontab':
										if mycmddic[mycmd] == 'I' and myReq['job_status'] != 'STOP':

											sql = """select distinct myc.job_status, ci.client_name, ci.sel_act_packages, ci.c_name, ci.c_file, myc.c_job_num, myc.c_url 
												, concat(ci.c_name, ci.c_file) as file_spec_name
												, concat(ci.c_name, '@', ci.c_file, '@', apq.act_package) as fsname
												, apq.act_package
												, myc.mgr_host 
												, myc.delimiter, myc.use_cr_code
                        									from myfeed.client_info ci, myfeed.act_package_qry apq, myfeed.mycrontab myc, myfeed.client_dns cdns, ws_status wss
                        									where ci.sel_act_packages like concat('%', apq.act_package, '%')
												and myc.c_name = '{c_name}' and myc.c_file = {myQuote}{c_file}{myQuote} and myc.c_job_num = {c_job_num}
												and myc.c_name = ci.c_name and ci.c_file = myc.c_file
                        									and myc.c_url like concat('%',cdns.c_url,'%') and wss.name = cdns.c_host""".format(myQuote=myQuote, c_name=myReq['c_name'], c_file=myReq['c_file'], c_job_num=myReq['c_job_num'])
											items = mycon.exeQry("G", sql, IS_PRINT=True, useDict=True)
													
											for item in items:
												for myURL in item['c_url'].split(","):
													subItems = item.copy()

													sql = """select * 
														, case when cdns.c_proto = "REST_API_CLIENT" then 'restapi' else 'stream' end as type
														from client_dns cdns, ws_status wss
														where cdns.c_proto like '%_CLIENT'
														and cdns.c_host = wss.name
														and cdns.c_url = '{}'""".format(myURL)
													items2 = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
													if items2 is not None:
														subItems['c_job_num'] = str(subItems['c_job_num'])
														subItems.update(items2)
														myToken = '@'.join([subItems['c_id'],subItems['c_passwd'],subItems['c_name'], subItems['c_job_num'],subItems['c_host']])
														subItems['token'] = myToken.strip()
														subItems['c_url'] = myURL.strip()
														if subItems['mgr_host'] != 'stream':
															subItems['type'] = 'restapi'
														myDic.update(subItems)
														myutil.rsleep(3,4)
														mysys.send(json.dumps(myDic).encode("utf8"))
														#sendData = json.dumps({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic})
														#mysys.send(sendData.encode("utf8"))

														# to websocket
														for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
															myurl = sendWSL[0]
															try:
																logger.info("{}".format(myurl))
																ws = websocket.create_connection(myurl)
																ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
																ws.close()
															except:
																logger.info("{}".format(myutil.getErrLine(sys)))

														# check deletion
														if myURL in myOriURL:
															myOriURL[myURL] = True

											if len(items) == 0:
												for myURL in list(myOriURL.keys()):
													myOriURL[myURL] = False
												

											print(myOriURL)
											# check deletion
											myDic = {"myJob":procTabnm, "myStat":'D'}
											for k,v in myOriURL.items():
												if not v:
													sql = """select myc.job_status, ci.sel_act_packages, myc.c_name, myc.c_job_num, myc.c_file, concat( cdns.c_id, '@', cdns.c_passwd, '@', myc.c_name, '@', myc.c_job_num, '@', cdns.c_host) as token
														, apq.act_package
														, concat(myc.c_name, '@', myc.c_file, '@', apq.act_package) as fsname
														, case when myc.mgr_host = 'stream' then 'stream' else 'restapi' end as type
														, myc.delimiter, myc.use_cr_code
														, wss.*
														from mycrontab myc, client_info ci, client_dns cdns, ws_status wss, myfeed.act_package_qry apq
														where myc.c_job_num = {c_job_num} and myc.c_name = '{c_name}'
														and ci.c_name = myc.c_name
														and ci.c_file = myc.c_file
														and ci.sel_act_packages like concat('%', apq.act_package, '%')
														and wss.name = cdns.c_host
														and cdns.c_url = '{myURL}'""".format(c_name=myReq['c_name'], c_job_num=myReq['c_job_num'], myURL=k)
													itemss = mycon.exeQry("G", sql, IS_PRINT=True, useDict=True)
													for items in itemss:
														myDic = {"myJob":procTabnm, "myStat":'D'}
														myDic.update(items)
														myutil.rsleep(3,4)
														mysys.send(json.dumps(myDic).encode("utf8"))
														#sendData = json.dumps({"token":"infomax_sys_cmd@systemmgr",procTabnm:str(myDic)})
														#mysys.send(sendData.encode("utf8"))
														
														# to websocket
														for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
															myurl = sendWSL[0]
															try:
																logger.info("{}".format(myurl))
																ws = websocket.create_connection(myurl)
																ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
																ws.close()
															except:
																logger.info("{}".format(myutil.getErrLine(sys)))


												
										else:
											myDic = {"myJob":procTabnm, "myStat":'D'}


											sql = """select distinct myc.job_status, ci.client_name, ci.sel_act_packages, ci.c_name, ci.c_file, myc.c_job_num, myc.c_url 
												, concat(ci.c_name, ci.c_file) as file_spec_name
												, concat(ci.c_name, '@', ci.c_file, '@', apq.act_package) as fsname
												, apq.act_package
												, myc.mgr_host 
												, myc.delimiter, myc.use_cr_code
                        									from myfeed.client_info ci, myfeed.act_package_qry apq, myfeed.mycrontab myc, myfeed.client_dns cdns, ws_status wss
                        									where ci.sel_act_packages like concat('%', apq.act_package, '%')
												and myc.c_name = '{c_name}' and myc.c_file = {myQuote}{c_file}{myQuote} and myc.c_job_num = {c_job_num}
												and myc.c_name = ci.c_name and ci.c_file = myc.c_file
                        									and myc.c_url like concat('%',cdns.c_url,'%') and wss.name = cdns.c_host""".format(myQuote=myQuote, c_name=myReq['c_name'], c_file=myReq['c_file'], c_job_num=myReq['c_job_num'])
											items = mycon.exeQry("G", sql, IS_PRINT=True, useDict=True)
											for item in items:
												for myURL in item['c_url'].split(","):
													subItems = item.copy()

													sql = """select * 
														, case when cdns.c_proto = "REST_API_CLIENT" then 'restapi' else 'stream' end as type
														from client_dns cdns, ws_status wss
														where cdns.c_proto like '%_CLIENT'
														and cdns.c_host = wss.name
														and cdns.c_url = '{}'""".format(myURL)
													items2 = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
													if items2 is not None:
														subItems['c_job_num'] = str(subItems['c_job_num'])
														subItems.update(items2)
														myToken = '@'.join([subItems['c_id'],subItems['c_passwd'],subItems['c_name'], subItems['c_job_num'],subItems['c_host']])
														subItems['token'] = myToken.strip()
														subItems['c_url'] = myURL.strip()
														if subItems['mgr_host'] != 'stream':
															subItems['type'] = 'restapi'
														myDic.update(subItems)
														myutil.rsleep(3,4)

														mysys.send(json.dumps(myDic).encode("utf8"))
														#sendData = json.dumps({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic})
														#mysys.send(sendData.encode("utf8"))

														# to websocket
														for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
															myurl = sendWSL[0]
															try:
																logger.info("{}".format(myurl))
																ws = websocket.create_connection(myurl)
																ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:myDic}))
																ws.close()
															except:
																logger.info("{}".format(myutil.getErrLine(sys)))


											#myDic.update(myReq)
											## to websocket
											#for sendWSL in mycon.exeQry("G", "select url from ws_status where url like 'ws://%'"):
											#	myurl = sendWSL[0]
											#	try:
											#		logger.info("{}".format(myurl))
											#		ws = websocket.create_connection(myurl)
											#		ws.send(str({"token":"infomax_sys_cmd@systemmgr",procTabnm:str(myDic)}))
											#		ws.close()
											#	except:
											#		logger.info("{}".format(myutil.getErrLine(sys)))


											#sql = """select myc.job_status, ci.sel_act_packages, myc.c_name, myc.c_job_num, myc.c_file, concat( cdns.c_id, '@', cdns.c_passwd, '@', myc.c_name, '@', myc.c_job_num, '@', cdns.c_host) as token
                                                                                        #                        , apq.act_package
                                                                                        #                        , concat(myc.c_name, '@', myc.c_file, '@', apq.act_package) as fsname
                                                                                        #                        , case when myc.mgr_host = 'stream' then 'stream' else 'restapi' end as type
                                                                                        #                        , wss.*
                                                                                        #                        from mycrontab myc, client_info ci, client_dns cdns, ws_status wss, myfeed.act_package_qry apq
                                                                                        #                        where myc.c_job_num = {c_job_num} and myc.c_name = '{c_name}'
                                                                                        #                        and ci.c_name = myc.c_name
                                                                                        #                        and ci.c_file = myc.c_file
                                                                                        #                        and ci.sel_act_packages like concat('%', apq.act_package, '%')
                                                                                        #                        and wss.name = cdns.c_host""".format(c_name=myReq['c_name'], c_job_num=myReq['c_job_num'])
											#itemss = mycon.exeQry("G", sql, IS_PRINT=True, useDict=True)
											#for items in itemss:
											#	myDic = {"myJob":procTabnm, "myStat":'D'}
											#	myDic.update(items)
											#	#myDic.update(myReq)
											#	myutil.rsleep(3,4)
											#	mysys.send(json.dumps(myDic).encode("utf8"))
											#	logger.info("{}".format(myDic))


									elif procTabnm == 'act_package_master':
										if mycmddic[mycmd] == 'I' or mycmddic[mycmd] == 'D':
											#sql = """select concat(ci.c_name,ci.c_file) as file_spec_name, fs.*, apm.*
                        								#from myfeed.file_spec fs, myfeed.act_package_master apm, myfeed.act_package_qry apq, myfeed.client_info ci
                        								#where apq.dbms in('stream','rio')
                        								#and apm.act_package = '{act_package}' and apm.act_package_seq = {act_package_seq}
                        								#and apq.act_package = apm.act_package
                        								#and ci.sel_act_packages = apm.act_package
                        								#and fs.c_name = ci.c_name and fs.c_file = ci.c_file
                        								#and apm.act_package_seq = fs.act_package_seq""".format(act_package=myReq['act_package'], act_package_seq=myReq['act_package_seq'])

											sql = """select concat(ci.c_name,ci.c_file) as file_spec_name, ci.sel_act_packages
												, concat(ci.c_name, '@', ci.c_file, '@', apm.act_package) as fsname, apm.*
												, ci.c_file
                                                                                        	from myfeed.act_package_master apm, myfeed.act_package_qry apq, myfeed.client_info ci
                                                                                        	where apq.dbms in('stream','rio')
                        									and apm.act_package = '{act_package}' and apm.act_package_seq = {act_package_seq}
                                                                                        	and apq.act_package = apm.act_package
                                                                                        	and ci.sel_act_packages like concat('%', apm.act_package, '%') """.format(act_package=myReq['act_package'], act_package_seq=myReq['act_package_seq'])
											for items in mycon.exeQry("G", sql, useDict=True, IS_PRINT=True):
												if items['c_file'].find("'") != -1:
													myQuote = '"'

												sel_act_packages_list = items['sel_act_packages'].replace("\t","").replace("\n","").replace("\r","").split('|')
												sel_act_package_idx = sel_act_packages_list.index(myReq['act_package'])

												myDic = {"myJob":'file_spec', "myStat":mycmddic[mycmd]}
												myDic2 = myDic
												sql = """select fs.*, apm.* 
													, concat(fs.c_name, '@', fs_c_file, '@', apm.act_package) as fsname
                        										from myfeed.file_spec fs, myfeed.act_package_master apm
                        										where fs.c_name = '{c_name}' and fs.c_file = {myQuote}{c_file}{myQuote} and fs.c_seq = {c_seq}
													and fs.sel_act_package_idx = {sel_act_package_idx}
                        										and apm.act_package = '{act_package}'
                        										and apm.act_package_seq = fs.act_package_seq""".format(myQuote=myQuote, c_name=items['c_name'], c_file=items['c_file'], c_seq=items['c_seq'], act_package=myReq['act_package'], sel_act_package_idx = sel_act_package_idx)
												for items2 in mycon.exeQry("G", sql, useDict=True, IS_PRINT=True):
													myDic2.update(items2)
													myutil.rsleep(3,4)
													mysys.send(json.dumps(myDic2).encode("utf8"))
										#else:
										#	sql = """select concat(ci.c_name,ci.c_file) as file_spec_name, fs.*
										#	, concat(fs.c_name, '@', fs_c_file, '@', apm.act_package) as fsname 
                        							#	from myfeed.file_spec fs, myfeed.client_info ci
                        							#	where ci.sel_act_packages = '{act_package}'
                        							#	and fs.c_name = ci.c_name and fs.c_file = ci.c_file
                        							#	and fs.act_package_seq = {act_package_seq}""".format(act_package=myReq['act_package'], act_package_seq=myReq['act_package_seq'])
										#	for items in mycon.exeQry("G", sql, useDict=True, IS_PRINT=True):
										#		myDic = {"myJob":'file_spec', "myStat":mycmddic[mycmd]}
										#		myDic2 = myDic
										#		myDic2.update(items)
										#		mysys.send(json.dumps(myDic2).encode("utf8"))

										#		#sql = """delete from myfeed.file_spec where c_file = '{c_file}' and 
											
									elif procTabnm == 'file_spec':
										sql = """select ci.sel_act_packages from myfeed.client_info ci where ci.c_name = '{c_name}' and ci.c_file = {myQuote}{c_file}{myQuote}""".format(myQuote=myQuote, c_name=myReq['c_name'], c_file=myReq['c_file'])
										items = mycon.exeQry("G1", sql, useDict=True, IS_PRINT=True)
										if items is not None:
											sel_act_packages_list = items['sel_act_packages'].replace("\t","").replace("\n","").replace("\r","").split('|')
											print(sel_act_packages_list, int(myReq['sel_act_package_idx']))
											act_package = sel_act_packages_list[int(myReq['sel_act_package_idx'])-1]

											if mycmddic[mycmd] == 'I' or mycmddic[mycmd] == 'D':
												sql = """select fs.*, apm.* 
                        									from myfeed.file_spec fs, myfeed.act_package_master apm
                        									where fs.c_name = '{c_name}' and fs.c_file = {myQuote}{c_file}{myQuote} and fs.c_seq = {c_seq}
												and fs.sel_act_package_idx = {sel_act_package_idx}
                        									and apm.act_package = '{act_package}'
                        									and apm.act_package_seq = fs.act_package_seq""".format(myQuote=myQuote, c_name=myReq['c_name'], c_file=myReq['c_file'], c_seq=myReq['c_seq'], sel_act_package_idx=myReq['sel_act_package_idx'], act_package=act_package)
												for items in mycon.exeQry("G", sql, useDict=True, IS_PRINT=True):
													myDic.update(items)
													myutil.rsleep(3,4)
													mysys.send(json.dumps(myDic).encode("utf8"))

											myutil.rsleep(3,4)
											c_name = myDic["c_name"]
											c_file = myDic["c_file"]
											myDic3 = {"myJob":procTabnm, "c_name":c_name, "c_file":c_file, "act_package":act_package, "myStat":"end"}
											myutil.rsleep(3,4)
											mysys.send(json.dumps(myDic3).encode("utf8"))
											logger.info("send!!!")
											#else:
											#	myDic.update(myReq)
											#	mysys.send(json.dumps(myDic).encode("utf8"))

									elif procTabnm == 'client_info':
										sel_act_packages_list = myReq['sel_act_packages'].replace("\t","").replace("\n","").replace("\r","").split("|")
										act_packages_qry_args_list = myutil.getSpecialStr(myReq['act_package_qry_args'].replace("\t","").replace("\n","").replace("\r","")).split("|")


										# check removed act_package at first
										sql = """select * from myfeed.client_info where c_name = '{c_name}' and c_file = '{c_file}'""".format(c_name=myReq['c_name'], c_file=myReq['c_file'])
										items = mycon.exeQry("G1", sql, IS_PRINT=True, useDict=True)
										if items is not None and mycmddic[mycmd] == 'I':
											if "act_package_qry_args" in items:
												del items["act_package_qry_args"]

											if myOriURL['sel_act_packages'] != items['sel_act_packages']:
												for ckPackage in myOriURL['sel_act_packages'].replace("\t","").replace("\n","").replace("\r","").split("|"):
													if items['sel_act_packages'].find(ckPackage) == -1:
														myDic3 = {"myJob":procTabnm, "act_package":ckPackage, "myStat":"D"}
														for k,v in myOriURL.items():
															k = k.replace("\t","").replace("\n","").replace("\r","")
															v = v.replace("\t","").replace("\n","").replace("\r","")
															myDic3[k] = v
															myutil.rsleep(3,4)
															mysys.send(json.dumps(myDic3).encode("utf8"))
												
										if mycmddic[mycmd] == 'I':
											for k,v in myReq.items():
												k = k.replace("\t","").replace("\n","").replace("\r","")
												v = v.replace("\t","").replace("\n","").replace("\r","")
												myDic[k] = v

											regexp_def_style=""".[^=]+=\".[^\"]*\"\s?(?:,|$)|.[^=]+=.[^\"]+\s?(?:,|$)|.[^=]+=\"\"|.[^=]+=$"""
											#sel_act_packages_list = myReq['sel_act_packages'].replace("\t","").replace("\n","").replace("\r","").split("|")
											#act_packages_qry_args_list = myutil.getSpecialStr(myReq['act_package_qry_args'].replace("\t","").replace("\n","").replace("\r","")).split("|")
											del myDic["act_package_qry_args"]

											for act_package, myArgStr in dict(zip(sel_act_packages_list,act_packages_qry_args_list)).items():
												myDic['act_package'] = act_package
												
												#myArgStr = myutil.getSpecialStr(v.replace("\t","").replace("\n","").replace("\r",""))
												for myARG in re.split(r'\][^\[,]*,[^\[]*\[', myArgStr.replace("\n","").strip('[] ')):
													myDic2 = dict([(x[:x.find("=")].strip(", "), x[x.find("=")+1:].strip(",' ") if x[x.find("=")+1:].strip(", ").startswith("'") else x[x.find("=")+1:].strip(",\" ")) for x in re.findall(regexp_def_style, myARG)])
													myDic['data'] = myDic2
													print(myDic2)
													myutil.rsleep(1,2)
													mysys.send(json.dumps(myDic).encode("utf8"))

												myutil.rsleep(3,4)
												c_name = myDic["c_name"]
												c_file = myDic["c_file"]
												myDic3 = {"myJob":procTabnm, "c_name":c_name, "c_file":c_file, "act_package":act_package, "myStat":"end"}
												myutil.rsleep(3,4)
												mysys.send(json.dumps(myDic3).encode("utf8"))
												logger.info("send!!!")
										else:
											if "act_package_qry_args" in myDic:
												del myDic["act_package_qry_args"]

											for k,v in myReq.copy().items():
												k = k.replace("\t","").replace("\n","").replace("\r","")
												v = v.replace("\t","").replace("\n","").replace("\r","")
												myDic[k] = v

											for act_package in sel_act_packages_list:
												#myDic.update(myDic)
												myDic['act_package'] = act_package
												myutil.rsleep(3,4)
												mysys.send(json.dumps(myDic).encode("utf8"))


									#if procTabnm in ['file_spec', 'client_info']:
									#	myutil.rsleep(3,4)
									#	#myDic["myStat"] = "end"
									#	c_name = myDic["c_name"]
									#	c_file = myDic["c_file"]
									#	myDic = {"myJob":procTabnm, "c_name":c_name, "c_file":c_file, "myStat":"end"}
									#	print(myDic)
									#	mysys.send(json.dumps(myDic).encode("utf8"))
									#	logger.info("send!!!")

							# real data treatment
							if mycmddic[mycmd] == 'D':
								smsMsg = "{}-{}-{}-{}".format(request.client_addr, request.authenticated_userid, request.matchdict['name'], str(mycon.exeQry(mycmddic[mycmd], tabnm, myReq, useColFilter=True, IS_PRINT=True)[0]))
								#logger.info("{}-{}-{}-{}".format(request.client_addr, request.authenticated_userid, request.matchdict['name'], str(mycon.exeQry(mycmddic[mycmd], tabnm, myReq, useColFilter=True, IS_PRINT=True)[0])))

								logger.info("{}".format(smsMsg))
								myutil.sms("박상우", smsMsg)
						except:
							print(myutil.getErrLine(sys))
							myerror = "alert(\"%s\")" % (myutil.getErrLine(sys))


				# listing
				myrows = []
				mylist = []
				if tabnm == 'file_spec':
					sql = """select ci.client_name, fs.c_name, fs.c_file, fs.sel_act_package_idx
					, cast(replace(replace(replace(SUBSTRING_INDEX(SUBSTRING_INDEX(ci.sel_act_packages, '|', fs.sel_act_package_idx), '\n', -2), '\n',''),'|',''),'\r','') as char(50)) as sel_act_package_name
					, fs.c_seq
					, fs.act_package_seq
					, (select apm.act_package_qry_col from myfeed.act_package_master apm where apm.act_package = cast(replace(replace(replace(SUBSTRING_INDEX(SUBSTRING_INDEX(ci.sel_act_packages, '|', fs.sel_act_package_idx), '\n', -2), '\n',''),'|',''),'\r','') as char(50)) and apm.act_package_seq = fs.act_package_seq) as act_package_seq_name
					, fs.act_package_block_seq, fs.myreplace  
					from myfeed.file_spec fs, myfeed.client_info ci 
					where fs.c_name = ci.c_name
					and fs.c_file = ci.c_file"""
				elif tabnm == 'mycrontab':
					sql = """select (select client_name from client_info where c_name = mc.c_name and c_file = mc.c_file) as client_name
							, mc.* 
							from {} mc
							order by {}""".format(tabnm, ",".join(['mc.'+x for x in mydic[tabnm][2]]))
				elif tabnm == 'ws_status':
					sql = """select wsstat.*
							from ws_status wsstat
							order by wsstat.url"""
				else:
					sql = "select * from {} order by {}".format(tabnm, ",".join(mydic[tabnm][2]))
					logger.info("{}-".format(sql))
				myrows = mycon.exeQry("G", sql)
				mylist = [HTMLParser().unescape(col[0]) for col in mycon.mycur.description]
      	  
			myHtml = """
<!DOCTYPE html>
<html>
<title>{tabnm}</title>
<head>
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="stylesheet" type="text/css" href="css/myfeed_tab.css">
</head>
<body>
	<script type="text/javascript" src="/tab/js/myfeed_tab.js?ver={myName}"></script>
	<script type="text/javascript" src="/tab/js/urgent_exe.js?ver={myName}"></script> 
""".format(tabnm=tabnm, myName=myName)
			if userset[request.authenticated_userid]['role1'] == 'A':
				myHtml += """
	<div class="myframeheader">
		<button class="open-button" onclick="openForm()">검색</button>
		<input type="text" id="myInput" onkeyup="mySearch()" placeholder="필터링 문자열을 타이핑 하세여..." size="50" value="%s">
		<button class="refresh-button" onclick="goRefresh()">새로고침</button>
	</div>

	<div class="form-popup" id="myForm">
		<form action="#" class="form-container" method="post">
			<h1>%s</h1>\n""" % (mySearchStr, tabnm)
			else:
				myHtml += """
	<div class="myframeheader">
		<input type="text" id="myInput" onkeyup="mySearch()" placeholder="필터링 문자열을 타이핑 하세여..." size="50" value="%s">
	</div>

	<div class="form-popup" id="myForm" method="post">
		<form action="#" class="form-container">
			<h1>%s</h1>\n""" % (mySearchStr, tabnm)


	#<form action="/myinsert" class="form-container">


			myHtml += """
			<input type='hidden' name="tabnm" value="{}" />""".format(tabnm)
			myHtml += """
			<input id="mysearchstr" type='hidden' name="mysearchstr" value="{}" />""".format(mySearchStr) # save search string if exists
			i = 1
			for mycol in mylist:
				# not editable
				if mycol in ['start_time','end_time','next_time','latest_status','sel_act_package_name','act_package_seq_name']:
					continue
				elif tabnm == 'file_spec':
					if mycol in ['client_name']:
						continue
				elif tabnm == 'mycrontab':
					if mycol in ['client_name']:
						continue

				myStyle=""	
				if (mycol.find("qry") != -1 or mycol.find("act_summary") != -1) and mycol.find("col") == -1:
					myStyle="""style='width:38.5vw;height:40vh'"""
				elif mycol == "sel_act_packages" or mycol.find("args") != -1 or mycol == 'email_body' or mycol == 'etc':
					myStyle="""style='width:38.5vw;height:20vh'"""
				elif mycol == "c_localdir" or mycol == "c_url":
					myStyle="""style='width:38.5vw;height:10vh'"""

				myHtml += """<div class='form_set_inner'>
						<div class="form_set_inner_l">
							<label for="{0}"><b>{0}</b></label>
						</div>
						<div class="form_set_inner_v">
							<textarea id="{0}_input" name="{0}" {1}></textarea>
						</div>
					</div>
					""".format(mycol, myStyle)
				i +=1


			myHtml +=""""
				<button type="submit" class="btn" formaction="/tab/myinsert">고고</button>
				<button type="button" class="btn cancel" onclick="closeForm()">빠이</button>
				<button type="submit" class="btn del" formaction="/tab/mydel" >삭제</button>"""

			if tabnm == 'mycrontab':
					myHtml +="""		
					<button type="button" id="btn_exe" class="btn exe" onclick="openExeForm()">즉시실행</button>
					"""
			#myHtml += """</div>
			#			</form>"""


			myHtml += """<div class='mybtn'> 
							<div class="form-inline-popup" id="myExeForm">
								<form class="myExeForm" id="myExeFormCt" method="post">
									<label>- package api query : </label>	
									<span style="font-size:35px" onclick="document.getElementById('myExeForm').style=display='none'" class="close" title="">&times;</span>
									<div class="myExe_ct" id="myExe_s1">
										<input type="radio" id="qry1" name="qry" value="myqry" checked="checked" />
										<label for="qry1">myqry</label>
										<input type="radio" id="qry2" name="qry" value="tmp_qry1" />
										<label for="qry1">tmp_qry1</label>
										<input type="radio" id="qry3" name="qry" value="api_qry" />
										<label for="qry1">api_qry</label>
									</div>

									<label>- package api qry_arg: </label>	
									<div class="myExe_ct" id="myExe_s2">
										<textarea id="myExe_s2_text" name="qyr_arg"></textarea>
									</div>

									<label>- package api query add statement: </label>	
									<div class="myExe_ct" id="myExe_s3">
										<textarea id="myExe_s3_text" name="e"></textarea>
									</div>

									<label>- localhost list: </label>	
									<div class="myExe_ct" id="myExe_s4">
										<textarea id="myExe_s4_text" name="localhost"></textarea>
									</div>

									<label>- localdir : </label>	
									<div class="myExe_ct" id="myExe_s5">
										<textarea id="myExe_s5_text" name="localdir"></textarea>
									</div>

									<label>- filename : </label>	
									<div class="myExe_ct" id="myExe_s6">
										<textarea id="myExe_s6_text" name="filename"></textarea>
									</div>

									<label>- do you want to send to client: </label>	
									<div class="myExe_ct" id="myExe_s7">
										<div style="display:inline-block;width:100%">
											<label sytle="padding:0px 50px 0px 0px">
												<input style="transform:scale(2);margin-bottom:10px" type='checkbox' checked="checked" name="send" /> YES, send to client 
											</label>

											<span style="float:right" class="send">
												<input type="submit" id="btn_go_exe" class="btn go" value="실행고고"></button>
											</span>
										</div>
									</div>
								</form>
							</div>	
						</div> """

			myHtml += """</div>
						</form>"""

			# list
			myHtml += """
					<br>
					<br>
					<div>

					<div id="myProgress">
						<div id="myBar">
							Process.....
						</div>
					</div>
					<table id="mytablelist" >
						<thead>
							<tr>

				"""

			# table header and style
			for mycol in mylist:
				myStyle = ""
				if mycol.find("seq") != -1:
					myStyle="""style="width:10vw" """
				elif mycol == "act_package":
					myStyle="""style='width:20vw'"""
				elif mycol.find("qry_col") != -1:
					myStyle="""style='width:30vw'"""
				elif mycol.find("data_type") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("summary") != -1:
					myStyle="""style='width:40vw'"""
				elif mycol.find("act_package") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("dbms") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("dbnm") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("host") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("port") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("myencoding") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("myqry_link_col") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("myqry") != -1:
					myStyle="""style='width:100vw'"""
				elif mycol.find("tmp_qry1") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("test_qry") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("client_name") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("c_name") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("c_file") != -1:
					myStyle="""style='width:30vw'"""
				elif mycol.find("act_package_qry_args") != -1:
					myStyle="""style='width:40vw'"""
				elif mycol.find("join_package_where") != -1:
					myStyle="""style='width:20vw'"""
				elif mycol.find("join_package_alias") != -1:
					myStyle="""style='width:10vw'"""
				elif mycol.find("c_url") != -1:
					myStyle="""style='width:40vw'"""
				elif mycol.find("c_dir") != -1:
					myStyle="""style='width:20vw'"""


				myHtml = myHtml+"<th height='50px' {1} onclick=\"mySortTable('{0}')\">{0}</th>\n".format(HTMLParser().unescape(mycol), myStyle)
			myHtml += """</thead>
					<tbody>"""

			# table body
			i = 0
			addEV=""
			if userset[request.authenticated_userid]['role1'] == 'A':
				addEV='onclick="openForm(this)"'
			
			for myrow in myrows:
				myHtml = myHtml+ """<tr id="mytablelist_{0}" {1}>\n""".format(i, addEV)
				#if myrow[0] == "선물환계산기_2270":
					#if myrow[0] == "DB_STOCK_MASTER":
				#	print(myrow)
				for j in range(0, len(mylist)):
					setData=myrow[j] 
					if mylist[j] == 'latest_status':
						if setData == 'O': #success
							setData='<img class="light" src="/tab/static/O.png">'
						elif setData == 'F':
							setData='<img class="light" src="/tab/static/N.png">'
						else:
							setData='<img class="light" src="/tab/static/R.png">'

					setData = HTMLParser().unescape(str(setData)).replace("<br>","").replace("\n", "<br>")
					myHtml = myHtml + """<td class="{0}" title="{0}">{1}</td>\n""".format(mylist[j], setData)
					
				myHtml = myHtml + """</tr>"""
				i+=1

			myHtml += """
	</tbody>
      	  </table>
	</div>
		<script>mySearch();</script>	
       	  </body>
      	   </html>"""
	except:
		logger.info("{}".format(myutil.getErrLine(sys)))
		myHtml = """hul!! error"""

	return Response(myHtml)

def mymon(request):
	mytab = request.matchdict['name']
	myReq = dict(request.GET)
	if mytab == 'stream':
		c_name=''
		c_job_num=''
		client_name=''
		sel_act_packages=''
		c_id = ''
		c_passwd = ''
		c_host = ''
		try:
			c_name=myReq['c_name']
			c_job_num=myReq['c_job_num']
		except:
			pass

		with mydbapi.Mydb("mysql", "myfeed", _myHost="ftp2", _myPort=3306, _myUser='myfeed') as mycon:
			sql = """select ci.client_name, ci.sel_act_packages, cdns.*
				from mycrontab mct, client_info ci, client_dns cdns
				where mct.c_name='{c_name}' and mct.c_job_num='{c_job_num}'
				and mct.c_name = ci.c_name and mct.c_file = ci.c_file
				and mct.c_url like concat('%', cdns.c_url, '%')
				and cdns.c_proto like 'WS_%'""".format(c_name=c_name,c_job_num=c_job_num)
			try:
				myDB = mycon.exeQry("G1", sql, useDict=True, IS_PRINT=True)
				client_name = myDB['client_name']	
				sel_act_packages = myDB['sel_act_packages'].replace("\n","").replace("\r","").replace("\t","")

				c_id = myDB['c_id']
				c_passwd = myDB['c_passwd']
				c_host = myDB['c_host']
			except:
				pass

		myHtml="""
			<html>
			<head>
			<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
			<title>infomax stream 구독 서비스 monitor</title>
			<link rel="stylesheet" type="text/css" href="/mon/css/myfeed_stream.css?ver={myName}">
			<script type="text/javascript" src="/mon/js/myfeed_stream.js?ver={myName}"></script>
			<script>
				function connect() {
			    	    const webSocket = new WebSocket('wss://myfeed.einfomax.co.kr/%s/');
			    	 	 webSocket.onopen = function () {
			    	 	   //const mydata = document.getElementById("success");
			    	 	           //jstalktheme_testfunc(mydata)
			    	 	   //mydata.innerHTML = "서버와 웹소켓 연결 성공";
			    	 	   //console.log('서버와 웹소켓 연결 성공!');
			    	 	   webSocket.send('{"id":"%s","passwd":"%s"}')
			    	 	   //webSocket.send('{"type":"urgent","c_name":"mirae","c_job_num":"10"}')
			    	 	   webSocket.send('{"c_name":"%s","c_job_num":"%s"}')
			    	 	   //webSocket.send('{"c_name":"sketernix","c_job_num":"4"}')
			    	 	   //webSocket.send('{"type":"urgent","c_name":"mirae","c_job_num":"13","qry_arg":{"InBlock.mydate":"20240702"}}')
			    	 	};
			""" % (c_host.lower(), c_id, c_passwd, c_name, c_job_num)

		myHtml +="""
					webSocket.onclose = function(e) {
						connect();
					};

      					webSocket.addEventListener("error", (event) => {
      					  console.log("websocket error : ", event)
      					});

      					webSocket.onmessage = function (event) {
      					  //console.log(event.data);
      					  //const mydata = document.getElementById("there");
      					      // mydata.innerHTML = event.data;
      					          jstalktheme_testfunc(event.data, '%s');
      					          //webSocket.ping();
      					  //webSocket.close();
      					  //webSocket.send('클라이언트에서 서버로 답장을 보냅니다');
      					};

			};

			connect();""" % (client_name+" "+sel_act_packages)

		myHtml+="""	
			</script>
			</head>
			
			<body>
			        <div style="color: blue;font-size:15px;"><b>-%s %s 스트림(%s,%s,%s)</b></div>
			""" % (client_name, sel_act_packages, c_id, c_passwd, c_host)

		myHtml +="""
			<!--<div class="jstalktheme" id="jstalktheme_test" style="width: 320px; height: 480px;"></div>-->
			<div class="jstalktheme" id="jstalktheme_test" style="width: 100%; height: 1000px;">
			
			<div class="msg">
			</div>
			
			<div class="sendmsg">
			    <!--<textarea class="textarea" id="jstalktheme_testmsg" onkeypress="if(event.keyCode==13){ jstalktheme_testfunc(); this.value=''; return false; }else if(event.keyCode==10){ this.value+='\n'; }"></textarea>
			    <div class="button" onclick="jstalktheme_testfunc()">
			           <p>전송</p>
			    </div>
			    <div class="clear">
			    </div>-->
			</div>
			
			</div>
			</body>
			</html>
			""" 
	else:
		myHtml="""잘못된 접근이영!"""

	return Response(myHtml)

def myapi(request):
	mytab = request.matchdict['name']

	# bad request
	myReVal = "<html> package {mytab} is not serviced..</html>".format(mytab=mytab)
	resp = Response()
	params = resp.content_type_params
	resp.text = myReVal


	# check pacakge
	myDB = []
	with mydbapi.Mydb("mysql", "myfeed", _myHost="ftp2", _myPort=3306, _myUser='myfeed') as mycon:
		myDB = mycon.exeQry("G1", "select * from myfeed.act_package_qry where act_package = '{mytab}'".format(mytab=mytab), useDict=True, IS_PRINT=True)

	# if package 
	if len(myDB) > 0:
		# check option
		myparam= {k:v for k,v in request.GET.items()}
		print(myDB)
		print(myparam)
		for myDefKey in re.findall("{.[^{}\\\\]*}", myDB['api_qry']):
			myKey = myDefKey[1:-1]
			if myKey not in myparam:
				if myKey.find("{") != -1 or myKey.find("}") != -1:
					pass
				else:
					myparam[myKey] = ""
	
		myqry = myDB['api_qry'].format(**myparam).replace("\r\n"," ")
		print(myqry)

		items = []	
		with mydbapi.Mydb(myDB['dbms'], myDB['dbnm'], _myHost=myDB['host']) as c:
			for item in c.exeQry("G", myqry, useDict=True):
				for k,v in item.items():
					if isinstance(v, Decimal):
						v = str(v).strip()
					elif isinstance(v, datetime.date):
						v = str(v).strip()
					try:
						item[k] = v.rstrip('\x00').replace('\u0000', '').strip()
					except:
						pass
				items.append(item)	

		mydata = items	

		myReVal = mydata
		resp.content_type = 'application/json;charset=utf-8'
		resp.json_body = myReVal 


	resp.content_type_params = params
	return resp

class DecimalEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, Decimal):
			return str(obj)

		elif isinstance(obj, datetime.date):
			return str(obj)

		return json.JSONEncoder.default(self, obj)

# make login or logout by a page	
#def login_view(request):
#	return Response("login")
#
#def logout_view(request):
#	return Response("logout")
#
#def includeme(config):
#	config.add_route('login', '/login')
#	config.add_view(login_view, route_name='login')
#	config.add_route('logout', '/logout')
#	config.add_view(logout_view, route_name='logout')
#	config.scan(__name__)


# modify the main function to include the configuration of login and logout views



def main(global_conf, **settings):
	with Configurator(settings=settings) as config:
		# authuntication
		authn_policy = BasicAuthAuthenticationPolicy(check_credentials)
		config.set_authentication_policy(authn_policy)
		config.set_authorization_policy(ACLAuthorizationPolicy()) 
		config.set_root_factory(lambda request: Root())

		#static
		config.add_static_view(name="/tab/js", path='js', )
		config.add_static_view(name="/tab/css", path='css')
		config.add_static_view(name="/tab/static", path='static')
		config.add_static_view(name="/mon/css", path='./mon/css')
		config.add_static_view(name="/mon/js", path='./mon/js')

		# route
		config.add_route('myhome', '/')
		config.add_route('mymon', '/mon/{name}')
		config.add_route('wanttab', '/tab/{name}')

		config.add_view(hello_world, route_name='myhome', permission='view')
		config.add_view(wanttabprc, route_name='wanttab', permission='view')
		config.add_view(mymon, route_name='mymon', permission='view')
		
		config.scan(__name__)
		return config.make_wsgi_app()

    

if __name__ == '__main__':
	global myPort
	global myServ	
	global myName
	#default
	myPort="7789"
	myServ="https://myfeed.einfomax.co.kr"

	myName = myutil.getToday("%Y%m%d%H%M%S")

	try:
		#myName = sys.argv[1]
		myPort = sys.argv[1]
		if myPort == '1234':
			myServ="https://myfeeddev.einfomax.co.kr"
		else:
			myServ = "http://"+socket.gethostbyname(socket.gethostname())+":"+myPort
		
	except:
		pass


	from waitress import serve
	app = main({})
	serve(app, listen='0.0.0.0:'+myPort)
