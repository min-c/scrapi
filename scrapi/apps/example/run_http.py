from scrap_toolkit import SyncClient, body

def main():
    cli = SyncClient()
          

    try:
        # 1)
        host = 'https://sm-members.fcfc-1.com/'
        url = "/articles/select_articles/d4f5c2b4-3099-11ed-8ef9-0a7d4ce2d6b91.json"
        
        login_data = {"id": "YOUR_ID", "pw": "YOUR_PW"}
        param = {
                "os":"i1",
                "ver" : 514,
                "it" : "190000",
                "s_t" : 0,
                "pw" : "",
                "cat" : "J",
                "g_t" : 606893524,
                "mn" : "",
                "gid" : "9cd88836-346e-11eb-a992-0a07e56d23481"
                }

        login_resp = cli.post(host + url, json=param)
        res = body(login_resp) 
        print("[RESULT]", res)

        # 2) 로그인 후 자동으로 쿠키 유지 → API 호출
        # api_url = "https://sm-members.fcfc-1.com/articles/select_articles/d4f5c2b4-3099-11ed-8ef9-0a7d4ce2d6b91.json"
        # resp = cli.post(api_url, json={"foo": "bar"})
        # print("[API]", resp.status_code)
        # print(resp.text[:500])
    finally:
        cli.close()

if __name__ == "__main__":
    main()