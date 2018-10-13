import requests
import bs4

baseurl = "http://www.zgpingshu.com/dabao/"
for index in range(571, 572):
    bdUrl = "{}{}/".format(baseurl, index)
    bdpageHtml = requests.get(bdUrl).content.decode(
        'gbk')
    bdpage = bs4.BeautifulSoup(bdpageHtml)
    # print(bdpage.prettify)
    links = bdpage.find_all("a")
    for link in links:
        print(link)
        pass
