#!/bin/env python
#encoding: utf-8
import sys
import zipfile


def oops(msg):
    print(msg)
    sys.exit(1)
class AXml:
    def __init__(self, data):
        self.idx=0
        self.CHUNK_AXML_FILE=0x00080003
        self.CHUNK_TYPE=0x001C0001
        self.CHUNK_RESOURCEIDS=0x00080180
        self.CHUNK_XML_START_NAMESPACE=0x00100100
        self.CHUNK_XML_END_NAMESPACE=0x00100101
        self.CHUNK_XML_START_TAG=0x00100102
        self.CHUNK_XML_END_TAG=0x00100103
        self.ATTRIBUTE_LENGHT=5
        self.ATTRIBUTE_IX_NAME=1
        self.ATTRIBUTE_IX_VALUE_STRING=2
        self.ATTRIBUTE_IX_VALUE_TYPE=3
        self.TEXT=0
        self.START_TAG=1
        self.END_TAG=2
        self.START_DOCUMENT=3
        self.END_DOCUMENT=4
        self.data=data
        self.pos=0
        self.m_strings=None
        self.m_strings = None
        self.m_event=-1
        self.m_decreaseDepth=False
        self.m_encreaseDepth=False
    def next(self):
        self.doNext()
        return self.m_event
    def doNext(self):
        if None == self.m_strings:
            self.readCheckType(self.CHUNK_AXML_FILE)
            self.skipInt()
            self.read()
            self.m_operational = True
        if self.END_DOCUMENT == self.m_event:
            return
        event = self.m_event
        self.resetEventInfo()
        while True:
            if self.m_decreaseDepth:
                self.m_decreaseDepth = False
                
            if self.pos == len(self.data):
                self.m_event = self.END_DOCUMENT
                break
            if self.START_DOCUMENT == event:
                chunkType = self.CHUNK_XML_START_TAG
            else:
                chunkType = self.readInt()
            if self.CHUNK_RESOURCEIDS == chunkType:
                chunkSize = self.readInt()
                self.m_resourceIds = self.readIntArray(int(chunkSize/4)-2)
                continue
            if self.CHUNK_XML_START_TAG == chunkType and event == -1:
                self.m_event = self.START_DOCUMENT
                break
            self.skipInt()
            lineNumber = self.readInt()
            self.skipInt()
            if chunkType in (self.CHUNK_XML_START_NAMESPACE, self.CHUNK_XML_END_NAMESPACE):
                if self.CHUNK_XML_START_NAMESPACE:
                    prefix = self.readInt()
                    uri = self.readInt()
                else:
                    #
                    pass
                continue
            self.m_lineNumber = lineNumber


            if chunkType == self.CHUNK_XML_START_TAG:
                self.readInt()
                self.m_name = self.readInt()
                self.skipInt()
                attributeCount=self.readInt()
                self.m_idAttribute = (attributeCount>>16)-1
                attributeCount &= 0xffff
                self.m_classAttribute = self.readInt()
                self.m_attributes = self.readIntArray(attributeCount*self.ATTRIBUTE_LENGHT)
                i = self.ATTRIBUTE_IX_VALUE_TYPE
                while i < len(self.m_attributes):
                    self.m_attributes[i] = self.m_attributes[i]>>24
                    i+=self.ATTRIBUTE_LENGHT
                self.m_event = self.START_TAG
                break
            if chunkType == self.CHUNK_XML_END_TAG:
                self.readInt()
                self.m_name = self.readInt()
                self.m_event = self.END_TAG
                self.m_decreaseDepth = True
                break
            if chunkType == self.CHUNK_XML_TEXT:
                self.m_name = self.readInt()
                self.skipInt()
                self.skipInt()
                self.m_event = TEXT
                break


    def resetEventInfo(self):
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
    def readCheckType(self, expectType):
        getType = self.readInt()
        if not getType == expectType:
            oops('Expect type %d!=%d' % (expectType, getType))
    def readInt(self):
        result=0
        for i in range(4):
            tmp = self.data[self.pos] << (i*8)
            result += tmp
            self.pos += 1
        if 0xffffffff == result:
            result = -1
        self.idx+=1
        return result
    def readIntArray(self, length):
        result=[]
        for i in range(length):
            tmp=self.readInt()
            result.append(tmp)
        return result
    def skip(self, n):
        self.pos += n
    def skipInt(self):
        self.skip(4)
    def getAttributeCount(self):
        return len(self.m_attributes)/self.ATTRIBUTE_LENGHT
    def getAttributeName(self, i):
        offset = self.getAttributeOffset(i)
        name = self.m_attributes[offset+self.ATTRIBUTE_IX_NAME]
        return self.getString(name)
    def getAttributeValue(self, i):
        offset = self.getAttributeOffset(i)
        valueType = self.m_attributes[offset + self.ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == 3:
            valueString=self.m_attributes[offset+self.ATTRIBUTE_IX_VALUE_STRING]
            return self.getString(valueString)
        return ""
    def getAttributeOffset(self, i):
        return i*5
    def getString(self, i):
        offset = self.m_stringOffsets[i]
        length=self.getShort(offset)
        offset+=2
        result=''
        for i in range(length):
            result += chr(self.getShort(offset))
            offset+=2
        return result
    def getShort(self, offset):
        if (offset%4)/2 == 0:
            length=self.m_strings[int(offset/4)] & 0xffff
        else:
            length=self.m_strings[int(offset/4)] >> 16
        return length
    
    def read(self):
        self.readCheckType(self.CHUNK_TYPE)
        chunkSize = self.readInt()
        stringCount = self.readInt()
        styleOffsetCount=self.readInt()
        self.readInt()
        stringsOffset=self.readInt()
        stylesOffset=self.readInt()
        self.m_stringOffsets = self.readIntArray(stringCount)

        if not 0 == styleOffsetCount:

            self.readIntArray(styleOffsetCount)

        if 0 == stylesOffset:

            size = chunkSize - stringsOffset

        else:

            size = stylesOffset - stringsOffset

        self.m_strings = self.readIntArray(int(size/4))

        if not stylesOffset == 0:

            size = chunkSize - stylesOffset

            self.m_styles = self.readIntArray(int(size/4))



class APK:
    def __init__(self, xmlStr):
        xml = AXml(xmlStr)
        self.package='net.hankjohn.unknown'
        self.version='1.0'
        self.icon='None'
        while True:
            node = xml.next()
            if xml.END_DOCUMENT == node:
                break
            if xml.START_TAG == node:
                for i in range(int(xml.getAttributeCount())):
                    key=xml.getAttributeName(i)
                    value=xml.getAttributeValue(i)
                    #print("key:%s\tvalue:%s"%(key,value))
                    if 'versionName'==key:
                        self.version=value
                    if 'package' == key:
                        self.package=value
                    if 'icon' == key:
                        self.icon == value


if __name__=='__main__':
    zipFile=zipfile.ZipFile("xunlei_10.apk")
    data = zipFile.read('AndroidManifest.xml')
    apk = APK(data)
    print(apk.package)
    print(apk.version)
    print(apk.icon)
