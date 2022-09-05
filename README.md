fork from [limoxi/aliyun_ddns](https://github.com/limoxi/aliyun_ddns)

my case is:

got an openwrt router(redmi-AX6S) and dial pppoe on it

## setup steps
add your config in `settings.json`

1. this case wanna change rdp.mydomain.com
```
{
	"access_key": "test-Key",
	"access_secret": "test-Secret",
	"root-domain": "mydomain.com",
	"update-subdomains": [
		"acs"
	]
}
```


2. in order to run this script:
```bash
opkg install python3 python3-pip
# it install python=3.10.5 for me

python3 -m pip install requests
```

3. setup crontab: check every minute, shell script will check ethernet ip , report aliyun update ip but only when it changed
```
* * * * * cd /root/tasks/ddns && ./auto-ddns.sh
```

thanks limoxi
