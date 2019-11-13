import requests
import time
import json
import pickle


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
        self._proxies = [{"https": "https://localhost:8060", "http": "http://localhost:8060"}]
        self._proxy = 0

    def run(self):
        self.getfollowers(5)
        self._data["followers"] = self._followerlist
        self._offset = 0

    def getfollowers(self, partial):

        print("正在抓取 {}-{} 关注者".format(self._offset, self._offset + 20))
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36",
            "Referer": "zhuanlan.zhihu.com"

        }
        with requests.Session() as s:
            try:
                with s.get(
                        "https://www.zhihu.com/api/v4/columns/{}/followers?"
                        "limit=20&offset={}".format(self._zl_id, self._offset),
                        headers=headers, timeout=5) as rep:
                    if rep.status_code == 403:
                        exit(1)
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
                self._proxy += 1

            finally:

                if self._offset + 20 <= self._followercount:
                    self._offset = self._offset + 20
                    # print("防止被办，休息0.5s")
                    time.sleep(1.3)
                    if partial > 0:
                        self.getfollowers(partial-1)
                else:
                    print("关注者获取完毕")

    def refresh(self):
        self._usrfollowing = []

    def getfollowingzl(self, usr_token):
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36",
            "Referer": "zhuanlan.zhihu.com"
        }
        with requests.Session() as s:
            try:
                with s.get(
                        # , proxies=self._proxies[self._proxy % len(self._proxies)]
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
                                                                  "url": "https://zhuanlan.zhihu.com/" + zl["url"][
                                                                        30:len(zl["url"])]}
                                                       })
                        # print(self._followerlist)
            except Exception as e:
                self._proxy += 1
                print(e.args)

            finally:

                if self._offset == 0:
                    print("他关注了", self._followingcount, "个专栏")
                if self._offset + 20 <= self._followingcount:
                    self._offset = self._offset + 20
                    # print("防止被办，休息0.1s")
                    time.sleep(0.5)
                    self.getfollowingzl(usr_token)


if __name__ == '__main__':
    cont = 1

    if cont:
        load_bak = open("breakpoint.bak", "rb")
        zl_pc = pickle.load(load_bak)
        zl_pool = pickle.load(load_bak)
        zl_follower_count = pickle.load(load_bak)
        zl_article_count = pickle.load(load_bak)
        yh_pool = pickle.load(load_bak)
        yh_pc = pickle.load(load_bak)
        zl_cur = pickle.load(load_bak)
        zl_detailed = pickle.load(load_bak)
        zllist = pickle.load(load_bak)
        load_bak.close()
    else:
        zl_pc = set()
        zl_pool = []
        zl_follower_count = []
        zl_article_count = []
        yh_pool = []
        yh_pc = set()
        zl_cur = 0
        zl_detailed = 0
        zllist = []
        zl_pc.add("founderchip2")
        zl_pool.append("founderchip2")
        zl_follower_count.append(495)
        zl_article_count.append(6)

    while zl_cur < len(zl_pool):
        zhi = Getzl(zl_pool[zl_cur])
        zhi.run()
        for zlfollower in zhi._data["followers"]:
            if zlfollower[29:len(zlfollower)] not in yh_pc:
                tmp = len(zl_pool)
                print("正在抓取第", len(yh_pc), "位用户所关注的专栏", end=' ')
                # print(zlfollower[29:len(zlfollower)])
                yh_pc.add(zlfollower[29:len(zlfollower)])
                zhi.refresh()
                zhi.getfollowingzl(zlfollower[29:len(zlfollower)])
                # print("got")
                for zl in zhi._usrfollowing:
                    # print(" ", zl["id"])
                    if zl["id"] not in zl_pc:
                        zl_pool.append(zl["id"])
                        zl_follower_count.append(zl["followers"])
                        zl_article_count.append(zl["articles_count"])
                        zl_pc.add(zl["id"])
                        zllist.append(zl["zlinfo"])
                        # print("   ", zl["zlinfo"]["title"])
                print("        新增了", len(zl_pool) - tmp, "个专栏")
        zhi.refresh()
        print(json.dumps(zllist, indent=4, separators=(', ', ': '),
                         ensure_ascii=False), file=open("zllist.txt", "w+", encoding="utf-8"))
        print(zl_pool, file=open("zlpool.txt", "w+", encoding="utf-8"))
        print(zl_follower_count, file=open("zlfollowercount.txt", "w+", encoding="utf-8"))
        zl_cur += 1
        print("***完成抓取第", zl_cur, "个专栏")
        save_bak = open("breakpoint.bak", "wb")
        pickle.dump(zl_pc, save_bak)
        pickle.dump(zl_pool, save_bak)
        pickle.dump(zl_follower_count, save_bak)
        pickle.dump(zl_article_count, save_bak)
        pickle.dump(yh_pool, save_bak)
        pickle.dump(yh_pc, save_bak)
        pickle.dump(zl_cur, save_bak)
        pickle.dump(zl_detailed, save_bak)
        pickle.dump(zllist, save_bak)
        save_bak.close()
