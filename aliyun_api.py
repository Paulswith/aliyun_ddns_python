# coding: utf8

import hashlib
import hmac
import json
import os
import urllib.parse as urlparser
import uuid
import base64
import requests
from datetime import datetime
import logging


logging.basicConfig(format='[%(asctime)s] %(levelname)s %(message)s', level=os.environ.get("DDNS_LOG_LEVEL", "INFO"))
logger = logging.getLogger()


class Job:
	REQUEST_URL = "https://alidns.aliyuncs.com/"
	ALIYUN_SETTINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

	@classmethod
	def get_common_params(cls, access_key: str) -> dict:
		"""
		获取公共参数
		参考文档：https://help.aliyun.com/document_detail/29745.html?spm=5176.doc29776.6.588.sYhLJ0
		"""
		return {
			"Format": "json",
			"Version": "2015-01-09",
			"AccessKeyId": access_key,
			"SignatureMethod": "HMAC-SHA1",
			"Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
			"SignatureVersion": "1.0",
			"SignatureNonce": uuid.uuid4()
		}

	@classmethod
	def get_signed_params(cls, http_method: str, params: dict, access_key: str, access_secret: str) -> dict:
		"""
		参考文档：https://help.aliyun.com/document_detail/29747.html?spm=5176.doc29745.2.1.V2tmbU
		"""

		# 1、合并参数，不包括Signature
		params.update(cls.get_common_params(access_key))
		# 2、按照参数的字典顺序排序
		sorted_params = sorted(params.items())
		# 3、encode 参数
		query_params = urlparser.urlencode(sorted_params)
		# 4、构造需要签名的字符串
		str_to_sign = http_method + "&" + urlparser.quote_plus("/") + "&" + urlparser.quote_plus(query_params)
		# 5、计算签名
		digest = hmac.new(
			f"{access_secret}&".encode(),
			str_to_sign.encode(),
			hashlib.sha1
		).digest() #此处注意，必须用str转换，因为hmac不接受unicode，大坑！！！
		signature = base64.encodebytes(digest).decode("utf-8").rstrip("\n")
		# 6、将签名加入参数中
		params["Signature"] = signature

		return params

	@classmethod
	def update_domains(cls, ip: str) -> None:
		"""
		修改云解析
		参考文档：
			获取解析记录：https://help.aliyun.com/document_detail/29776.html?spm=5176.doc29774.6.618.fkB0qE
			修改解析记录：https://help.aliyun.com/document_detail/29774.html?spm=5176.doc29774.6.616.qFehCg
		"""
		update_type = "A"
		update_value = ip
		if len(ip.split(".")) != 4:
			logger.debug(f"Identify ip={ip} as ipv6, if ipv4, please use '.' separate")
			update_type = "AAAA"
			update_value = ip

		with open(cls.ALIYUN_SETTINGS, "r") as f:
			settings = json.loads(f.read())
		update_subdomains = set(settings["update-subdomains"])
		assert len(update_subdomains) > 0, "zero update-subdomains configured"
		logger.info(f"Updating ip={ip} for subdomains={update_subdomains}")
		# query records by root-domain
		get_params = cls.get_signed_params(
			"GET",
			{
				"Action": "DescribeDomainRecords",
				"DomainName": settings["root-domain"],
				"TypeKeyWord": update_type
			},
			settings["access_key"],
			settings["access_secret"]
		)
		logger.debug(f"Built query domains {get_params=}")
		rsp = requests.get(cls.REQUEST_URL, get_params)
		logger.debug(f"Query domains with status={rsp.status_code}")
		records = rsp.json()
		logger.debug(f"{records=}")

		# update domain if match wanna change list
		all_records = records["DomainRecords"]["Record"]
		if len(all_records) == 0:
			raise RuntimeError("Not found any records, check log and settings.json")
		for record in all_records:
			if record["RR"] in update_subdomains:
				logger.debug("Matched need update domain")
				if ip == record["Value"]:
					logger.info("Don't need to update, cause values are same")
					continue
				post_params = cls.get_signed_params("POST", {
					"Action": "UpdateDomainRecord",
					"RecordId": record["RecordId"],
					"RR": record["RR"],
					"Type": record["Type"],
					"Value": update_value
				}, settings)
				logger.debug(f"Built update domains {get_params=}")
				rsp = requests.post(cls.REQUEST_URL, post_params)
				logger.debug(f"{rsp.status_code}")
				logger.debug(f"{rsp.json()}")
				logger.info(f"Updated {record['RR']} succeed")


if __name__ == "__main__":
	import sys

	assert len(sys.argv) == 2, (
		"view verbose logger by set `export DDNS_LOG_LEVEL=DEBUG`, default is INFO\n"
		f"run as `python {sys.argv[0]} <ipv4 or ipv6>`"
	)
	Job.update_domains(ip=sys.argv[1])

