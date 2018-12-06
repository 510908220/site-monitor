# -*- encoding: utf-8 -*-

import asyncio
import requests
import sys
from pyppeteer import launch


def _get_reason(status_code):
    try:
        reason = requests.status_codes._codes[status_code][0]
    except:
        reason = 'err'
    return reason


def request_get(url, cookies, headers):
    request = requests.get(url,
                           cookies=cookies,
                           headers=headers,
                           timeout=(20, 30),
                           verify=False)
    return request.status_code


def check(url):
    params = {
        'executablePath': '/usr/bin/google-chrome',
        'headless': True,
        'ignoreHTTPSErrors': True,
        'args': ['--no-sandbox', '--disable-gpu']
    }
    ret = {
        'status_code': 200
    }

    async def main():
        browser = await launch(params)
        page = await browser.newPage()
        response = await page.goto(url)  # 这一步是521

        # 感谢黑岩同学提供新的方式:保持浏览器和requests UA一致就可以成功访问
        # 这样将第二次浏览器访问替换为requests, 节省时间
        page_cookies = await  page.cookies()
        cookies = {}
        for item in page_cookies:
            cookies[item["name"]] = item["value"]
        user_agent = response._request._headers["user-agent"]
        headers = {'User-Agent': user_agent}
        ret['status_code'] = request_get(url, cookies, headers)
        # result = await response.text()
        await browser.close()
    asyncio.get_event_loop().run_until_complete(main())

    return ret['status_code'], _get_reason(ret['status_code'])


if __name__ == "__main__":
    status_code, reason = check(sys.argv[1])
    print('chrome:{}-{}'.format(status_code, reason))
