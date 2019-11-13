import json

ans = []
for i in range(500):
    f = open("detail/" + str(i) + ".txt", "r", encoding="utf-8")
    data = f.read()
    zl = json.loads(data)
    ans.append(zl)
print(json.dumps(ans, indent=4, separators=(', ', ': '),
                 ensure_ascii=False), file=open("detailed_list.txt", "w+", encoding="utf-8"))
