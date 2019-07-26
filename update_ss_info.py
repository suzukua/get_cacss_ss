#!coding:utf-8    相信这句大家都懂的，不解释
#导入需要的python模块httplib，用来模拟提交http请求，详细的用法可见python帮助手册
import httplib
import urllib
import re
import base64
import json
import urlparse
import os,sys,socket
import time


USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
ACCEPT='*/*'

def syslog(text):
    if sys.platform == 'linux2':
        os.system('logger -t "【SS-UPDATE】" "' + str(text) + '"')
    elif sys.platform == 'darwin':
        print('logger -t "【SS-UPDATE】" "' + str(text) + '"')


def getSS1Info():
    host = 's1.cacss.me'
    #定义请求头
    reqheaders={
        'Accept':ACCEPT,
        'Host': host,
        'Origin':'http://%s' % (host),
        'Referer':'http://%s/' % (host),
        'User-Agent': USER_AGENT,
        'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    params = urllib.urlencode({'token':''})
    conn=httplib.HTTPConnection(host, timeout=10)
    url = 'http://%s/qrcode' % (host)
    syslog('正在请求' + url)
    conn.request(method='POST', url=url, body=params, headers=reqheaders)
    #获取服务器的返回
    res=conn.getresponse()
    resStr=res.read()
    ssStr = ((json.loads(resStr)['qrcode']).encode('UTF-8')).replace("ss://",'')
    ssStr = "ss://" + base64.b64decode(ssStr)
    syslog("SS服务器1匹配结果: " + ssStr)
    return getServerConfig(ssStr)

def getSS2Info():
    host = 's2.cacss.me'
    #定义请求头
    reqheaders={
        'Accept':ACCEPT,
        'Host': host,
        'Origin':'http://%s' % (host),
        'Referer':'http://%s/' % (host),
        'User-Agent': USER_AGENT
    }
    conn=httplib.HTTPConnection(host, timeout=10)
    url = 'http://%s/' % (host)
    syslog('正在请求' + url)
    conn.request(method='GET', url=url, headers=reqheaders)
    #获取服务器的返回
    res=conn.getresponse()
    resStr=res.read()
    #pattern = re.compile('<a id="qrcode" href="(ss://.*)"></a>')
    m = re.findall('<a id="qrcode" href="ss://(.*)"></a>', resStr)
    ssStr = "ss://" + base64.b64decode(m[0])
    syslog("SS服务器2正则匹配结果: " + ssStr)
    return getServerConfig(ssStr)

def getSS3Info():
    host = 's3.cacss.me'
    #定义请求头
    reqheaders={
        'Accept':ACCEPT,
        'Host': host,
        'Origin':'http://%s' % (host),
        'Referer':'http://%s/' % (host),
        'User-Agent': USER_AGENT
    }
    conn=httplib.HTTPConnection(host, timeout=10)
    url = 'http://%s/' % (host)
    syslog('正在请求' + url)
    conn.request(method='GET', url=url, headers=reqheaders)
    #获取服务器的返回
    res=conn.getresponse()
    resStr=res.read()
    #pattern = re.compile('<a id="qrcode" href="(ss://.*)"></a>')
    m = re.findall('<a id="qrcode" href="ss://(.*)"></a>', resStr)
    ssStr = "ss://" + base64.b64decode(m[0])
    syslog("SS服务器1正则匹配结果: " + ssStr)
    return getServerConfig(ssStr);


def getServerConfig(ssStr):
    parsedResult=urlparse.urlparse(ssStr);
    config = {"server": "", "port": "", "password": "", "method": ""};
    if len(parsedResult.hostname) == 0 or len(str(parsedResult.port)) == 0 or len(parsedResult.username) == 0 or len(parsedResult.password) == 0:
        syslog("无法解析ss协议: " + ssStr)
        return
    config['server'] = parsedResult.hostname
    config['port'] = parsedResult.port
    config['method'] = parsedResult.username
    config['password'] = parsedResult.password
    if testConnection(config['server'], config['port']):
        return config;

def testConnection(HOST, PORT):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    ADDR = (str(HOST),int(PORT))
    times = 3
    for i in range(1, times+1):
        status = s.connect_ex(ADDR)
        if status != 0:
                syslog('Connection to %s %s port [tcp] failure [%s] times' % (HOST,PORT, i))
                if i == times:
                    return False
                else:#重试等待0.3s
                    time.sleep(0.3)

        else:
                syslog('Connection to %s %s port [tcp] succeeded [%s] times!' % (HOST,PORT, i))
                return True


def updateSSConfig(serverIndex, config):
    syslog("第 {} 服务器-配置: {}".format(serverIndex, json.dumps(config)))
    serverKey='ss_server{}'.format(serverIndex) if serverIndex > 1 else 'ss_server'
    portKey='ss_s{}_port'.format(serverIndex) if serverIndex > 1 else 'ss_server_port'
    methodKey='ss_s{}_method'.format(serverIndex) if serverIndex > 1 else 'ss_method'
    keyKey='ss_s{}_key'.format(serverIndex) if serverIndex > 1 else 'ss_key'
    # nvram param name ss_server1,ss_s1_port,ss_s1_method,ss_s1_key
    paramCmdTemplate = 'nvram set {}={}'
    cmd = paramCmdTemplate.format(serverKey, config['server'])
    cmd += ' && ' + paramCmdTemplate.format(portKey, config['port'])
    cmd += ' && ' + paramCmdTemplate.format(methodKey, config['method'])
    cmd += ' && ' + paramCmdTemplate.format(keyKey, config['password'])
    cmd += '&& nvram commit'
    syslog('执行更新命令: ' + cmd)
    if sys.platform == 'linux2':
        os.system(cmd)

def main():
    index = 0;
    try:
        config1 = getSS1Info()
        if not config1 is None:
            index = index + 1
            updateSSConfig(index, config1)
    except Exception,e:
        syslog('getSS1Info: ' + e.message)

    try:
        config2 = getSS2Info()
        if not config2 is None:
            index = index + 1
            updateSSConfig(index, config2)
    except Exception,e:
        syslog('getSS2Info: ' + e.message)

    try:
        config3 = getSS3Info()
        if not config3 is None:
            index = index + 1
            updateSSConfig(index, config3)
    except Exception,e:
        syslog('getSS3Info: ' + e.message)

    syslog('ss配置[%s]个完毕' % (index))
    #只取2个有效服务器配置
    if index >= 1 and index <= 3 and sys.platform == 'linux2':
        syslog('开始重启ss')
        #关闭ss
        os.system("nvram set button_script_2=1 && /etc/storage/ez_buttons_script.sh 2 &")
        #sleep
        time.sleep(10)
        os.system("killall Sh15_ss.sh")
        #开启SS
        os.system("nvram set button_script_2=0 && /etc/storage/ez_buttons_script.sh 2 &")
        time.sleep(50)
        syslog('kill Sh15_ss')
        os.system("ps |grep Sh15_ss |grep -vE '(keep|grep)' | awk '{print $1}' |xargs kill")

main()
