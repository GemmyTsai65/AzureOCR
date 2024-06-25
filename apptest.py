import argparse
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormRecognizerClient
from starlette.responses import JSONResponse
import json  # Import the json module

# 設定Azure Form Recognizer的設定
endpoint = "https://thi-pdf2txt.cognitiveservices.azure.com/"  # 例如: https://my-resource-name.cognitiveservices.azure.com/
api_key = "3cd103b7ddd145138bd9de546ebbe6f5"

client = FormRecognizerClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# 使用 argparse 處理命令行參數
parser = argparse.ArgumentParser(description='Process a PDF file for text extraction.')
parser.add_argument('-f', '--file', help='The PDF file to process', required=True)
args = parser.parse_args()

# 讀取PDF文件
with open(args.file, "rb") as pdf:
    poller = client.begin_recognize_content(pdf)
    result = poller.result()

# 輸出文字區塊
#for page in result:
#   if page.lines is not None:  # 檢查 page.lines 是否為 None
#        for line in page.lines:
#            if line.text != '.':
#               print(line.text)

# 將結果寫入到.txt檔
#with open("22092023135634.txt", "w", encoding="utf-8") as outfile:
#    for page in result:
#        for line in page.lines:        
#            if line.text != '.':
#                outfile.write(line.text)

# 將文字區塊合併成單一字串
# output_text = ''.join([pline.text for page in result for pline in page.lines if pline.text != '.'])
# 初始化最終的合併字串
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

output_text = output_text.replace("：",":")
#print(output_text+"\n")

# 找到“單續辦。訂正本:”的位置
index = output_text.find("正本:")
# 截取所需的文本部分
if index != -1:
    line= output_text[:index+3]
else:
    index = output_text.find("出席者:")
    line= output_text[:index+4]

print(line + "\n")
# 現在，output_text 包含所有符合條件的文本，合併成單一字串

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

# Convert the data dictionary to a JSON-formatted string
json_output = json.dumps(data, ensure_ascii=False, indent=2)

# Print the JSON-formatted string
print(json_output)

print("\n==文字輸出完成!==")



# 注意: Azure Form Recognizer API有使用限制，請確保測試文件不要太大或請求不要太頻繁
