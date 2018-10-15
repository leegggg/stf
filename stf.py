import requests
import bs4
import re
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
}
MAX_LENGTH = 2048

class Resource(Base):
    # 表的名字:
    __tablename__ = 'RESOURCE'

    def __init__(self, res):
        self.url = str(res.get('url'))[0:MAX_LENGTH]
        self.pageId = int(res.get('pageId'))
        self.resId = int(res.get('resId'))
        self.title = str(res.get('title'))[0:MAX_LENGTH]
        self.link = str(res.get('link'))[0:MAX_LENGTH]
        self.pwd = str(res.get('pwd'))[0:MAX_LENGTH]
        return

    # 表的结构:
    url = Column(String(MAX_LENGTH), primary_key=True)
    pageId = Column(Integer)
    resId = Column(Integer)
    title = Column(String(MAX_LENGTH))
    link = Column(String(MAX_LENGTH))
    pwd = Column(String(MAX_LENGTH))

    def __str__(self):
        linkStr = str(self.link)
        length = len(linkStr)
        linkOut = "{}...{}({})".format(linkStr[0:8],linkStr[length-8:length],length)
        return "url: {url}, pageId: {pageId}, resId: {resId}, title: {title}, link: {link}, pwd: {pwd}".format(
            url=self.url,pageId=self.pageId,resId=self.resId,title=self.title,link=linkOut,pwd=self.pwd)


def getResources(baseUrl: str, pageId :int, resId : int):
    url = '{}{}/'.format(baseUrl,pageId)

    if resId > 0:
        url = '{}{}.html'.format(url, resId)

    resHtml = None
    try:
        resHtml = requests.get(url).content.decode('gbk')
    except:
        logging.warning("Download failed {}".format(url))

    if resHtml is None:
        return None

    resPage = bs4.BeautifulSoup(resHtml, "html.parser")
    scripts = resPage.find_all("script", type="text/javascript")
    jsStr = None
    for script in scripts:
        jsStr = str(script)
        if jsStr.find("假如您无法点击下载,或者看不到下载地址。很可能是您的浏览器开启的广告屏蔽功能把下载地址给误杀了。") > 0:
            break

    if jsStr is None:
        return None

    regexp = re.compile("<div class=ad><table .+</table></div>")
    matchs = regexp.findall(jsStr)

    if len(matchs) < 1:
        return None

    resTabHtml = str(matchs.pop())

    resTab = bs4.BeautifulSoup(resTabHtml, "html.parser")

    span = resTab.find("span", {'class':'red'})
    link = span.parent.find('a')

    return {
        'url': url,
        'pageId': pageId,
        'resId': resId,
        'title': resPage.head.title.text,
        'link': link.get("href"),
        'pwd': span.text
    }

    pass


def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s : \t %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


    url = "http://www.zgpingshu.com/dabao/"
    engine = create_engine('sqlite:///./resource.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)

    for page in range(5500, 6000):
        logging.info("Downloading page {}".format(page))
        for resId in range(20):
            res = getResources(baseUrl=url, pageId=page, resId=resId)
            if res is not None:
                obj = Resource(res=res)
                try:
                    session.merge(obj)
                    session.commit()
                except:
                    raise
                finally:
                    session.close()
                logging.info(obj)
            elif resId == 0:
                logging.info("Give up page {}".format(page))
                break
            elif resId >= 6:
                logging.info("For {} stop at {}".format(page,resId))
                break

    return


if __name__ == "__main__":
    main()