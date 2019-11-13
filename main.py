import requests
import time
import json


class Getzl(object):

    def __init__(self, zl_id):

        self._offset = 0
        self._zl_id = zl_id
        self._articlecount = -1
        self._followercount = -1
        self._data = {}
        self._followerlist = []
        self._articlelist = []
        self._usrfollowing = []
        self._followingcount = 0


    def run(self):
        self.getfollowers(1)
        self._data["followers"] = self._followerlist
        self._offset = 0

    def run_full(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.31",
            "Referer": "zhuanlan.zhihu.com"
        }
        with requests.Session() as s:
            try:
                with s.get(
                        "https://zhuanlan.zhihu.com/{}/about".format(self._zl_id),
                        headers=headers, timeout=3) as rep:
                    data = rep.content

                    if data:  # analyze
                        tmpstr = str(data.decode('utf-8'))
                        p = tmpstr.find("ColumnAbout-title") + 19
                        head = p
                        while tmpstr[p] != '<':
                            p += 1
                        self._data["title"] = tmpstr[head:p]
                        p += 11
                        head = p
                        while tmpstr[p] != '<':
                            p += 1
                        self._data["description"] = tmpstr[head:p]
                        print(self._data)
            except Exception as e:
                print(e.args)
        self.getfollowers(0)
        self._data["followers"] = self._followerlist

        self._offset = 0
        self.getarticle()
        self._data["article"] = self._articlelist
        self._offset = 0

    def getfollowers(self, partial):

        print("正在抓取 {}-{} 关注者".format(self._offset, self._offset + 20))
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.31",
            "Referer": "zhuanlan.zhihu.com"
        }
        with requests.Session() as s:
            try:
                with s.get(
                        "https://www.zhihu.com/api/v4/columns/{}/followers?"
                        "limit=20&offset={}".format(self._zl_id, self._offset),
                        headers=headers, timeout=5) as rep:
                    data = rep.json()
                    # print(data)
                    if data:  # analyze
                        self._followercount = data['paging']['totals']
                        followers = data['data']
                        for follower in followers:
                            self._followerlist.append("https://www.zhihu.com/people/" + follower['url_token'])
                        # print(self._followerlist)
                        # print(len(self._followerlist))
            except Exception as e:
                print(e.args)

            finally:

                if self._offset + 20 <= self._followercount:
                    self._offset = self._offset + 20
                    # print("防止被办，休息0.5s")
                    time.sleep(1)
                    if not partial:
                        self.getfollowers(0)
                else:
                    print("关注者获取完毕")

    def getarticle(self):

        print("正在抓取 {} 文章".format(self._offset))
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.31",
            "Referer": "zhuanlan.zhihu.com"
        }
        with requests.Session() as s:
            try:
                with s.get(
                        "https://zhuanlan.zhihu.com/api/columns/{}/articles?"
                        "include=voteup_count,voting,topics,is_labeled,label_info"
                        "&limit=10&offset={}".format(self._zl_id, self._offset),
                        headers=headers, timeout=3) as rep:
                    data = rep.json()
                    # print(data)
                    if data:  # analyze
                        self._articlecount = data['paging']['totals']
                        articles = data['data']
                        # print(articles)

                        for article in articles:
                            articledata = {}
                            articledata["url"] = article["url"]
                            articledata["userName"] = article["author"]["name"]
                            articledata["userLink"] = "https://www.zhihu.com" + article["author"]["url"]
                            articledata["upvote"] = article["voteup_count"]
                            articledata["title"] = article["title"]
                            print("正在抓取文章:", articledata["title"])
                            with s.get(articledata["url"], headers=headers, timeout=3) as rep2:
                                data = rep2.content
                                if data:  # analyze
                                    tmpstr = str(data.decode('utf-8'))
                                    p = tmpstr.find("ztext Post-RichText")
                                    p = p + 21
                                    head = p
                                    while tmpstr[p:p + 24] != "class=\"ContentItem-time\"":
                                        p += 1
                                    articledata["content"] = tmpstr[head:p - 17]
                                    tags = []
                                    while tmpstr.find("TopicLink", p) > 0:
                                        tag = {}
                                        p = tmpstr.find("TopicLink", p)
                                        p += 17
                                        head = p
                                        while tmpstr[p] != "\"":
                                            p += 1
                                        tag["tagLink"] = "https:" + tmpstr[head:p]
                                        p = tmpstr.find("-content", p)
                                        p += 10
                                        head = p
                                        while tmpstr[p] != "<":
                                            p += 1
                                        tag["tag"] = tmpstr[head:p]
                                        tags.append(tag)
                                    articledata["topic"] = tags
                            # getcomment
                            comment_count = 1
                            comments = []
                            comment_offset = 0
                            child_count = 0
                            while len(comments)+child_count < comment_count:

                                with s.get("https://www.zhihu.com/api/v4/articles/{}/root_comments?order=normal"
                                           "&limit=20&offset={}&status=open".format(article["id"], comment_offset),
                                           headers=headers, timeout=5) as rep2:
                                    data = rep2.json()
                                    comment_count = data["common_counts"]
                                    data = data["data"]
                                    for comment_data in data:
                                        child_comment = []
                                        child_count += comment_data["child_comment_count"]
                                        for child_comment_data in comment_data["child_comments"]:
                                            child_comment.append({
                                                "userName": child_comment_data["author"]["member"]["name"],
                                                "userLink": child_comment_data["author"]["member"]["url"],
                                                "content": child_comment_data["content"],
                                                "likes": child_comment_data["vote_count"],
                                                "replyToAuthor": child_comment_data["reply_to_author"]["member"]["name"]
                                            })
                                        comment = {"userName": comment_data["author"]["member"]["name"],
                                                   "userLink": comment_data["author"]["member"]["url"],
                                                   "content": comment_data["content"],
                                                   "likes": comment_data["vote_count"],
                                                   "childComments": child_comment
                                                   }
                                        # if comment["userName"] == "知乎用户":
                                        #     print(comment)
                                        #     print(data)
                                        comments.append(comment)
                                time.sleep(0.5)
                            articledata["comments"] = comments
                            # print(data)
                            self._articlelist.append(articledata)
                            time.sleep(0.5)
                            # print(articledata)

            except Exception as e:
                print(e.args)

            finally:

                if self._offset + 10 <= self._articlecount:
                    self._offset = self._offset + 10
                    print("防止被办，休息2s")
                    time.sleep(2)
                    self.getarticle()
                else:
                    print("所有数据获取完毕")

    def refresh(self):
        self._usrfollowing = []

    def getfollowingzl(self, usr_token):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.31",
            "Referer": "zhuanlan.zhihu.com"
        }
        with requests.Session() as s:
            try:
                with s.get(
                        "https://www.zhihu.com/api/v4/members/{}/following-columns?"
                        "&offset={}&limit=20".format(usr_token, self._offset),
                        headers=headers, timeout=5) as rep:
                    data = rep.json()
                    # print(rep)
                    # print(data)
                    # print(data)
                    if data:  # analyze

                        self._followingcount = data['paging']['totals']
                        zls = data['data']
                        for zl in zls:
                            self._usrfollowing.append({"id": zl["id"],
                                                       "followers": zl["followers"],
                                                       "articles_count": zl["articles_count"],
                                                       "zlinfo": {"title": zl["title"],
                                                                  "url": zl["url"]}
                                                       })
                        # print(self._followerlist)
            except Exception as e:
                print(e.args)

            finally:

                if self._offset + 20 <= self._followingcount:
                    self._offset = self._offset + 20
                    # print("防止被办，休息0.1s")
                    time.sleep(0.7)
                    self.getfollowingzl(usr_token)


