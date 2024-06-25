from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # <- 新增這行
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormRecognizerClient
from prometheus_fastapi_instrumentator import Instrumentator
import logging
from contextlib import asynccontextmanager
import uvicorn

app = FastAPI()

# 跨網域設定
origins = [
    "http://localhost:6065",
    "http://localhost",
    "http://192.168.10.5:6065",
    "http://192.168.10.5",
    "http://ms1.thi.com.tw:6065",
    "http://ms1.thi.com.tw",
    # 你可以加入其他的網域
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator().instrument(app).expose(app, include_in_schema=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # You can place cleanup code here if needed

app.router.lifespan = lifespan

# Azure Form Recognizer 的設定
endpoint = "https://thi-pdf2txt.cognitiveservices.azure.com/"
api_key = "3cd103b7ddd145138bd9de546ebbe6f5"
client = FormRecognizerClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

UPLOAD_DIR = "C:\inetpub\wwwroot\DocCenter\PDF"

@app.get("/pdf/")
async def pdf(filename: str):
    # 確認有提供檔案名稱
    if not filename:
        raise HTTPException(status_code=400, detail="檔案名稱未提供")

    filepath = os.path.join(UPLOAD_DIR, filename)
    #print(filepath)
    # 檢查該檔案是否存在於 upload 目錄中
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="/PDF 目錄中找不到該檔案")

    # 讀取 PDF 檔案
    with open(filepath, 'rb') as file:
        content = file.read()

    poller = client.begin_recognize_content(content)
    result = poller.result()

    # 將文字區塊合併成單一字串
    #output_text = ''.join([pline.text for page in result for pline in page.lines if pline.text != '.'])
    output_text = ''

    # 遍歷 result 中的每個 page
    for page in result:
        # 檢查 page.lines 是否為 None
        if page.lines is not None:
            # 遍歷 page 中的每一行
            for pline in page.lines:
                # 如果行的內容不是單獨一個句點，則將其添加到輸出字串
                if pline.text != '.':
                    output_text += pline.text
  
    # 現在，output_text 包含所有符合條件的文本，合併成單一字串    
    output_text = output_text.replace("：",":")

    # 找到“單續辦。訂正本:”的位置
    index = output_text.find("正本:")
    # 截取所需的文本部分
    if index != -1:
        line= output_text[:index+3]
    else:
        index = output_text.find("出席者:")
        line= output_text[:index+4]

    def extract_text(stext, vstart_keyword, vend_keyword):
        s_index = stext.find(vstart_keyword) + len(vstart_keyword)
        e_index = stext.find(vend_keyword)
        if s_index > -1 and e_index > -1:
            return stext[s_index+1:e_index].strip()
        else:
            return "沒找到文字!"
    
    data = {}
     # 解析邏輯，與原始程式碼相同
    start_index = line.find("開會事由")
    if start_index != -1:     #開會事由文字有出現
        vfromname = line[line.find("保存年限") + len("保存年限")+1:line.find("受文者")]   
        if "開會通知單" in vfromname:
            #data["來文單位"] = line[line.find("保存年限") + len("保存年限")+1:line.find("開會通知單")]
            data["來文單位"] = extract_text(line, "保存年限","開會通知單")
        else:
            #data["來文單位"] = line[line.find("保存年限") + len("保存年限")+1:line.find("受文者")]
            data["來文單位"] = extract_text(line, "保存年限","函")
    else:
        #data["來文單位"] = line[line.find("保存年限") + len("保存年限")+1:line.find("函")]
        vfromname = line.find("CECI")
        if vfromname != -1: #有檔號:
            vfrom = extract_text(line, "檔號","保存年限")
            if vfrom == "CECI台灣世曦":
                vfrom = "台灣世曦工程顧問股份有限公司"
            data["來文單位"] = vfrom          
        else:
            data["來文單位"] = extract_text(line, "保存年限","函")
            if len(data["來文單位"]) > 200:
            # 如果大於200個字，則只取前100個字
                data["來文單位"] = data["來文單位"][:50]

    # 公文日期
    #data["公文日期"] = line[line.find("中華民國"):line.find("日", line.find("中華民國")) + 1]
    data["公文日期"] = extract_text(line, "發文日期","發文字號")

    # 公文文號  
    vno = line.find("速別:")  
    if vno != -1:
        data["公文文號"] = extract_text(line, "發文字號","速別")
    else:    
        data["公文文號"] = extract_text(line, "發文字號","密等及解密條件")

    if start_index != -1:     #開會事由文字有出現
        data["附件"] = extract_text(line, "附件","開會事由")   
        data["主旨"] = extract_text(line, "開會事由","主持人") 
    else:
        data["附件"] = extract_text(line, "附件","主旨")   
        vsub = line.find("說明:")
        if vsub != -1: #有找到
            data["主旨"] = extract_text(line, "主旨","說明:")
        else:
            data["主旨"] = extract_text(line, "主旨","正本:")  

    return JSONResponse(content=data)