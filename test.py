


def extract_text_between(text, start_keyword, end_keyword):
    start_index = text.find(start_keyword) + len(start_keyword)
    end_index = text.find(end_keyword)
    if start_index > -1 and end_index > -1:
        return text[start_index:end_index].strip()
    else:
        return "Text not found."

text_to_search = """11.21檔號:7672保存年限:高雄市政府捷運工程局函地址:80203高雄市苓雅區四維三路2號10樓承辦單位:綜合規劃科80757承辦人:駱思斌高雄市三民區博愛一路28號7樓電話:07-3368333#3836傳真:07-3314366電子 信箱:rafalelo@kcg. gov. tw受文者:鼎漢國際工程顧問股份有限公司發文日期:中華民國112年11月17日發文字號:高市捷綜字第11232085500號速別:普通件密等及解密條件或保密期限:附件:審查會議紀錄裝主旨:檢送本局112 年11月10日召開「高雄都會區大眾捷運系統整體路網規劃評估委託技術服務案」旅運需求資料更新分析期末報告書審查會議紀錄乙份,請查照。說明:依據本局112年10月27日高市捷綜字第11231930100號開會通知單續辦。"""  # The provided document text

extracted_text = extract_text_between(text_to_search, "附件:", "主旨:")
print(extracted_text)