if __name__ == '__main__':
    zl_pc = set()
    zl_pc.add("c_1021051479859326976")
    zl_pool = ["c_1021051479859326976"]
    zl_follower_count = [101]
    zl_article_count = [10]
    yh_pool = []
    yh_pc = set()
    zl_cur = 0
    zl_detailed = 0
    zllist = []

    while zl_cur < len(zl_pool):
        zhi = Getzl(zl_pool[zl_cur])
        if zl_detailed < 500 and zl_follower_count[zl_cur] < 150 and zl_article_count[zl_cur] < 30:
            zhi.run_full()
            result = json.dumps(zhi._data, indent=4, separators=(', ', ': '),
                                ensure_ascii=False)
            print(result, file=open(str(zl_detailed) + ".txt", "w+", encoding="utf-8"))
            zl_detailed += 1
        else:
            zhi.run()
        for zlfollower in zhi._data["followers"]:
            if zlfollower not in yh_pc:

                if len(yh_pc) % 10 == 0:
                    print("正在抓取第", len(yh_pc), "位用户所关注的专栏")
                yh_pc.add(zlfollower[29:len(zlfollower)])
                zhi.refresh()
                zhi.getfollowingzl(zlfollower[29:len(zlfollower)])
                for zl in zhi._usrfollowing:
                    # print(zl)
                    if zl["id"] not in zl_pc:
                        zl_pool.append(zl["id"])
                        zl_follower_count.append(zl["followers"])
                        zl_article_count.append(zl["articles_count"])
                        zl_pc.add(zl["id"])
                        zllist.append(zl["zlinfo"])
                # print(len(zl_pool))
        zhi.refresh()
        print(zllist, file=open("zllist.txt", "w+", encoding="utf-8"))
        print(zl_pool, file=open("zlpool.txt", "w+", encoding="utf-8"))
        print(zl_follower_count, file=open("zlfollowercount.txt", "w+", encoding="utf-8"))
        zl_cur += 1
        print("***完成抓取第", zl_cur, "个专栏")
