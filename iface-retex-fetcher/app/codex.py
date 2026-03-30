#! python3
# -*- coding: utf-8 -*-
#
#  RETEX POS API 編碼/解碼
##
import time
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def getTimeStamp(timeString):
    
    structTime = time.strptime(timeString, "%Y-%m-%d %H:%M:%S") # 轉成時間元組
    timeStamp = int(time.mktime(structTime)) # 轉成時間戳  

    return(timeStamp)

##
def encryptBase64(byteStr):
       
    b64Byte = base64.b64encode(byteStr)

    return(b64Byte)

##
def decryptBase64(b64Byte):
    
    strByte = base64.b64decode(b64Byte)
    
    return(strByte) 

##
def encryptAES256(toEncrypt, key, iv):   
    
    cryptor = AES.new( key, AES.MODE_CBC, iv)
    encrypt = cryptor.encrypt(pad(toEncrypt, AES.block_size))

    return (encrypt)

##
def decryptAES256(toDecrypt, key, iv):    
    
    cryptor = AES.new(key, AES.MODE_CBC, iv)
    decrypt = unpad(cryptor.decrypt(toDecrypt), AES.block_size)

    return(decrypt)

##
def encryptSHA512(data):    

    m = hashlib.sha512()
    m.update(data)
    sha512Data = m.hexdigest()

    return(sha512Data)

##
def createCipherText(strData, key, iv):

    clearData = strData.replace(" ","").replace('\t',"").replace('\n',"").replace('\r',"")

    cliperText = encryptBase64(encryptAES256(clearData.encode("UTF-8"), decryptBase64(key), decryptBase64(iv)))

    return (cliperText)

##
def createSignature(TimeStamp, Token, APISaltKey, CipherText):

    StrSignatureBody = "{0}{1}{2}{3}".format(TimeStamp, Token, APISaltKey, CipherText)
    
    txtSignature = encryptSHA512(StrSignatureBody.encode("UTF-8"))

    return(txtSignature.upper())